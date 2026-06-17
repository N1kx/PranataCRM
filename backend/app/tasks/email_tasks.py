from app.worker import celery_app


@celery_app.task(name="app.tasks.email_tasks.send_email", bind=True, max_retries=3)
def send_email(self, to: str, subject: str, body: str) -> dict:
    # Placeholder — call NotificationService here.
    return {"status": "queued", "to": to}
