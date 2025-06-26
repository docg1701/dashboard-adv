from celery import Celery
from src.core.config import settings # Import Pydantic settings

# Broker and backend URLs are now sourced from Pydantic settings,
# which loads them from the .env file or environment variables.
# Defaults are defined in the Settings class if not found in .env.

celery_app = Celery(
    'transcritor_pdf', # Using the project name as the main app name
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BACKEND_URL,
    include=['src.tasks'] # List of modules to import when worker starts
)

# Optional Celery configuration
# Ensure settings values are not None if Celery expects strings.
# Pydantic settings should provide default strings.
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
