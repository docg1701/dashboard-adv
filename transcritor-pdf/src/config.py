# -*- coding: utf-8 -*-
"""
Módulo de Configurações para o serviço Transcritor-PDF.

Utiliza pydantic-settings para carregar, validar e disponibilizar
as configurações a partir de variáveis de ambiente ou de um arquivo .env.
"""
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Define e valida as variáveis de ambiente necessárias para a aplicação.
    O Pydantic-Settings lerá automaticamente as variáveis do ambiente.
    """
    model_config = SettingsConfigDict(
        extra='ignore'  # Ignora variáveis de ambiente extras que não estão no modelo
    )

    # --- Configurações do Banco de Dados ---
    # A URL completa para conexão com o banco de dados assíncrono.
    # Ex: postgresql+asyncpg://user:password@host:port/dbname
    ASYNC_DATABASE_URL: str

    # --- Configurações do Celery ---
    # URL para o broker do Celery (ex: redis://localhost:6379/0)
    CELERY_BROKER_URL: str
    # URL para o backend de resultados do Celery (ex: redis://localhost:6379/1)
    CELERY_BACKEND_URL: str

    # --- Configurações de Modelos de IA ---
    # Chave da API para o Google Gemini
    GEMINI_API_KEY: str
    # Dimensão dos vetores de embedding (padrão para text-embedding-004)
    EMBEDDING_DIMENSIONS: int = 768

# Instância única das configurações para ser importada em outros módulos
try:
    settings = Settings()
    logger.info("Configurações da aplicação carregadas com sucesso.")
    # Log de exemplo para verificar se as variáveis foram carregadas (não logar senhas em produção)
    logger.debug(f"DATABASE_URL loaded: {settings.ASYNC_DATABASE_URL is not None}")
    logger.debug(f"CELERY_BROKER_URL loaded: {settings.CELERY_BROKER_URL is not None}")

except Exception as e:
    logger.critical(f"Erro ao carregar as configurações: {e}", exc_info=True)
    # Em caso de falha, a aplicação provavelmente não funcionará.
    # Criamos uma instância vazia para evitar NameError na importação.
    settings = None

