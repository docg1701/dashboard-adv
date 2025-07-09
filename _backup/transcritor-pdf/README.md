# Transcritor PDF

Este projeto é uma API em Python que visa processar arquivos PDF contendo documentos médicos manuscritos. Ele extrai o texto de cada página usando modelos de linguagem multimodais, analisa o texto para extrair informações chave (nome do cliente, data, etc.), formata a saída em chunks adequados para RAG (Retrieval-Augmented Generation) e, finalmente, gera embeddings vetoriais para esses chunks, armazenando-os em um banco de dados PostgreSQL com a extensão pgvector.

## Status Atual da Implementação

**Importante:** Embora muitos componentes individuais para o processamento de PDFs (como divisão de arquivos, pré-processamento de imagens, extração de texto via LLM, etc.) contenham lógica funcional, o pipeline principal de orquestração em `src/processing.py` (`process_pdf_pipeline`) atualmente utiliza lógica de simulação (placeholders).

Isso significa que o processamento de ponta-a-ponta descrito nas "Funcionalidades Principais" ainda não está totalmente integrado e operacional. A funcionalidade completa requer desenvolvimento adicional para integrar os módulos componentes ao pipeline principal. Os testes de API existentes validam a interface da API e o enfileiramento de tarefas, mas não o processamento real do conteúdo do PDF.

**Funcionalidades Principais:**

* Divide PDFs de múltiplas páginas em imagens individuais por página (formato WebP temporário).
* Aplica um pipeline de pré-processamento de imagem (Escala de Cinza, Filtro de Mediana, CLAHE, Binarização Sauvola) usando Scikit-image para melhorar a legibilidade.
* Utiliza um LLM (via Langchain/OpenAI API) para extrair o texto bruto de cada imagem de página pré-processada.
* Utiliza um LLM (via Langchain/OpenAI API) para analisar o texto extraído e identificar informações estruturadas (nome, data, assinatura, doenças).
* Formata os dados extraídos em chunks de texto com metadados associados, otimizados para RAG.
* Gera embeddings vetoriais para cada chunk de texto usando a API da OpenAI (`text-embedding-3-small`).
* Insere/Atualiza os chunks, metadados e embeddings em uma tabela PostgreSQL configurada com `pgvector`.

**Estrutura do Projeto:**

* `src/`: Código fonte principal da aplicação.
    * `input_handler/`: Módulos para lidar com a entrada (dividir PDF, carregar página).
        * `pdf_splitter.py`: Divide PDF em imagens de página.
        * `loader.py`: Carrega imagens de página.
    * `preprocessor/`: Módulo para pré-processar imagens de página.
        * `image_processor.py`: Aplica filtros (Median, CLAHE, Sauvola).
    * `extractor/`: Módulos para interagir com LLMs.
        * `llm_client.py`: Configura o cliente LLM (OpenAI/OpenRouter).
        * `text_extractor.py`: Extrai texto bruto da imagem via LLM.
        * `info_parser.py`: Extrai informações estruturadas do texto via LLM.
    * `output_handler/`: Módulo para formatar a saída.
        * `formatter.py`: Cria chunks formatados para RAG.
    * `vectorizer/`: Módulos para vetorização e armazenamento.
        * `embedding_generator.py`: Gera embeddings via API OpenAI.
        * `vector_store_handler.py`: Interage com o banco de dados PostgreSQL/pgvector.
    * `main.py`: Ponto de entrada da aplicação FastAPI e orquestrador do pipeline.
* `tests/`: Testes unitários e de integração (usando `pytest`).
* `requirements.txt`: Lista de dependências Python do projeto.
* `.env`: Arquivo para armazenar segredos (API keys, credenciais de DB) - **NÃO versionar no Git!**
* `.gitignore`: Especifica arquivos e diretórios a serem ignorados pelo Git.
* `ROADMAP.md`: Detalha as fases de desenvolvimento do projeto.

