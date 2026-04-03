from config.config import get_settings
from handlers.server import create_app

settings = get_settings()
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_dev,
        log_config=None,
        access_log=False,
    )
