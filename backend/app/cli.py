from __future__ import annotations

import asyncio
import logging

from alembic import command
from alembic.config import Config

from app.core.config import BACKEND_DIR, settings
from app.db.seed import seed_catalog
from app.db.session import SessionLocal, engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("attestive.cli")


def run_migrations() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    logger.info("Applying migrations to %s", settings.DATABASE_URL)
    command.upgrade(config, "head")


async def seed() -> None:
    async with SessionLocal() as session:
        subjects, achievements, courses, assessments, roles, questions = await seed_catalog(
            session
        )
    logger.info(
        "Seed complete (%s new subjects, %s new achievements, %s courses, %s diagnostics, "
        "%s career roles, %s interview questions)",
        subjects,
        achievements,
        courses,
        assessments,
        roles,
        questions,
    )
    await engine.dispose()


def main() -> None:
    import sys

    command_name = sys.argv[1] if len(sys.argv) > 1 else "init"
    if command_name == "init":
        run_migrations()
        asyncio.run(seed())
    elif command_name == "seed":
        asyncio.run(seed())
    else:
        raise SystemExit("Usage: python -m app.cli [init|seed]")


if __name__ == "__main__":
    main()
