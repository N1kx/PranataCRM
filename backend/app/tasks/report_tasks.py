from app.worker import celery_app


@celery_app.task(name="app.tasks.report_tasks.aggregate_daily_reports")
def aggregate_daily_reports() -> dict:
    # Placeholder — aggregate daily CRM metrics.
    return {"status": "aggregated"}
