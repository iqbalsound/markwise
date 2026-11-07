from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="teacher")  # "admin" or "teacher"


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200), default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    offerings: Mapped[list["Offering"]] = relationship(cascade="all, delete")


class Offering(Base):
    """A course taught in one semester, e.g. CS101 in 'Fall 2026'."""

    __tablename__ = "offerings"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    semester: Mapped[str] = mapped_column(String(80))
    students: Mapped[list["Student"]] = relationship(cascade="all, delete")
    assessments: Mapped[list["Assessment"]] = relationship(cascade="all, delete")


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (UniqueConstraint("offering_id", "student_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    offering_id: Mapped[int] = mapped_column(ForeignKey("offerings.id"))
    student_id: Mapped[str] = mapped_column(String(60))  # string keeps leading zeros
    name: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(200), default="")
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    grades: Mapped[list["Grade"]] = relationship(cascade="all, delete")


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    offering_id: Mapped[int] = mapped_column(ForeignKey("offerings.id"))
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20), default="assignment")  # or "quiz"
    max_marks: Mapped[float] = mapped_column(Float, default=10.0)
    rubric: Mapped[str] = mapped_column(Text, default="")
    solution_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    submissions_folder: Mapped[str | None] = mapped_column(String(500), nullable=True)
    grades: Mapped[list["Grade"]] = relationship(cascade="all, delete")


class Grade(Base):
    """One row per (assessment, student): the PDF found for them and the result."""

    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint("assessment_id", "student_pk"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"))
    student_pk: Mapped[int] = mapped_column(ForeignKey("students.id"))
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # status: pending | graded | error | no_file | no_consent
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[str] = mapped_column(String(20), default="")
    overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_json: Mapped[str] = mapped_column(Text, default="")
    graded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
