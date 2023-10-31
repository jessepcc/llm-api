from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "User"  # this is table name

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True)
    emailVerified = Column(DateTime)
    image = Column(String)

    sessions = relationship("Session", back_populates="user")
    resumes = relationship("Resume", back_populates="user")
    interviews = relationship("Interview", back_populates="user")


class Session(Base):
    __tablename__ = "Session"

    id = Column(String, primary_key=True)
    sessionToken = Column(String, unique=True)
    expires = Column(DateTime)
    userId = Column(String, ForeignKey("User.id"))

    user = relationship("User", back_populates="sessions")


class Resume(Base):
    __tablename__ = "Resume"

    id = Column(String, primary_key=True)
    userId = Column(String, ForeignKey("User.id"))
    resource = Column(String)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

    user = relationship("User", back_populates="resumes")
    interviews = relationship("Interview", back_populates="resume")


class Job(Base):
    __tablename__ = "Job"

    id = Column(String, primary_key=True)
    title = Column(String)
    content = Column(String)
    resource = Column(String)
    company = Column(String)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

    interviews = relationship("Interview", back_populates="job")

    def __repr__(self):
        return f"<Job {self.title}>"


class Interview(Base):
    __tablename__ = "Interview"

    id = Column(String, primary_key=True)
    history = Column(JSON)
    result = Column(JSON)
    type = Column(String)
    userId = Column(String, ForeignKey("User.id"))
    jobId = Column(String, ForeignKey("Job.id"))
    resumeId = Column(String, ForeignKey("Resume.id"))

    user = relationship("User", back_populates="interviews")
    job = relationship("Job", back_populates="interviews")
    resume = relationship("Resume", back_populates="interviews")


class InterviewTicket(Base):
    __tablename__ = "InterviewTicket"

    id = Column(String, primary_key=True)
    interviewId = Column(String, ForeignKey("Interview.id"))
    userId = Column(String, ForeignKey("User.id"))
    createdAt = Column(DateTime)
    expiredAt = Column(DateTime)
    host = Column(String)
