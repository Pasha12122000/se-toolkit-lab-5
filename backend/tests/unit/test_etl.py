"""Unit tests for the ETL pipeline."""

import os
from datetime import datetime

import pytest
from sqlalchemy import JSON, event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

os.environ.setdefault("API_KEY", "test")
os.environ["DEBUG"] = "false"

from app.etl import load_items, load_logs, sync
from app.models.interaction import InteractionLog
from app.models.item import ItemRecord
from app.models.learner import Learner


@pytest.fixture
async def engine():
    """Create an in-memory async SQLite engine with test schema."""
    from sqlalchemy.dialects.postgresql import JSONB

    @event.listens_for(SQLModel.metadata, "column_reflect")
    def _reflect(inspector, table, column_info):  # noqa: ANN001 ARG001
        if isinstance(column_info["type"], JSONB):
            column_info["type"] = JSON()

    for col in ItemRecord.__table__.columns:
        if isinstance(col.type, JSONB):
            col.type = JSON()

    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    """Provide a database session bound to the test engine."""
    async with AsyncSession(engine) as sess:
        yield sess


@pytest.mark.asyncio
async def test_load_items_creates_labs_and_tasks(session: AsyncSession) -> None:
    items_catalog = [
        {"lab": "lab-05", "task": None, "title": "Lab 5", "type": "lab"},
        {
            "lab": "lab-05",
            "task": "setup",
            "title": "Repository Setup",
            "type": "task",
        },
        {
            "lab": "lab-05",
            "task": "task-1",
            "title": "Build the Data Pipeline",
            "type": "task",
        },
    ]

    created_count = await load_items(items_catalog, session)
    result = await session.exec(select(ItemRecord).order_by(ItemRecord.id))
    stored_items = list(result.all())

    assert created_count == 3
    assert len(stored_items) == 3
    assert stored_items[0].type == "lab"
    assert stored_items[1].parent_id == stored_items[0].id
    assert stored_items[2].parent_id == stored_items[0].id


@pytest.mark.asyncio
async def test_load_logs_creates_learners_and_is_idempotent(
    session: AsyncSession,
) -> None:
    lab = ItemRecord(id=1, type="lab", title="Lab 5")
    task = ItemRecord(id=2, type="task", title="Repository Setup", parent_id=1)
    session.add_all([lab, task])
    await session.commit()

    items_catalog = [
        {"lab": "lab-05", "task": None, "title": "Lab 5", "type": "lab"},
        {
            "lab": "lab-05",
            "task": "setup",
            "title": "Repository Setup",
            "type": "task",
        },
    ]
    logs = [
        {
            "id": 101,
            "student_id": "stu-1",
            "group": "B23-CS-01",
            "lab": "lab-05",
            "task": "setup",
            "score": 100.0,
            "passed": 4,
            "total": 4,
            "submitted_at": "2026-03-01T10:00:00Z",
        }
    ]

    first_created = await load_logs(logs, items_catalog, session)
    second_created = await load_logs(logs, items_catalog, session)

    learners = list((await session.exec(select(Learner))).all())
    interactions = list((await session.exec(select(InteractionLog))).all())

    assert first_created == 1
    assert second_created == 0
    assert len(learners) == 1
    assert learners[0].external_id == "stu-1"
    assert len(interactions) == 1
    assert interactions[0].external_id == 101


@pytest.mark.asyncio
async def test_sync_uses_latest_timestamp_and_returns_counts(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing_lab = ItemRecord(id=1, type="lab", title="Lab 4")
    existing_task = ItemRecord(id=2, type="task", title="Old Task", parent_id=1)
    existing_learner = Learner(id=1, external_id="stu-old", student_group="B23-CS-01")
    existing_interaction = InteractionLog(
        id=1,
        external_id=1,
        learner_id=1,
        item_id=2,
        kind="attempt",
        score=50.0,
        checks_passed=1,
        checks_total=2,
        created_at=datetime(2026, 3, 1, 9, 0, 0),
    )
    session.add_all([existing_lab, existing_task, existing_learner, existing_interaction])
    await session.commit()

    items_catalog = [
        {"lab": "lab-05", "task": None, "title": "Lab 5", "type": "lab"},
        {
            "lab": "lab-05",
            "task": "setup",
            "title": "Repository Setup",
            "type": "task",
        },
    ]
    api_logs = [
        {
            "id": 200,
            "student_id": "stu-new",
            "group": "B23-CS-02",
            "lab": "lab-05",
            "task": "setup",
            "score": 75.0,
            "passed": 3,
            "total": 4,
            "submitted_at": "2026-03-01T10:30:00Z",
        }
    ]
    observed_since: list[datetime | None] = []

    async def fake_fetch_items() -> list[dict]:
        return items_catalog

    async def fake_fetch_logs(since: datetime | None = None) -> list[dict]:
        observed_since.append(since)
        return api_logs

    monkeypatch.setattr("app.etl.fetch_items", fake_fetch_items)
    monkeypatch.setattr("app.etl.fetch_logs", fake_fetch_logs)

    result = await sync(session)

    assert observed_since == [datetime(2026, 3, 1, 9, 0, 0)]
    assert result == {"new_records": 1, "total_records": 2}
