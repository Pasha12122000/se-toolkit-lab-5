"""ETL pipeline: fetch data from the autochecker API and load it into the database.

The autochecker dashboard API provides two endpoints:
- GET /api/items — lab/task catalog
- GET /api/logs  — anonymized check results (supports ?since= and ?limit= params)

Both require HTTP Basic Auth (email + password from settings).
"""

from datetime import datetime, timezone

import httpx
from sqlalchemy import func
from sqlmodel import select

from app.models.interaction import InteractionLog
from app.models.item import ItemRecord
from app.models.learner import Learner
from sqlmodel.ext.asyncio.session import AsyncSession

from app.settings import settings


def _parse_api_datetime(value: str) -> datetime:
    """Parse an ISO timestamp from the autochecker API into naive UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _format_since(value: datetime) -> str:
    """Format a database timestamp for the autochecker API."""
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Extract — fetch data from the autochecker API
# ---------------------------------------------------------------------------


async def fetch_items() -> list[dict]:
    """Fetch the lab/task catalog from the autochecker API.

    Returns:
        The parsed JSON array returned by the autochecker API.
    """
    async with httpx.AsyncClient(auth=httpx.BasicAuth(
        settings.autochecker_email, settings.autochecker_password
    )) as client:
        response = await client.get(f"{settings.autochecker_api_url}/api/items")
        response.raise_for_status()
        return response.json()


async def fetch_logs(since: datetime | None = None) -> list[dict]:
    """Fetch check results from the autochecker API.

    Returns:
        The combined log list from all paginated API responses.
    """
    all_logs: list[dict] = []
    current_since = since

    async with httpx.AsyncClient(auth=httpx.BasicAuth(
        settings.autochecker_email, settings.autochecker_password
    )) as client:
        while True:
            params: dict[str, str | int] = {"limit": 500}
            if current_since is not None:
                params["since"] = _format_since(current_since)

            response = await client.get(
                f"{settings.autochecker_api_url}/api/logs",
                params=params,
            )
            response.raise_for_status()
            payload = response.json()

            batch_logs = payload["logs"]
            all_logs.extend(batch_logs)

            if not payload["has_more"] or not batch_logs:
                break

            current_since = _parse_api_datetime(batch_logs[-1]["submitted_at"])

    return all_logs


# ---------------------------------------------------------------------------
# Load — insert fetched data into the local database
# ---------------------------------------------------------------------------


async def load_items(items: list[dict], session: AsyncSession) -> int:
    """Load items (labs and tasks) into the database.

    Returns:
        The number of newly inserted lab and task rows.
    """
    created_count = 0
    labs_by_short_id: dict[str, ItemRecord] = {}

    for item in items:
        if item["type"] != "lab":
            continue

        statement = select(ItemRecord).where(
            ItemRecord.type == "lab",
            ItemRecord.title == item["title"],
        )
        existing_lab = (await session.exec(statement)).first()

        if existing_lab is None:
            existing_lab = ItemRecord(type="lab", title=item["title"])
            session.add(existing_lab)
            await session.flush()
            created_count += 1

        labs_by_short_id[item["lab"]] = existing_lab

    for item in items:
        if item["type"] != "task":
            continue

        parent_lab = labs_by_short_id.get(item["lab"])
        if parent_lab is None:
            continue

        statement = select(ItemRecord).where(
            ItemRecord.type == "task",
            ItemRecord.title == item["title"],
            ItemRecord.parent_id == parent_lab.id,
        )
        existing_task = (await session.exec(statement)).first()

        if existing_task is not None:
            continue

        session.add(
            ItemRecord(
                type="task",
                title=item["title"],
                parent_id=parent_lab.id,
            )
        )
        created_count += 1

    await session.commit()
    return created_count


async def load_logs(
    logs: list[dict], items_catalog: list[dict], session: AsyncSession
) -> int:
    """Load interaction logs into the database.

    Args:
        logs: Raw log dicts from the API (each has lab, task, student_id, etc.)
        items_catalog: Raw item dicts from fetch_items() — needed to map
            short IDs (e.g. "lab-01", "setup") to item titles stored in the DB.
        session: Database session.

    Returns:
        The number of newly inserted interaction rows.
    """
    created_count = 0
    item_titles_by_key = {
        (item["lab"], item["task"]): item["title"]
        for item in items_catalog
    }

    for log in logs:
        learner_statement = select(Learner).where(
            Learner.external_id == log["student_id"]
        )
        learner = (await session.exec(learner_statement)).first()
        if learner is None:
            learner = Learner(
                external_id=log["student_id"],
                student_group=log["group"],
            )
            session.add(learner)
            await session.flush()

        item_title = item_titles_by_key.get((log["lab"], log["task"]))
        if item_title is None:
            continue

        item_statement = select(ItemRecord).where(ItemRecord.title == item_title)
        item = (await session.exec(item_statement)).first()
        if item is None:
            continue

        interaction_statement = select(InteractionLog).where(
            InteractionLog.external_id == log["id"]
        )
        existing_interaction = (await session.exec(interaction_statement)).first()
        if existing_interaction is not None:
            continue

        session.add(
            InteractionLog(
                external_id=log["id"],
                learner_id=learner.id,
                item_id=item.id,
                kind="attempt",
                score=log["score"],
                checks_passed=log["passed"],
                checks_total=log["total"],
                created_at=_parse_api_datetime(log["submitted_at"]),
            )
        )
        created_count += 1

    await session.commit()
    return created_count


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


async def sync(session: AsyncSession) -> dict:
    """Run the full ETL pipeline.

    Returns:
        A summary with the newly inserted interaction count and the
        total interaction count after sync.
    """
    items_catalog = await fetch_items()
    await load_items(items_catalog, session)

    latest_created_at = await session.scalar(select(func.max(InteractionLog.created_at)))
    logs = await fetch_logs(latest_created_at)
    new_records = await load_logs(logs, items_catalog, session)

    total_records = await session.scalar(select(func.count()).select_from(InteractionLog))

    return {
        "new_records": new_records,
        "total_records": total_records or 0,
    }
