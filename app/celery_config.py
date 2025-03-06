from celery import Celery
from celery.schedules import crontab
from sentry_sdk.integrations.celery import CeleryIntegration
import sentry_sdk
from helpers.config import Config

conf = Config()


# Initialize Sentry for Celery processes
sentry_sdk.init(
    dsn=conf.sentry_dsn,
    integrations=[CeleryIntegration(monitor_beat_tasks=True)],
    environment=conf.env,
    release=conf.release,
)

celery_app = Celery(
    'vulnerability_assessment',
    broker=conf.redis_url,
    backend=conf.redis_url,
    include=["celery_tasks.tasks"],
)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

celery_app.conf.beat_schedule = {
    'generate-templates-every-hour': {
        'task': 'celery_tasks.tasks.generate_templates',
        'schedule': crontab(minute= 0, hour='*/1'),
    },
}