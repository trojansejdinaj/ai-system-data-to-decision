from fastapi import FastAPI

from app.api.dashboard import router as dashboard_api_router
from app.api.ingest import router as ingest_router
from app.web.dashboard_page import router as dashboard_page_router

app = FastAPI(title="ai-system-data-to-decision")

# Register routers
app.include_router(ingest_router)
app.include_router(dashboard_api_router)
app.include_router(dashboard_page_router)


@app.get("/health")
def health():
    return {"status": "ok"}
