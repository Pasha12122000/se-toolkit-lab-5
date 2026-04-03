"""Router for analytics endpoints.

Each endpoint performs SQL aggregation queries on the interaction data
populated by the ETL pipeline. All endpoints require a `lab` query
parameter to filter results by lab (e.g., "lab-01").
"""

from collections.abc import Sequence

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.interaction import InteractionLog
from app.models.item import ItemRecord
from app.models.learner import Learner

router = APIRouter()


def _lab_title_fragment(lab: str) -> str:
    """Convert a short lab id like ``lab-04`` into a title fragment."""
    prefix, _, number = lab.partition("-")
    if prefix != "lab" or not number:
        return lab
    return f"Lab {number}"


async def _get_lab_task_ids(session: AsyncSession, lab: str) -> tuple[ItemRecord | None, list[int]]:
    """Find the lab item and the ids of its child task items."""
    lab_statement = select(ItemRecord).where(
        ItemRecord.type == "lab",
        ItemRecord.title.contains(_lab_title_fragment(lab)),
    )
    lab_item = (await session.exec(lab_statement)).first()
    if lab_item is None:
        return None, []

    task_statement = select(ItemRecord.id).where(
        ItemRecord.type == "task",
        ItemRecord.parent_id == lab_item.id,
    )
    task_ids = list((await session.exec(task_statement)).all())
    return lab_item, task_ids


def _round_1(value: float | None) -> float:
    """Round a float to one decimal place, defaulting missing values to 0.0."""
    if value is None:
        return 0.0
    return round(float(value), 1)


@router.get("/scores")
async def get_scores(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    """Score distribution histogram for a given lab.
    """
    _, task_ids = await _get_lab_task_ids(session, lab)
    buckets = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}

    if not task_ids:
        return [{"bucket": bucket, "count": count} for bucket, count in buckets.items()]

    score_statement = select(InteractionLog.score).where(
        InteractionLog.item_id.in_(task_ids),
        InteractionLog.score.is_not(None),
    )
    scores = list((await session.exec(score_statement)).all())

    for score in scores:
        if score <= 25:
            buckets["0-25"] += 1
        elif score <= 50:
            buckets["26-50"] += 1
        elif score <= 75:
            buckets["51-75"] += 1
        else:
            buckets["76-100"] += 1

    return [{"bucket": bucket, "count": count} for bucket, count in buckets.items()]


@router.get("/pass-rates")
async def get_pass_rates(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    """Per-task pass rates for a given lab.
    """
    _, task_ids = await _get_lab_task_ids(session, lab)
    if not task_ids:
        return []

    statement = (
        select(
            ItemRecord.title,
            func.avg(InteractionLog.score),
            func.count(InteractionLog.id),
        )
        .join(InteractionLog, InteractionLog.item_id == ItemRecord.id)
        .where(ItemRecord.id.in_(task_ids))
        .group_by(ItemRecord.id, ItemRecord.title)
        .order_by(ItemRecord.title)
    )
    rows: Sequence[tuple[str, float | None, int]] = (await session.exec(statement)).all()

    return [
        {
            "task": title,
            "avg_score": _round_1(avg_score),
            "attempts": attempts,
        }
        for title, avg_score, attempts in rows
    ]


@router.get("/timeline")
async def get_timeline(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    """Submissions per day for a given lab.
    """
    _, task_ids = await _get_lab_task_ids(session, lab)
    if not task_ids:
        return []

    statement = (
        select(
            func.date(InteractionLog.created_at),
            func.count(InteractionLog.id),
        )
        .where(InteractionLog.item_id.in_(task_ids))
        .group_by(func.date(InteractionLog.created_at))
        .order_by(func.date(InteractionLog.created_at))
    )
    rows: Sequence[tuple[str, int]] = (await session.exec(statement)).all()

    return [
        {"date": str(date_value), "submissions": submissions}
        for date_value, submissions in rows
    ]


@router.get("/groups")
async def get_groups(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    """Per-group performance for a given lab.
    """
    _, task_ids = await _get_lab_task_ids(session, lab)
    if not task_ids:
        return []

    statement = (
        select(
            Learner.student_group,
            func.avg(InteractionLog.score),
            func.count(func.distinct(Learner.id)),
        )
        .join(InteractionLog, InteractionLog.learner_id == Learner.id)
        .where(InteractionLog.item_id.in_(task_ids))
        .group_by(Learner.student_group)
        .order_by(Learner.student_group)
    )
    rows: Sequence[tuple[str, float | None, int]] = (await session.exec(statement)).all()

    return [
        {
            "group": group,
            "avg_score": _round_1(avg_score),
            "students": students,
        }
        for group, avg_score, students in rows
    ]
