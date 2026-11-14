"""Curated catalogue + achievement definitions.

These are real platform definitions (subjects, skills, achievement criteria),
not demo student progress. Running this twice is safe.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seed_career import CAREER_ROLES, INTERVIEW_QUESTIONS
from app.db.seed_content import CURRICULUM, DIAGNOSTICS
from app.models.assessment import Assessment, Question
from app.models.career import CareerRole, InterviewQuestion
from app.models.catalog import Course, Module, Skill, Subject
from app.models.enums import AssessmentKind
from app.models.gamification import Achievement

SUBJECTS: list[dict] = [
    {
        "slug": "python",
        "name": "Python Programming",
        "description": "From syntax to OOP, tooling and writing maintainable Python.",
        "category": "engineering",
        "accent": "blue",
        "icon": "terminal",
        "skills": [
            ("syntax-and-types", "Syntax & types"),
            ("control-flow", "Control flow"),
            ("functions", "Functions & scope"),
            ("data-structures", "Lists, dicts & sets"),
            ("oop", "Object-oriented Python"),
            ("error-handling", "Errors & exceptions"),
            ("modules-packaging", "Modules & packaging"),
            ("testing", "Testing with pytest"),
        ],
    },
    {
        "slug": "javascript",
        "name": "JavaScript & the Web",
        "description": "Modern JavaScript, the DOM, async programming and React foundations.",
        "category": "engineering",
        "accent": "violet",
        "icon": "braces",
        "skills": [
            ("js-fundamentals", "Language fundamentals"),
            ("dom", "DOM & events"),
            ("async-js", "Promises & async/await"),
            ("fetch-api", "HTTP & APIs"),
            ("react-components", "React components"),
            ("state-management", "State management"),
            ("typescript", "TypeScript"),
        ],
    },
    {
        "slug": "dsa",
        "name": "Data Structures & Algorithms",
        "description": "Reason about complexity and solve problems with the right structure.",
        "category": "computer-science",
        "accent": "cyan",
        "icon": "git-branch",
        "skills": [
            ("complexity", "Big-O & complexity"),
            ("arrays-strings", "Arrays & strings"),
            ("hashing", "Hash maps"),
            ("linked-lists", "Linked lists"),
            ("trees", "Trees & traversal"),
            ("graphs", "Graphs"),
            ("sorting", "Sorting algorithms"),
            ("dynamic-programming", "Dynamic programming"),
            ("recursion", "Recursion"),
        ],
    },
    {
        "slug": "sql",
        "name": "SQL & Data Modelling",
        "description": "Model relational data, write correct queries and reason about indexes.",
        "category": "data",
        "accent": "amber",
        "icon": "database",
        "skills": [
            ("select-queries", "SELECT & filtering"),
            ("joins", "Joins"),
            ("aggregation", "Aggregation"),
            ("subqueries", "Subqueries & CTEs"),
            ("normalisation", "Normalisation"),
            ("indexing", "Indexes & performance"),
            ("transactions", "Transactions"),
        ],
    },
    {
        "slug": "machine-learning",
        "name": "Machine Learning Foundations",
        "description": "The maths and intuition behind models, evaluation and feature work.",
        "category": "data",
        "accent": "emerald",
        "icon": "brain",
        "skills": [
            ("python-for-ml", "Python for ML"),
            ("statistics", "Statistics"),
            ("regression", "Regression"),
            ("classification", "Classification"),
            ("model-evaluation", "Model evaluation"),
            ("feature-engineering", "Feature engineering"),
            ("neural-networks", "Neural networks"),
        ],
    },
    {
        "slug": "system-design",
        "name": "System Design",
        "description": "Design reliable services: APIs, storage, caching and trade-offs.",
        "category": "engineering",
        "accent": "rose",
        "icon": "network",
        "skills": [
            ("api-design", "API design"),
            ("caching", "Caching"),
            ("databases", "Database choices"),
            ("scalability", "Scalability"),
            ("reliability", "Reliability"),
            ("observability", "Monitoring & logging"),
        ],
    },
]

ACHIEVEMENTS: list[dict] = [
    {
        "code": "first_steps",
        "name": "First Steps",
        "description": "Complete your first lesson.",
        "icon": "sparkles",
        "xp_reward": 25,
        "criteria": {"type": "lessons_completed", "threshold": 1},
    },
    {
        "code": "streak_three",
        "name": "Momentum",
        "description": "Study three days in a row.",
        "icon": "flame",
        "xp_reward": 50,
        "criteria": {"type": "streak_days", "threshold": 3},
    },
    {
        "code": "streak_seven",
        "name": "Consistency",
        "description": "Keep a seven-day learning streak.",
        "icon": "flame",
        "xp_reward": 150,
        "criteria": {"type": "streak_days", "threshold": 7},
    },
    {
        "code": "skill_builder",
        "name": "Skill Builder",
        "description": "Reach 60% proficiency in five skills.",
        "icon": "target",
        "xp_reward": 200,
        "criteria": {"type": "skills_acquired", "threshold": 5},
    },
    {
        "code": "problem_solver",
        "name": "Problem Solver",
        "description": "Pass your first coding exercise's test suite.",
        "icon": "code",
        "xp_reward": 100,
        "criteria": {"type": "coding_exercises_solved", "threshold": 1},
    },
    {
        "code": "project_ship",
        "name": "Ship It",
        "description": "Complete a portfolio project.",
        "icon": "rocket",
        "xp_reward": 300,
        "criteria": {"type": "projects_completed", "threshold": 1},
    },
    {
        "code": "interview_ready",
        "name": "Interview Ready",
        "description": "Complete a mock interview and review its rubric feedback.",
        "icon": "message-square",
        "xp_reward": 150,
        "criteria": {"type": "mock_interviews_completed", "threshold": 1},
    },
]


async def _seed_curriculum(session: AsyncSession, subjects: dict[str, Subject]) -> int:
    created = 0
    for subject_slug, entry in CURRICULUM.items():
        subject = subjects.get(subject_slug)
        if subject is None:
            continue
        course_data = entry["course"]
        course = (
            await session.execute(select(Course).where(Course.slug == course_data["slug"]))
        ).scalar_one_or_none()
        if course is None:
            course = Course(subject_id=subject.id, **course_data)
            session.add(course)
            await session.flush()
            created += 1

        existing_modules = (
            await session.execute(select(Module.id).where(Module.course_id == course.id))
        ).first()
        if existing_modules:
            continue

        for position, module in enumerate(entry["modules"], start=1):
            session.add(
                Module(
                    course_id=course.id,
                    title=module["title"],
                    summary=module["summary"],
                    position=position,
                    estimated_minutes=module["minutes"],
                    is_project=module.get("is_project", False),
                    skill_slugs=module["skills"],
                )
            )
    return created


async def _seed_diagnostics(
    session: AsyncSession,
    subjects: dict[str, Subject],
    skills_by_subject: dict[str, dict[str, Skill]],
) -> int:
    created = 0
    for subject_slug, items in DIAGNOSTICS.items():
        subject = subjects.get(subject_slug)
        if subject is None:
            continue
        title = f"{subject.name} diagnostic"
        existing = (
            await session.execute(
                select(Assessment).where(
                    Assessment.subject_id == subject.id,
                    Assessment.kind == AssessmentKind.DIAGNOSTIC.value,
                    Assessment.title == title,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue

        assessment = Assessment(
            subject_id=subject.id,
            title=title,
            description=(
                f"A short diagnostic that maps your current {subject.name} knowledge to specific skills. "
                "Answer honestly — the result selects where your roadmap starts."
            ),
            kind=AssessmentKind.DIAGNOSTIC.value,
            level="beginner",
            estimated_minutes=10,
            generated_by="curated",
        )
        session.add(assessment)
        await session.flush()

        subject_skills = skills_by_subject.get(subject_slug, {})
        for position, item in enumerate(items, start=1):
            skill = subject_skills.get(item["skill"])
            if skill is None:
                raise ValueError(
                    f"Diagnostic content references unknown skill '{item['skill']}' in {subject_slug}"
                )
            session.add(
                Question(
                    assessment_id=assessment.id,
                    skill_id=skill.id,
                    kind=item["kind"],
                    prompt=item["prompt"],
                    options=item.get("options"),
                    correct_answer=item["answer"],
                    explanation=item["explanation"],
                    difficulty=item["difficulty"],
                    position=position,
                )
            )
        created += 1
    return created


async def _seed_career(
    session: AsyncSession,
    skills_by_subject: dict[str, dict[str, Skill]],
) -> tuple[int, int]:
    """Seed curated roles and their question bank, validating every skill reference."""
    all_skills = {
        slug: skill for subject_skills in skills_by_subject.values() for slug, skill in subject_skills.items()
    }

    roles_created = 0
    for entry in CAREER_ROLES:
        requirements: list[dict] = []
        for subject_slug, skill_slug, target, importance in entry["skills"]:
            skill = skills_by_subject.get(subject_slug, {}).get(skill_slug)
            if skill is None:
                raise ValueError(
                    f"Career role '{entry['slug']}' references unknown skill "
                    f"'{skill_slug}' in {subject_slug}"
                )
            requirements.append(
                {
                    "subject_slug": subject_slug,
                    "skill_slug": skill_slug,
                    "target": target,
                    "importance": importance,
                }
            )

        role = (
            await session.execute(select(CareerRole).where(CareerRole.slug == entry["slug"]))
        ).scalar_one_or_none()
        if role is None:
            role = CareerRole(slug=entry["slug"], title=entry["title"])
            session.add(role)
            roles_created += 1
        # Curated content is refreshed on every seed so a version bump in code
        # actually reaches existing deployments.
        role.title = entry["title"]
        role.summary = entry["summary"]
        role.level = entry["level"]
        role.version = entry["version"]
        role.skills = requirements
        role.portfolio_briefs = entry["portfolio_briefs"]
    await session.flush()

    roles = {
        role.slug: role for role in (await session.execute(select(CareerRole))).scalars().all()
    }
    questions_created = 0
    for role_slug, items in INTERVIEW_QUESTIONS.items():
        role = roles.get(role_slug)
        if role is None:
            raise ValueError(f"Interview questions reference unknown role '{role_slug}'")
        existing = {
            question.position: question
            for question in (
                await session.execute(
                    select(InterviewQuestion).where(InterviewQuestion.role_id == role.id)
                )
            ).scalars().all()
        }
        for position, item in enumerate(items, start=1):
            skill = all_skills.get(item["skill"]) if item.get("skill") else None
            if item.get("skill") and skill is None:
                raise ValueError(
                    f"Interview question in {role_slug} references unknown skill '{item['skill']}'"
                )
            rubric = [
                {"point": point, "keywords": list(keywords)}
                for point, keywords in item["rubric"]
            ]
            question = existing.get(position)
            if question is None:
                question = InterviewQuestion(role_id=role.id, position=position)
                session.add(question)
                questions_created += 1
            question.skill_id = skill.id if skill else None
            question.kind = item["kind"]
            question.prompt = item["prompt"]
            question.difficulty = item.get("difficulty", 2)
            question.rubric = rubric
            question.model_answer = item.get("answer")

    return roles_created, questions_created


async def seed_catalog(session: AsyncSession) -> tuple[int, int, int, int, int, int]:
    existing_subjects = (await session.execute(select(Subject.slug))).scalars().all()
    created_subjects = 0
    for entry in SUBJECTS:
        if entry["slug"] in existing_subjects:
            subject = (
                await session.execute(select(Subject).where(Subject.slug == entry["slug"]))
            ).scalar_one()
        else:
            subject = Subject(
                slug=entry["slug"],
                name=entry["name"],
                description=entry["description"],
                category=entry["category"],
                accent=entry["accent"],
                icon=entry["icon"],
            )
            session.add(subject)
            await session.flush()
            created_subjects += 1

        existing_skills = set(
            (
                await session.execute(select(Skill.slug).where(Skill.subject_id == subject.id))
            ).scalars()
        )
        for slug, name in entry["skills"]:
            if slug not in existing_skills:
                session.add(
                    Skill(
                        subject_id=subject.id,
                        slug=slug,
                        name=name,
                        description=f"{name} in {entry['name']}.",
                    )
                )

    existing_achievements = (await session.execute(select(Achievement.code))).scalars().all()
    created_achievements = 0
    for entry in ACHIEVEMENTS:
        if entry["code"] not in existing_achievements:
            session.add(Achievement(**entry))
            created_achievements += 1

    await session.flush()

    subjects = {
        subject.slug: subject
        for subject in (await session.execute(select(Subject))).scalars().all()
    }
    skills_by_subject: dict[str, dict[str, Skill]] = {slug: {} for slug in subjects}
    for skill, subject_slug in (
        await session.execute(select(Skill, Subject.slug).join(Subject, Subject.id == Skill.subject_id))
    ).all():
        skills_by_subject.setdefault(subject_slug, {})[skill.slug] = skill

    created_courses = await _seed_curriculum(session, subjects)
    created_assessments = await _seed_diagnostics(session, subjects, skills_by_subject)
    created_roles, created_questions = await _seed_career(session, skills_by_subject)

    await session.commit()
    return (
        created_subjects,
        created_achievements,
        created_courses,
        created_assessments,
        created_roles,
        created_questions,
    )
