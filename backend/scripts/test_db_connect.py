# backend/app/test_db_connect.py
import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import SQLAlchemyError

# Carregar URLs do ambiente (serão passadas pelo docker-compose exec)
SYNC_DB_URL = os.getenv("DATABASE_URL")
ASYNC_DB_URL = os.getenv("ASYNC_DATABASE_URL")

print("--- Iniciando Teste de Conexão com Banco de Dados ---")
print(f"URL Síncrona (DATABASE_URL): {SYNC_DB_URL[:SYNC_DB_URL.find('@')] if SYNC_DB_URL and '@' in SYNC_DB_URL else SYNC_DB_URL}")
print(f"URL Assíncrona (ASYNC_DATABASE_URL): {ASYNC_DB_URL[:ASYNC_DB_URL.find('@')] if ASYNC_DB_URL and '@' in ASYNC_DB_URL else ASYNC_DB_URL}")
print("-" * 30)

# --- Teste Conexão Síncrona (psycopg2) ---
print("\n[TESTE 1] Tentando conexão SÍNCRONA (postgresql://)...")
if not SYNC_DB_URL:
    print("ERRO: Variável de ambiente DATABASE_URL não definida.")
else:
    try:
        # Tenta criar o engine síncrono
        sync_engine = create_engine(SYNC_DB_URL, echo=False)
        # Tenta estabelecer uma conexão
        connection = sync_engine.connect()
        print("SUCESSO: Conexão síncrona estabelecida!")
        connection.close()
        sync_engine.dispose()
        print("SUCESSO: Conexão síncrona fechada e engine descartado.")
    except ImportError as e:
        print(f"ERRO de Importação (Driver Síncrono?): {e}")
    except SQLAlchemyError as e:
        print(f"ERRO SQLAlchemy (Conexão Síncrona): {e}")
    except Exception as e:
        print(f"ERRO Inesperado (Conexão Síncrona): {e}")

print("-" * 30)

# --- Teste Conexão Assíncrona (asyncpg) ---
print("\n[TESTE 2] Tentando conexão ASSÍNCRONA (postgresql+asyncpg://)...")

async def test_async_connection():
    if not ASYNC_DB_URL:
        print("ERRO: Variável de ambiente ASYNC_DATABASE_URL não definida.")
        return

    async_engine = None # Definir fora do try para o finally
    try:
        # Tenta criar o engine assíncrono
        async_engine = create_async_engine(ASYNC_DB_URL, echo=False)
        # Tenta estabelecer uma conexão
        async with async_engine.connect() as connection:
            print("SUCESSO: Conexão assíncrona estabelecida!")
        print("SUCESSO: Conexão assíncrona fechada.")
    except ImportError as e:
        print(f"ERRO de Importação (Driver Assíncrono?): {e}")
    except SQLAlchemyError as e:
        print(f"ERRO SQLAlchemy (Conexão Assíncrona): {e}")
    except Exception as e:
        print(f"ERRO Inesperado (Conexão Assíncrona): {e}")
    finally:
        if async_engine:
            await async_engine.dispose()
            print("SUCESSO: Engine assíncrono descartado.")

# Executa a função de teste assíncrona
try:
    asyncio.run(test_async_connection())
except Exception as e:
     print(f"ERRO ao executar o teste assíncrono: {e}")

print("-" * 30)
print("--- Teste de Conexão Finalizado ---")