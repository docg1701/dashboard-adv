### Visão Geral

O `transcritor-pdf` é uma API FastAPI projetada para processar arquivos PDF, especialmente documentos médicos. O fluxo principal envolve receber um PDF, extrair seu conteúdo textual página por página, dividir esse texto em pedaços menores (chunks), gerar vetores de embedding para cada chunk e, finalmente, armazenar esses chunks e seus vetores em um banco de dados PostgreSQL com a extensão `pgvector`. O serviço também expõe um endpoint para realizar buscas semânticas (RAG) nesses dados armazenados.

### Estrutura e Componentes Principais

O serviço é orquestrado por tarefas Celery para lidar com o processamento de PDF de forma assíncrona, evitando que as requisições HTTP fiquem bloqueadas durante operações longas.

1.  **Entrada e API (`src/main.py`)**:
    *   A API é construída com **FastAPI**.
    *   O endpoint principal é `POST /process-pdf/`, que aceita um arquivo PDF e um `document_id`.
    *   Ao receber um arquivo, ele não o processa diretamente. Em vez disso, enfileira uma tarefa no **Celery** (`process_pdf_task`) e retorna imediatamente um `task_id`.
    *   Existe um endpoint `GET /process-pdf/status/{task_id}` para verificar o status da tarefa.
    *   Há também um endpoint `POST /query-document/{document_id}` para fazer perguntas sobre um documento específico.
    *   Na inicialização, a aplicação se conecta ao banco de dados PostgreSQL e garante que a extensão `vector` exista.

2.  **Fila de Tarefas (`src/celery_app.py`, `src/tasks.py`)**:
    *   Utiliza **Celery** com **Redis** como broker (para enfileirar tarefas) e backend (para armazenar resultados).
    *   A tarefa principal, `process_pdf_task`, recebe o conteúdo do PDF, o nome do arquivo e o `document_id`. Ela chama a função `process_pdf_pipeline` para executar o trabalho pesado.
    *   A comunicação entre a API e a tarefa é assíncrona, o que torna a aplicação mais robusta e escalável.

3.  **Pipeline de Processamento (`src/processing.py`)**:
    *   Esta é a função central que orquestra todo o fluxo de processamento do PDF.
    *   **Carregamento do PDF**: Utiliza a biblioteca `pypdfium2` para carregar o conteúdo do PDF a partir dos bytes recebidos.
    *   **Extração de Texto**: Itera por cada página do PDF e extrai o texto bruto usando `pypdfium2`.
    *   **Chunking (Divisão de Texto)**: O texto extraído de cada página é dividido em "chunks" (pedaços) de tamanho fixo com alguma sobreposição. Isso é feito para otimizar a busca de similaridade posterior.
    *   **Geração de Embeddings**: Para cada chunk de texto, ele chama o `embedding_generator` para criar um vetor numérico (embedding) que representa o significado semântico daquele texto.
    *   **Armazenamento**: Finalmente, ele invoca o `vector_store_handler` para salvar cada chunk, seu embedding e metadados associados (nome do arquivo, número da página) no banco de dados.

4.  **Vetorização (`src/vectorizer/`)**:
    *   `embedding_generator.py`: Usa a biblioteca `langchain-openai` para se conectar à API da OpenAI e gerar embeddings usando o modelo `text-embedding-3-small`.
    *   `vector_store_handler.py`: É responsável por toda a comunicação com o banco de dados PostgreSQL.
        *   `add_chunks_to_vector_store`: Insere ou atualiza os chunks e seus embeddings na tabela `document_chunks`. A função agora recebe um `document_id` para criar a relação de chave estrangeira correta.
        *   `search_similar_chunks`: Recebe um texto de busca (query), gera um embedding para essa query e usa a capacidade do `pgvector` para encontrar os chunks de texto mais similares no banco de dados, filtrando opcionalmente por um nome de arquivo.

5.  **Processamento de Consultas (`src/query_processor.py`)**:
    *   Orquestra o fluxo de Retrieval-Augmented Generation (RAG).
    *   Primeiro, chama `vector_store_handler.search_similar_chunks` para encontrar os trechos de texto (contexto) mais relevantes para a pergunta do usuário.
    *   Em seguida, monta um prompt para um modelo de linguagem (LLM), que inclui o contexto recuperado e a pergunta original do usuário.
    *   Usa o `llm_client` para enviar este prompt ao LLM e obter uma resposta. A ideia é que o LLM responda à pergunta com base *apenas* no contexto fornecido.

6.  **Módulos de Extração e Pré-processamento (Atualmente não utilizados no pipeline principal)**:
    *   O projeto contém módulos como `preprocessor` e `extractor` que parecem ter sido parte de um design anterior ou futuro, focado em extrair texto de *imagens* de páginas de PDF (OCR) e analisar a estrutura do documento.
    *   `preprocessor/image_processor.py`: Contém funções para melhorar a qualidade de imagens (deskew, CLAHE, binarização Sauvola) antes do OCR.
    *   `extractor/text_extractor.py`: Usa um LLM multimodal para extrair texto de uma imagem.
    *   `extractor/info_parser.py`: Usa um LLM para extrair informações estruturadas (nome, data, etc.) de um texto bruto.
    *   **Importante**: O `README.md` menciona que o pipeline principal (`process_pdf_pipeline`) usa uma lógica de simulação (placeholders). No entanto, a implementação atual em `src/processing.py` parece ser funcional e focada na extração de texto direto do PDF, não em OCR de imagens. Os módulos de pré-processamento e extraç��o baseada em imagem não estão sendo chamados no fluxo atual.

### Resumo do Fluxo de Dados

1.  Usuário envia um `POST /process-pdf/` com um arquivo PDF e `document_id`.
2.  A API FastAPI cria uma tarefa Celery e retorna um `task_id`.
3.  Um worker Celery pega a tarefa e executa `process_pdf_pipeline`.
4.  O pipeline extrai texto, cria chunks, gera embeddings para eles.
5.  Os chunks e embeddings são salvos no PostgreSQL, associados ao `document_id`.
6.  Posteriormente, um usuário pode enviar um `POST /query-document/{document_id}` com uma pergunta.
7.  A API busca chunks relevantes no banco de dados, usa um LLM para gerar uma resposta baseada nesses chunks e a retorna ao usuário.

A arquitetura está bem definida para ser assíncrona e escalável, separando a API web do processamento pesado de documentos. O próximo passo, como sugerido pelo seu pedido de refatoração, pode ser integrar os módulos mais avançados de pré-processamento de imagem e extração de informações estruturadas no pipeline principal.