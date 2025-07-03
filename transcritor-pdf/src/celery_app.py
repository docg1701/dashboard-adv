# -*- coding: utf-8 -*-
"""
Configuração da aplicação Celery.

Este módulo inicializa a aplicação Celery, carregando a configuração
a partir do módulo centralizado de configurações da aplicação.
"""
import logging
from celery import Celery
from .config import settings

logger = logging.getLogger(__name__)

# Verifica se as configurações foram carregadas corretamente
if not settings or not settings.CELERY_BROKER_URL or not settings.CELERY_BACKEND_URL:
    logger.critical("Configurações do Celery (BROKER_URL, BACKEND_URL) não encontradas. A aplicação Celery não pode ser iniciada.")
    # Define valores padrão para evitar que a importação quebre, mas o worker não funcionará.
    celery_app = None
else:
    # Inicializa a aplicação Celery com as configurações do Pydantic
    celery_app = Celery(
        'transcritor_pdf',
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_BACKEND_URL,
        include=['src.tasks']  # Módulos onde as tarefas estão definidas
    )

    # Configurações adicionais do Celery
    celery_app.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='UTC',
        enable_utc=True,
        result_expires=3600 * 24,  # Expira os resultados após 24 horas
        # Aumenta o timeout de visibilidade se as tarefas forem muito longas
        # broker_transport_options={'visibility_timeout': 3600 * 4}, # Ex: 4 horas
    )
    logger.info("Aplicação Celery configurada com sucesso.")

if __name__ == '__main__':
    if celery_app:
        celery_app.start()
