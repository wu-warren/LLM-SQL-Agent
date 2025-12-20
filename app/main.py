from fastapi import FastAPI

app = FastAPI(title="SQL Agent Executor")


@app.get("/health")
def health():
    return {"status": "ok"}
