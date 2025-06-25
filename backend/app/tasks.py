# backend/app/tasks.py
from celery import Celery
import os

# Configura um cliente Celery que aponta para o mesmo broker usado pelos workers.
# Isso apenas define COMO enviar tarefas, não as executa.
BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
BACKEND_URL = os.getenv('CELERY_BACKEND_URL', 'redis://redis:6379/1')

celery_app = Celery(
    'main_app_tasks',
    broker=BROKER_URL,
    backend=BACKEND_URL
)

# Defina a assinatura da tarefa para que o backend saiba como chamá-la.
# O nome 'src.tasks.process_pdf_task' deve corresponder exatamente ao nome da tarefa no worker do transcritor.
process_pdf_task = celery_app.signature('src.tasks.process_pdf_task')