import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock # For mocking async session and embedding client

from sqlalchemy.ext.asyncio import AsyncSession # For type hinting
from src.vectorizer import vector_store_handler
from src.vectorizer import embedding_generator # To mock its client
from src.core.config import settings # To access EMBEDDING_DIMENSIONS

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

from sqlalchemy.engine import Result, MappingResult # For specing mocks

@pytest.fixture
def mock_db_session():
    """Fixture to create a mock AsyncSession with a properly mocked execute->mappings chain."""
    session = AsyncMock(spec=AsyncSession)

    # Mock for the Result object returned by awaited session.execute()
    # The Result object itself has synchronous methods like mappings().
    mock_result = MagicMock(spec=Result) # Changed from AsyncMock to MagicMock

    # Mock for the MappingResult object returned by result.mappings()
    mock_mapping_result = MagicMock(spec=MappingResult)
    mock_mapping_result.all.return_value = []  # Default: .all() returns empty list
    mock_mapping_result.first.return_value = None  # Default: .first() returns None

    # Configure mock_result.mappings() to return our mock_mapping_result
    mock_result.mappings.return_value = mock_mapping_result

    # Configure session.execute (which is awaited) to return our mock_result
    session.execute.return_value = mock_result # This is the key, execute returns a sync-method object after await

    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session

@pytest.fixture
def mock_embedding_client(mocker):
    """Fixture to mock the embedding client."""
    mock_client = MagicMock()
    # Simulate embed_documents and embed_query methods
    # embed_documents returns a list of embeddings (list of lists of floats)
    # embed_query returns a single embedding (list of floats)
    mock_client.embed_documents.return_value = [[0.1] * settings.EMBEDDING_DIMENSIONS for _ in range(2)] # Example for 2 chunks
    mock_client.embed_query.return_value = [0.2] * settings.EMBEDDING_DIMENSIONS

    # Patch the get_embedding_client function in embedding_generator module
    mocker.patch('src.vectorizer.embedding_generator.get_embedding_client', return_value=mock_client)
    return mock_client

async def test_add_chunks_to_vector_store_success(mock_db_session, mock_embedding_client):
    """Test successful addition of chunks to the vector store."""
    doc_id = 1
    sample_chunks = [
        {"chunk_id": str(uuid.uuid4()), "text_content": "Test chunk 1", "embedding": [0.1] * settings.EMBEDDING_DIMENSIONS, "metadata": {"original_chunk_index_on_page": 0}},
        {"chunk_id": str(uuid.uuid4()), "text_content": "Test chunk 2", "embedding": [0.1] * settings.EMBEDDING_DIMENSIONS, "metadata": {"original_chunk_index_on_page": 1}},
    ]

    await vector_store_handler.add_chunks_to_vector_store(mock_db_session, doc_id, sample_chunks)

    # Assert that db.execute was called for each chunk
    assert mock_db_session.execute.call_count == len(sample_chunks)
    # Further assertions could check the SQL query and parameters if the mock was more detailed
    # For example, checking if "INSERT INTO document_chunks" is in the query string.
    # args, kwargs = mock_db_session.execute.call_args_list[0]
    # query_text_obj = args[0] # Assuming the text() object is the first arg
    # assert "INSERT INTO document_chunks" in str(query_text_obj)


async def test_add_chunks_to_vector_store_empty_chunks(mock_db_session, mock_embedding_client):
    """Test add_chunks_to_vector_store with an empty list of chunks."""
    doc_id = 1
    await vector_store_handler.add_chunks_to_vector_store(mock_db_session, doc_id, [])
    mock_db_session.execute.assert_not_called()

async def test_search_similar_chunks_success(mock_db_session, mock_embedding_client):
    """Test successful search for similar chunks."""
    query_text = "search query"
    top_k = 3

    # Simulate database returning some rows
    mock_row1 = {"logical_chunk_id": "id1", "chunk_text": "text1", "chunk_order": 0, "distance": 0.1}
    mock_row2 = {"logical_chunk_id": "id2", "chunk_text": "text2", "chunk_order": 1, "distance": 0.2}

    # Configure the .all() method of the already mocked chain from the fixture
    mock_db_session.execute.return_value.mappings.return_value.all.return_value = [mock_row1, mock_row2]

    results = await vector_store_handler.search_similar_chunks(mock_db_session, query_text, top_k)

    assert len(results) == 2
    assert results[0]["chunk_id"] == "id1"
    assert results[0]["similarity_score"] == pytest.approx(1 - 0.1)
    mock_embedding_client.embed_query.assert_called_once_with(query_text)
    mock_db_session.execute.assert_called_once()
    # args, kwargs = mock_db_session.execute.call_args
    # query_text_obj = args[0]
    # assert "SELECT dc.logical_chunk_id, dc.chunk_text" in str(query_text_obj) # Check parts of the query

async def test_search_similar_chunks_no_results(mock_db_session, mock_embedding_client):
    """Test search when no similar chunks are found."""
    # Default mock_db_session.execute.return_value.mappings.return_value.all.return_value is []
    results = await vector_store_handler.search_similar_chunks(mock_db_session, "query", 5)
    assert len(results) == 0
    mock_embedding_client.embed_query.assert_called_once_with("query")
    mock_db_session.execute.assert_called_once()

async def test_search_similar_chunks_with_filename_filter(mock_db_session, mock_embedding_client):
    """Test search with a document filename filter."""
    query_text = "search query"
    top_k = 3
    filename = "test.pdf"

    await vector_store_handler.search_similar_chunks(mock_db_session, query_text, top_k, document_filename=filename)

    mock_embedding_client.embed_query.assert_called_once_with(query_text)
    mock_db_session.execute.assert_called_once()

    # call_args is a tuple (args, kwargs) or a Call object
    # If params is passed as a positional arg to execute:
    # call_args_tuple = mock_db_session.execute.call_args
    # params_dict_in_call = call_args_tuple[0][1] # First positional arg after self (text object)
    # assert params_dict_in_call['document_filename'] == filename

    # More robust: access by name if using pytest-mock's call_args.kwargs or specific call object structure
    # For an AsyncMock, call_args might be simpler.
    # Assuming 'params' is the name of the keyword argument to execute if it were one,
    # or it's the second positional argument.
    # The `text()` object is the first positional arg (index 0), `params` dict is second (index 1).

    called_query_obj, called_params_dict = mock_db_session.execute.call_args[0]

    assert called_params_dict['document_filename'] == filename
    # Check that the query string contains the JOIN and WHERE clause for filename
    assert "JOIN documents d ON dc.document_id = d.id" in str(called_query_obj)
    assert "WHERE d.file_name = :document_filename" in str(called_query_obj)

# More tests:
# - Error handling (e.g., SQLAlchemyError during execute)
# - Different top_k values
# - Chunks with missing or invalid data for add_chunks_to_vector_store (though some validation is in the function itself)
