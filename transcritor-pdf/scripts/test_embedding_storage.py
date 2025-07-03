import asyncio
import logging
import os
import sys
import json
from typing import List, Dict, Any

# Adiciona o diretório 'src' ao sys.path para permitir importações diretas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from vectorizer.vector_store_handler import add_chunks_to_vector_store
from db_config import get_db_session # Para verificar a conexão
from sqlalchemy import text

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def check_db_connection():
    """Verifica se a conexão com o banco de dados pode ser estabelecida."""
    logger.info("Verificando a conexão com o banco de dados...")
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Conexão com o banco de dados bem-sucedida.")
        return True
    except Exception as e:
        logger.error(f"Falha ao conectar com o banco de dados: {e}", exc_info=True)
        return False

async def main():
    """
    Função principal para executar o teste de armazenamento de embeddings.
    """
    logger.info("--- Iniciando teste de armazenamento de embeddings ---")

    if not await check_db_connection():
        logger.error("Teste abortado. Não foi possível conectar ao banco de dados.")
        return

    test_document_id = 999
    embedding_dim = 768

    test_rag_chunks: List[Dict[str, Any]] = [
        {
            "chunk_id": f"test_chunk_1_{test_document_id}",
            "text_content": "Este é o primeiro chunk de texto para o documento de teste.",
            "embedding": [0.1] * embedding_dim,
            "metadata": {"original_chunk_index_on_page": 0}
        },
        {
            "chunk_id": f"test_chunk_2_{test_document_id}",
            "text_content": "Este é o segundo chunk, contendo informações adicionais.",
            "embedding": [0.2] * embedding_dim,
            "metadata": {"original_chunk_index_on_page": 1}
        },
        {
            "chunk_id": f"test_chunk_3_{test_document_id}",
            "text_content": "Este é o terceiro e último chunk para este teste específico.",
            "embedding": [0.3] * embedding_dim,
            "metadata": {"original_chunk_index_on_page": 2}
        }
    ]

    logger.info(f"Preparado para inserir {len(test_rag_chunks)} chunks para o document_id: {test_document_id}")

    try:
        logger.info("Chamando a função 'add_chunks_to_vector_store'...")
        await add_chunks_to_vector_store(
            document_id=test_document_id,
            rag_chunks=test_rag_chunks
        )
        logger.info("--- ✅ SUCESSO: A função 'add_chunks_to_vector_store' foi executada sem erros. ---")
        logger.info("Verifique o banco de dados para confirmar se os dados foram inseridos/atualizados corretamente.")

    except Exception as e:
        logger.error(f"--- ❌ FALHA: Ocorreu um erro ao chamar 'add_chunks_to_vector_store'. ---")
        logger.error(f"Detalhes do erro: {e}", exc_info=True)


if __name__ == "__main__":
    # Adiciona o diretório pai de 'scripts' ao sys.path para que 'src' seja encontrado
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    asyncio.run(main())