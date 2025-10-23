from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from .db_config import Base
import enum

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
    
class Job_Query(Base):
    __tablename__ = "job_query"

    query_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Use SAEnum with values_callable to store the enum .value (e.g. "Past Month")
    # and set native_enum=False so SQLAlchemy stores it as a string column that
    # matches the human-readable values. This prevents storing the enum member
    # name (e.g. 'PastMonth').
    date_posted: Mapped[DatePosted] = mapped_column(SAEnum(DatePosted, values_callable=lambda enum: [e.value for e in enum], native_enum=False), default=DatePosted.PastWeek)
    experience_level: Mapped[ExperienceLevel] = mapped_column(SAEnum(ExperienceLevel, values_callable=lambda enum: [e.value for e in enum], native_enum=False), default=ExperienceLevel.EntryLevel)
    job_title: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))

class Scrape_Session(Base):
    __tablename__ = "scrape_sessions"

    scrape_session_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    keywords: Mapped[str] = mapped_column(String(255))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime)
    status: Mapped[ScrapeStatus] = mapped_column(SAEnum(ScrapeStatus, values_callable=lambda enum: [e.value for e in enum], native_enum=False), default=ScrapeStatus.Running)
    log: Mapped[str] = mapped_column(String(1000), default="Scrape started.")

class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    JobTitle: Mapped[str] = mapped_column(String(255))
    Company: Mapped[str] = mapped_column(String(255))
    Location: Mapped[str] = mapped_column(String(255))
    URL: Mapped[str] = mapped_column(String(500))
    Status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus, values_callable=lambda enum: [e.value for e in enum], native_enum=False), default=JobStatus.New)
    DateFound: Mapped[datetime] = mapped_column(DateTime, default=datetime)
