from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import get_settings
from app.database import ensure_runtime_dirs

settings = get_settings()
app = FastAPI(title="Project Broker V2", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    ensure_runtime_dirs()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "project-broker-v2-backend"}


app.include_router(router)
