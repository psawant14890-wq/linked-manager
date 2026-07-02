import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, auth, connections, import_routes, jobs, messages, posts, reports
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered LinkedIn management on your own data export. No scraping, no auto-send.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(import_routes.router)
app.include_router(messages.router)
app.include_router(posts.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(jobs.router)
app.include_router(connections.router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}
