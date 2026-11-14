"""Domain enums shared by ORM models and Pydantic schemas."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    STUDENT = "student"
    ADMIN = "admin"


class EducationLevel(str, Enum):
    HIGH_SCHOOL = "high_school"
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    SELF_TAUGHT = "self_taught"
    PROFESSIONAL = "professional"


class ExperienceLevel(str, Enum):
    NONE = "none"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningStyle(str, Enum):
    VISUAL = "visual"
    PRACTICAL = "practical"
    READING = "reading"
    AUDIO = "audio"


class CareerGoal(str, Enum):
    SOFTWARE_ENGINEER = "software_engineer"
    FRONTEND_DEVELOPER = "frontend_developer"
    BACKEND_DEVELOPER = "backend_developer"
    DATA_SCIENTIST = "data_scientist"
    ML_ENGINEER = "ml_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    MOBILE_DEVELOPER = "mobile_developer"
    UNDECIDED = "undecided"


class CourseLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LessonKind(str, Enum):
    READING = "reading"
    EXERCISE = "exercise"
    PROJECT = "project"


class ProgressStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PathStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AssessmentKind(str, Enum):
    DIAGNOSTIC = "diagnostic"
    QUIZ = "quiz"
    PRACTICE = "practice"
    PROJECT = "project"


class QuestionKind(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    CONCEPTUAL = "conceptual"
    CODING = "coding"


class AttemptStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ActivityKind(str, Enum):
    LESSON = "lesson"
    ASSESSMENT = "assessment"
    CODING = "coding"
    TUTOR = "tutor"
    PROJECT = "project"
    REVIEW = "review"
