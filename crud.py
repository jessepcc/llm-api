from sqlalchemy import select, update, func
from sqlalchemy.orm import Session
from pydantic import BaseModel

import datetime
import models


def get_user(db: Session, user_id: str):
    return db.scalars(select(models.User).where(models.User.id == user_id)).one()


def get_session_by_id(db: Session, session_id: str, user_id):
    now = datetime.datetime.now()
    return db.scalars(
        select(models.Session).where(
            models.Session.id == session_id,
            models.Session.user_id == user_id,
            models.Session.expires > now,
        )
    ).one()


def get_job_list(db: Session, skip: int = 0, limit: int = 100):
    result = db.execute(select(models.Job).offset(skip).limit(limit))
    return result.scalars().fetchall()


def get_job_by_id(db: Session, job_id: str):
    return db.scalars(select(models.Job).where(models.Job.id == job_id)).one()


def get_resume_by_id(db: Session, resume_id: str):
    return db.scalars(select(models.Resume).where(models.Resume.id == resume_id)).one()


def get_interview_by_id(db: Session, interview_id: str):
    result = db.execute(
        select(models.Interview)
        .join(models.Resume)
        .join(models.Job)
        .add_columns(models.Resume)
        .add_columns(models.Job)
        .where(models.Interview.id == interview_id)
    ).first()
    return {
        "interview": result[0],
        "resume": result[1],
        "job": result[2],
    }

    # return db.query(models.Interview, models.Resume.resource, models.Job.content)\
    #         .join(models.Resume).join(models.Job)\
    #         .filter(models.Interview.id == interview_id).unique()


def add_interview_history(db: Session, interview_id: str, history):
    print(history)
    stmt = (
        update(models.Interview)
        .where(models.Interview.id == interview_id)
        .values(history=history)
    )
    result = db.execute(stmt)
    db.commit()
    return True if result.rowcount == 1 else False


def add_pending_interview_result(db: Session, interview_id: str):
    pending = {"evaluation": "pending", "mock": "pending"}
    stmt = (
        update(models.Interview)
        .where(models.Interview.id == interview_id)
        .values(result=pending)
    )
    result = db.execute(stmt)
    db.commit()
    return True if result.rowcount == 1 else False


def add_interview_result(db: Session, interview_id: str, field: str, result):
    stmt = (
        update(models.Interview)
        .where(models.Interview.id == interview_id)
        .values(
            {"result": func.json_set(models.Interview.result, f"$.{field}", result)}
        )
    )
    result = db.execute(stmt)
    db.commit()
    return True if result.rowcount == 1 else False


def get_interview_ticket(db: Session, ticket_id: str):
    return db.scalars(
        select(models.InterviewTicket).where(models.InterviewTicket.id == ticket_id)
    ).one()
