from fastapi import FastAPI

from app.api.ingest import router as ingest_router

app = FastAPI(title="ai-system-data-to-decision")

# Register routers
app.include_router(ingest_router)


@app.get("/health")
def health():
    return {"status": "ok"}
