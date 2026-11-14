"""Import every model so Base.metadata/Alembic sees the full schema."""

from app.db.base import Base
from app.models.assessment import Assessment, AssessmentAttempt, AssessmentResponse, Question
from app.models.auth_tokens import EmailToken
from app.models.career import (
    CareerRole,
    InterviewQuestion,
    InterviewResponse,
    MockInterview,
    ResumeSkill,
)
from app.models.catalog import Course, Lesson, Module, Skill, Subject
from app.models.gamification import (
    Achievement,
    LearningRecommendation,
    UserAchievement,
    XPTransaction,
)
from app.models.learning import LearningActivity, LearningPath, LearningPathItem, LessonProgress
from app.models.tutor import ConversationMessage, TutorConversation
from app.models.user import (
    LearningPreference,
    RefreshToken,
    User,
    UserProfile,
    UserSkill,
    UserSubjectInterest,
)

__all__ = [
    "Base",
    "Achievement",
    "Assessment",
    "CareerRole",
    "InterviewQuestion",
    "InterviewResponse",
    "MockInterview",
    "ResumeSkill",
    "AssessmentAttempt",
    "AssessmentResponse",
    "ConversationMessage",
    "Course",
    "EmailToken",
    "LearningActivity",
    "LearningPath",
    "LearningPathItem",
    "LearningPreference",
    "LearningRecommendation",
    "Lesson",
    "LessonProgress",
    "Module",
    "Question",
    "RefreshToken",
    "Skill",
    "Subject",
    "TutorConversation",
    "User",
    "UserAchievement",
    "UserProfile",
    "UserSkill",
    "UserSubjectInterest",
    "XPTransaction",
]
