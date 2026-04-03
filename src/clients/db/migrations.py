import subprocess
from pathlib import Path

from log.logger import get_logger

logger = get_logger(__name__)


def _get_project_root() -> Path:
    src_dir = Path(__file__).resolve().parent.parent.parent
    return src_dir.parent


def run_migrations() -> None:
    project_root = _get_project_root()
    logger.info("Running database migrations", extra={"cwd": str(project_root)})

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(
            "Migration failed",
            extra={"stderr": result.stderr, "stdout": result.stdout},
        )
        raise RuntimeError(f"Alembic migration failed:\n{result.stderr}")

    if result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            logger.info(f"[alembic] {line}")

    logger.info("Database migrations completed successfully")
