from celery import Celery
from celery.schedules import crontab
from sentry_sdk.integrations.celery import CeleryIntegration
import sentry_sdk, os
from dotenv import load_dotenv

load_dotenv()

sentry_dsn = os.getenv("SENTRY_DSN")
env = os.getenv("ENVIRONMENT")
release = os.getenv("RELEASE")
redis_url = os.getenv("REDIS_URL")

# Initialize Sentry for Celery processes
sentry_sdk.init(
    dsn=sentry_dsn,
    integrations=[CeleryIntegration(monitor_beat_tasks=True)],
    environment=env,
    release=release,
)

celery_app = Celery(
    'vulnerability_assessment',
    broker=redis_url,
    backend=redis_url,
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