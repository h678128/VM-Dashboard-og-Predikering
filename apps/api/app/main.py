from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import domain  # noqa: F401

app = FastAPI(
    title="VM Dashboard og Predikering API",
    description="Norsk VM-dashboard for kamper, prediksjoner, modellinnsikt og offisielle TV-lenker.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def create_demo_tables() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # pragma: no cover - API can still serve seeded data without DB.
        print(f"Database startup skipped: {exc}")

