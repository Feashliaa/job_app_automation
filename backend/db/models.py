from datetime import datetime
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db_config import Base
import enum


#=========================================
#                 Enum's
#=========================================

class Source (str, enum.Enum):
    LinkedIn = "LinkedIn"
    Indeed = "Indeed"
    
class ScrapeStatus(str, enum.Enum):
    Running = "Running"
    Complete = "Complete"
    Failed = "Failed"
    
class DatePosted(str, enum.Enum):
    PastMonth = "Past Month"
    PastWeek = "Past Week"
    Past24Hours = "Past 24 Hours"

class ExperienceLevel(str, enum.Enum):
    EntryLevel = "Entry Level"
    MidLevel = "Mid Level"
    SeniorLevel = "Senior Level"
    
class JobStatus(str, enum.Enum):
    New = "New"
    Applied = "Applied"
    Ignored = "Ignored"
    
    

# =======================================
#               Tables
# =======================================
    
class Job_Query(Base):
    __tablename__ = "job_query"

    query_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    date_posted: Mapped[DatePosted] = mapped_column(
        SAEnum(DatePosted, values_callable=lambda e: [x.value for x in e], native_enum=False),
        default=DatePosted.PastWeek,
    )

    experience_level: Mapped[ExperienceLevel] = mapped_column(
        SAEnum(ExperienceLevel, values_callable=lambda e: [x.value for x in e], native_enum=False),
        default=ExperienceLevel.EntryLevel,
    )

    job_title: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))

    # Relationships
    scrape_sessions = relationship("Scrape_Session", back_populates="query", cascade="all, delete")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Scrape_Session(Base):
    __tablename__ = "scrape_sessions"

    scrape_session_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    query_id: Mapped[int] = mapped_column(ForeignKey("job_query.query_id", ondelete="CASCADE"))

    keywords: Mapped[str] = mapped_column(String(255))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[ScrapeStatus] = mapped_column(
        SAEnum(ScrapeStatus, values_callable=lambda e: [x.value for x in e], native_enum=False),
        default=ScrapeStatus.Running,
    )
    log: Mapped[str] = mapped_column(String(1000), default="Scrape started.")

    # Relationships
    query = relationship("Job_Query", back_populates="scrape_sessions")
    jobs = relationship("Job", back_populates="scrape_session", cascade="all, delete")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scrape_session_id: Mapped[int] = mapped_column(ForeignKey("scrape_sessions.scrape_session_id", ondelete="CASCADE"))

    JobTitle: Mapped[str] = mapped_column(String(255))
    Company: Mapped[str] = mapped_column(String(255))
    Location: Mapped[str] = mapped_column(String(255))
    URL: Mapped[str] = mapped_column(String(500), unique=True, index=True)

    Status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, values_callable=lambda e: [x.value for x in e], native_enum=False),
        default=JobStatus.New,
    )
    
    Salary: Mapped[str] = mapped_column(String(255))

    DateFound: Mapped[datetime] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    scrape_session = relationship("Scrape_Session", back_populates="jobs")

    __table_args__ = (
        Index("idx_jobs_status_date", "Status", "DateFound"),
    )