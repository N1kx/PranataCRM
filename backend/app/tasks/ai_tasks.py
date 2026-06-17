from app.worker import celery_app


@celery_app.task(name="app.tasks.ai_tasks.run_deal_scoring", bind=True, max_retries=2)
def run_deal_scoring(self, deal_id: str) -> dict:
    # Placeholder — call AIUseCase.score_deal asynchronously.
    return {"status": "queued", "deal_id": deal_id}


@celery_app.task(name="app.tasks.ai_tasks.ping")
def ping() -> str:
    """Trivial task to verify Celery wiring is working."""
    return "pong"
