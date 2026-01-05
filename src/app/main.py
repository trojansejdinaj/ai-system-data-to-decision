from fastapi import FastAPI

app = FastAPI(title="ai-system-data-to-decision")


@app.get("/health")
def health():
    return {"status": "ok"}
