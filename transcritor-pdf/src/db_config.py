# -*- coding: utf-8 -*-
"""
Configuração do banco de dados usando SQLAlchemy para a aplicação assíncrona.
"""
import logging
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from .config import settings  # Importa a instância única das configurações

logger = logging.getLogger(__name__)

# --- Configuração do SQLAlchemy ---
try:
    # A URL do banco de dados é obtida do objeto de configurações validado
    if not settings or not settings.ASYNC_DATABASE_URL:
        raise ValueError("ASYNC_DATABASE_URL não foi configurada corretamente.")

    # O engine é o ponto de entrada para o banco de dados.
    engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)

    # A sessionmaker é uma fábrica para criar novas sessões.
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    logger.info("SQLAlchemy async engine e session maker configurados com sucesso.")

except (ValueError, Exception) as e:
    logger.critical(f"Falha ao configurar o engine do SQLAlchemy: {e}", exc_info=True)
    engine = None
    AsyncSessionLocal = None

# --- Gerenciador de Contexto para Sessão ---
@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """
    Providencia uma sessão do SQLAlchemy e garante que ela seja fechada corretamente.
    """
    if AsyncSessionLocal is None:
        logger.error("Session maker não está disponível. A configuração do DB falhou.")
        raise ConnectionError("A configuração do banco de dados falhou e a sessão não pode ser criada.")

    session = AsyncSessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"Erro durante a sessão do banco de dados: {e}", exc_info=True)
        await session.rollback()
        raise
    finally:
        await session.close()
