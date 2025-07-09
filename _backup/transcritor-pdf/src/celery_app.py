import os
from celery import Celery

# Broker and backend URLs are now configurable via environment variables.
# Defaults point to a Redis service named 'redis' as expected in Docker Compose.

celery_app = Celery(
    'transcritor_pdf', # Using the project name as the main app name
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_BACKEND_URL', 'redis://redis:6379/1'), # Using a different DB for backend
    include=['src.tasks'] # List of modules to import when worker starts
)

# Optional Celery configuration
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    # visibility_timeout might be important if tasks are long
    # broker_transport_options={'visibility_timeout': 3600*4}, # 4 hours example
    result_expires=3600 * 24, # Expire results after 24 hours
)

if __name__ == '__main__':
    celery_app.start()