**Instalação:**

1.  **Clone o repositório:**

        git clone [https://github.com/galvani4987/transcritor-pdf.git](https://github.com/galvani4987/transcritor-pdf.git)
        cd transcritor-pdf

2.  **Crie e ative um ambiente virtual:**

        python -m venv .venv
        # Linux/macOS:
        source .venv/bin/activate
        # Windows:
        # .\.venv\Scripts\activate

3.  **Instale as dependências:**

        pip install -r requirements.txt

**Configuração:**

1.  **Crie um arquivo `.env`** na raiz do projeto.
2.  **Adicione as seguintes variáveis de ambiente** ao arquivo `.env`, substituindo pelos seus valores reais:

    ```dotenv
    # Chave da API OpenAI (necessária para embeddings e potencialmente LLMs)
    # Se usar OpenRouter para LLMs, esta chave pode ser a do OpenRouter se ele usar a API compatível OpenAI.
    OPENAI_API_KEY="sk-..."

    # Credenciais do Banco de Dados PostgreSQL (com pgvector)
    DB_HOST="localhost"        # Ou o endereço do seu servidor DB
    DB_PORT="5432"             # Ou a porta do seu servidor DB
    DB_NAME="nome_do_seu_banco" # Nome do banco de dados
    DB_USER="usuario_do_banco"   # Usuário com permissão de escrita
    DB_PASSWORD="senha_do_usuario" # Senha do usuário

    # --- Opcional: Configuração do LLM via OpenRouter ---
    # Se quiser usar OpenRouter para os LLMs de extração/parsing (em vez da OpenAI direta)
    # OPENAI_BASE_URL="https://openrouter.ai/api/v1"
    # OPENAI_MODEL_NAME="google/gemini-flash" # Ou outro modelo do OpenRouter
    ```

3.  **Configure o Banco de Dados PostgreSQL:**
    *   Certifique-se de que o PostgreSQL (versão 16+ recomendada) esteja instalado e rodando.
    *   Crie um banco de dados e um usuário com as permissões necessárias no PostgreSQL.
    *   **Configuração do Schema:** A aplicação FastAPI gerenciará automaticamente a criação da extensão `vector` (se não existir) e da tabela `documents` necessária durante a inicialização. Você não precisa executar manualmente os comandos `CREATE EXTENSION` ou `CREATE TABLE` para a tabela `documents`.
    *   A tabela `documents` criada pela aplicação terá a seguinte estrutura:
        *   `chunk_id TEXT PRIMARY KEY`
        *   `filename TEXT`
        *   `page_number INTEGER`
        *   `text_content TEXT`
        *   `metadata JSONB`
        *   `embedding VECTOR(1536)` (configurado para o modelo `text-embedding-3-small`)
        *   `created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP`
    *   **Variáveis de Ambiente:** Certifique-se de que as variáveis de ambiente `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, e `DB_PASSWORD` no seu arquivo `.env` estão corretamente configuradas para apontar para o seu banco de dados PostgreSQL.

**API Usage**

Esta seção descreve como rodar e interagir com a API FastAPI fornecida pelo projeto.

**Rodando a API Localmente:**

Para rodar a API localmente com recarregamento automático durante o desenvolvimento, use Uvicorn:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

A API estará acessível em `http://localhost:8000`.

**Endpoints:**

1.  **Health Check**
    *   **Propósito:** Verificar o status operacional da API.
    *   **Método:** `GET`
    *   **Caminho:** `/health/`
    *   **Resposta (200 OK):**
        ```json
        {"status": "ok"}
        ```
    *   **Exemplo `curl`:**
        ```bash
        curl http://localhost:8000/health/
        ```

2.  **Processar PDF**
    *   **Propósito:** Fazer upload de um arquivo PDF, processá-lo para extrair texto e informações, gerar embeddings e armazená-los no banco de dados.
    *   **Método:** `POST`
    *   **Caminho:** `/process-pdf/`
    *   **Corpo da Requisição:** `multipart/form-data` com uma chave `pdf_file` e o arquivo PDF como seu valor.
    *   **Resposta de Sucesso (200 OK):**
        ```json
        {
            "message": "PDF processed and data stored successfully.",
            "file_id": "unique_id_of_the_file",
            "chunks_added": "count"
        }
        ```
    *   **Respostas de Erro:**
        *   `400 Bad Request`:
            ```json
            {"detail": "No PDF file provided."}
            ```
            ```json
            {"detail": "Invalid PDF file."}
            ```
        *   `500 Internal Server Error`:
            ```json
            {"detail": "Error processing PDF: <specific error>"}
            ```
            ```json
            {"detail": "Database connection error: <specific error>"}
            ```
    *   **Exemplo `curl`:**
        ```bash
        curl -X POST -F "pdf_file=@/caminho/para/seu/documento.pdf" http://localhost:8000/process-pdf/
        ```

## 🐳 Running with Docker Compose (as part of `dashboard-adv`)

This `transcritor-pdf` service is an integral part of the `dashboard-adv` project and is managed by its main Docker Compose setup. This integration simplifies service management, dependency handling (like the PostgreSQL database), and networking.

### Prerequisites

*   **Docker and Docker Compose installed:** Ensure you have the latest versions of Docker Desktop (which includes Docker Compose) or Docker Engine and Docker Compose plugin installed on your system.
*   **`dashboard-adv` project cloned:** You need to have the main `dashboard-adv` repository cloned. The `transcritor-pdf` service موجود neste repositório no diretório `transcritor-pdf/`.

### Configuration

All runtime configuration for the `transcritor-pdf` service, when run via `dashboard-adv`'s Docker Compose, is managed through the `.env` file located at `dashboard-adv/backend/.env`.

The `transcritor-pdf` service expects the following essential environment variables to be present in this shared `.env` file:

*   `OPENAI_API_KEY`: Your API key for OpenAI (used for embeddings).
*   `DB_HOST=db`: This tells `transcritor-pdf` to connect to the PostgreSQL service named `db` as defined within the `docker-compose.yml` of `dashboard-adv`.
*   `DB_PORT=5432`: The internal port of the `db` service.
*   `DB_NAME`: The name of the database to use (e.g., `appdb`).
*   `DB_USER`: The username for connecting to the database (e.g., `appuser`).
*   `DB_PASSWORD`: The password for the database user.

**Important Note on `PYTHONPATH`**:
The `PYTHONPATH=/app` environment variable is crucial for the service to locate its Python modules correctly within the container. This is set in the `dashboard-adv/docker-compose.yml` file for the `transcritor_pdf` service.

### Running the Service

1.  **Navigate to the `dashboard-adv` root directory:**
    If you have cloned the `dashboard-adv` project, navigate to its root directory.

2.  **Run Docker Compose:**
    To build (if necessary) and start all services defined in `dashboard-adv`, including `transcritor-pdf` and its dependencies:
    ```bash
    docker compose up
    ```
    To run in detached mode (in the background):
    ```bash
    docker compose up -d
    ```
    The `transcritor-pdf` service will build its Docker image based on the `transcritor-pdf/Dockerfile` located within the `dashboard-adv` project and then start as part of the orchestrated services.

### Accessing the API

Once the `transcritor-pdf` service is running via the main Docker Compose of `dashboard-adv`:

*   The API will be available at: `http://localhost:8002` (as per the port mapping `8002:8002` defined in `dashboard-adv/docker-compose.yml`).
*   **Health Check:** `GET http://localhost:8002/health/`
*   **Process PDF:** `POST http://localhost:8002/process-pdf/` (use with a tool like `curl` or Postman to upload a PDF file).

## Testes

Para rodar os testes unitários (requer `pytest` instalado):

    # Certifique-se que o ambiente virtual está ativado
    pytest