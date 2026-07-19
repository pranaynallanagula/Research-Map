from fastapi import FastAPI

from research_map.core.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the Research Map API application."""

    settings = get_settings()
    application = FastAPI(
        title="Research Map",
        description=(
            "A research workspace that indexes papers, answers questions with "
            "citations, and builds a knowledge graph of the literature."
        ),
        version="0.1.0",
    )

    @application.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        """Report whether the API process is ready to accept requests."""

        return {"status": "ok", "environment": settings.app_env}

    return application


app = create_app()
