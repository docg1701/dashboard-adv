# Acompanhamento da Refatoração: Microsserviço Transcritor-PDF v7.2

**Última Atualização:** 02 de julho de 2025

Este documento serve para rastrear o progresso da refatoração do microsserviço `transcritor-pdf`, conforme definido no [Plano de Refatoração v7.2](PLANO_REFATORACAO_V7_2_REVISADO.md).

## Legenda de Status

-   `[ ]` **Pendente:** A tarefa ainda não foi iniciada.
-   `[/]` **Em Andamento:** A tarefa está sendo executada.
-   `[x]` **Concluída:** A tarefa foi finalizada e verificada.
-   `[-]` **Bloqueada:** A tarefa não pode prosseguir.

---

## PRIMEIRA ENTREGA: MVP

### Fase 1: Fundação de Código e Configuração (Prioridade Máxima)
*O alicerce do serviço. Esta fase estabelece a base para a segurança, estabilidade e manutenibilidade do sistema.*

-   [x] **1.1. Migrar Acesso a Dados para SQLAlchemy (Tarefa Crítica)**
    -   [x] Refatorar todo o código de acesso ao banco de dados para usar o ORM assíncrono do SQLAlchemy.
    -   [x] Implementar um gerenciador de contexto (`asynccontextmanager`) para as sessões do banco de dados.
    -   [x] Substituir todas as chamadas diretas `asyncpg` pela nova camada ORM.
-   [x] **1.2. Unificar Configuração de Ambiente com Pydantic**
    -   [x] Adicionar `pydantic-settings` ao `requirements.txt` do `transcritor-pdf`.
    -   [x] Criar um módulo de `settings` que carrega a configuração do arquivo `.env` do `backend`.
    -   [x] Remover qualquer configuração duplicada ou hardcoded.
-   [x] **1.3. Implementar Detecção de Arquivos Duplicados**
    -   [x] **No `backend`:** Criar uma nova migração Alembic para adicionar a coluna `file_hash` (string, unique) à tabela `documents`.
    -   [x] **No `transcritor-pdf`:** Implementar a função para calcular o hash SHA-256 do arquivo PDF.
    -   [x] **No `transcritor-pdf`:** Antes de processar, usar a camada SQLAlchemy para consultar o `backend` pelo `file_hash`.

---

### Fase 2: Lógica de Negócio e IA (Coração do MVP)
*O núcleo de valor do produto, construído sobre a fundação sólida da Fase 1.*

-   [ ] **2.1. Migrar de OpenAI para Google Gemini**
    -   [ ] Adicionar `langchain_google_genai` ao `requirements.txt`.
    -   [ ] Substituir o cliente da OpenAI pelo cliente do Gemini em `llm_client.py`.
    -   [ ] Substituir o gerador de embedding da OpenAI pelo do Gemini (`text-embedding-004`) em `embedding_generator.py`.
    -   [ ] **No `backend`:** Criar uma nova migração Alembic para alterar a dimensão da coluna `embedding` para 768.
    -   [ ] Criar e executar um script para limpar os dados das tabelas `documents` e `document_chunks`.
-   [ ] **2.2. Implementar Extração Híbrida (Digital + OCR)**
    -   [ ] Adicionar `pypdfium2` ao `requirements.txt`.
    -   [ ] Implementar a lógica que usa `pypdfium2` para verificar se uma página contém texto.
    -   [ ] Integrar a decisão (usar texto digital ou OCR) no pipeline de processamento de página.

---

### Fase 3: Qualidade e Robustez do Pipeline
*Garantir que o fluxo de ponta-a-ponta seja confiável e produza resultados de alta qualidade.*

-   [ ] **3.1. Otimizar o Processamento de Texto (Chunking)**
    -   [ ] Substituir o text splitter atual por `RecursiveCharacterTextSplitter`.
    -   [ ] Configurar os parâmetros `chunk_size=1000` and `chunk_overlap=200`.
-   [ ] **3.2. Aumentar a Robustez das Tarefas Assíncronas (Celery)**
    -   [ ] Modificar as tarefas Celery para usar `bind=True`.
    -   [ ] Implementar a lógica de retentativa com `self.retry()` e backoff exponencial.
    -   [ ] Adicionar o tratamento de falha final para atualizar o status do documento no banco de dados para "FALHOU".

---

## SEGUNDA ENTREGA: PÓS-MVP

### Fase 4: Qualidade de Código e Observabilidade

-   [ ] **4.1. Implementar Estratégia de Testes e Observabilidade**
    -   [ ] Adicionar `pytest-asyncio` e `structlog` ao `requirements.txt`.
    -   [ ] Configurar `structlog` para logs em formato JSON.
    -   [ ] Desenvolver testes unitários para as novas lógicas (SQLAlchemy, Gemini, etc.).
-   [ ] **4.2. Otimizar o Ambiente de Execução e Padrões de Código**
    -   [ ] Implementar multi-stage builds no Dockerfile do `transcritor-pdf`.
    -   [ ] Configurar `Ruff` e `Black` e aplicá-los à base de código.

---

### Fase 5: Segurança

-   [ ] **5.1. Garantir a Segurança da API**
    -   [ ] Isolar o serviço `transcritor-pdf` na rede interna do Docker.
    -   [ ] Implementar a verificação de uma chave de API (`X-Internal-API-Key`) no `transcritor-pdf`.
    -   [ ] Configurar o `backend` para enviar a chave de API nas requisições para o `transcritor-pdf`.
