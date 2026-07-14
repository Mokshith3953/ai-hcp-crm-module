from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, ensure_schema
from app.routes import agent, interactions

Base.metadata.create_all(bind=engine)
ensure_schema()

app = FastAPI(title="AI-First HCP CRM Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions.router)
app.include_router(agent.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
