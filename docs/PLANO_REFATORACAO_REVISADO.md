# Plano de Refatoração: Microsserviço Transcritor-PDF v7.2

**Versão:** 7.2
**Data:** 02 de julho de 2025
**Autor:** Gemini

## 1. Resumo Executivo

Este plano de refatoração define a estratégia para a evolução do microsserviço `transcritor-pdf`. O objetivo principal é entregar um **MVP (Minimum Viable Product)** robusto, seguro e de alto valor. Para isso, a **migração para SQLAlchemy foi priorizada** como um passo fundamental e inicial.

As prioridades do MVP são:
1.  **Fundação Segura com SQLAlchemy:** Estabelecer uma camada de acesso a dados segura e manutenível.
2.  **Configuração Unificada:** Centralizar e validar as configurações do ambiente.
3.  **Migração para Google Gemini:** Substituir a dependência da OpenAI sobre uma base de código estável.
4.  **Detecção de Duplicados:** Otimizar custos e performance.
5.  **Funcionalidade de Ponta-a-Ponta:** Garantir um pipeline de processamento completo, resiliente e com extração híbrida.

Esta abordagem mitiga riscos de segurança e débito técnico desde o início, garantindo que o desenvolvimento subsequente seja mais rápido, seguro e fácil de manter.

---

## PRIMEIRA ENTREGA: MVP (FASES 1-3)

O objetivo é entregar um serviço funcional, inteligente e resiliente, construído sobre uma fundação de código sólida.

### Fase 1: Fundação de Código e Configuração (Prioridade Máxima)
*O alicerce do serviço. Esta fase estabelece a base para a segurança, estabilidade e manutenibilidade do sistema.*

**1.1. Migrar Acesso a Dados para SQLAlchemy (Tarefa Crítica)**
-   **Tarefa:** Refatorar todo o código de acesso ao banco de dados para usar o ORM assíncrono do SQLAlchemy. Implementar um gerenciador de contexto (`asynccontextmanager`) para as sessões do banco de dados.
-   **Justificativa:** **Prioridade máxima.** Esta migração elimina o risco de SQL Injection, padroniza o acesso a dados e cria uma base de código mais limpa, segura e testável, acelerando o desenvolvimento de todas as funcionalidades subsequentes.
-   **Resultado Esperado:** Código de acesso a dados padronizado, seguro e manutenível, pronto para as próximas fases.

**1.2. Unificar Configuração de Ambiente com Pydantic**
-   **Tarefa:** Centralizar todas as variáveis de ambiente no arquivo `.env` do `backend`. O `transcritor-pdf` deverá ler este arquivo como única fonte da verdade, utilizando a biblioteca `pydantic-settings`.
-   **Justificativa:** Elimina a duplicação, simplifica o gerenciamento e previne erros de ambiente.
-   **Resultado Esperado:** Um único arquivo `.env` controla a configuração de ambos os serviços de forma segura e validada.

**1.3. Implementar Detecção de Arquivos Duplicados**
-   **Tarefa:** Utilizando a nova camada de SQLAlchemy, adicionar a lógica para calcular o hash SHA-256 de um PDF e verificar sua existência no banco de dados antes do processamento.
-   **Justificativa:** Otimização de alto impacto que economiza custos e melhora a velocidade de resposta.
-   **Dependência Crítica:**
    1.  **Ação no `backend`:** Adicionar uma coluna `file_hash` (string, unique) à tabela `documents` via uma nova migração Alembic.
    2.  **Ação no `transcritor-pdf`:** Implementar a consulta de hash usando o ORM do SQLAlchemy.
-   **Resultado Esperado:** O sistema não reprocessa arquivos idênticos.

---

### Fase 2: Lógica de Negócio e IA (Coração do MVP)
*O núcleo de valor do produto, construído sobre a fundação sólida da Fase 1.*

**2.1. Migrar de OpenAI para Google Gemini**
-   **Tarefa:** Substituir todas as chamadas e dependências da OpenAI pelas do Google Gemini, utilizando a biblioteca `langchain_google_genai`.
-   **Justificativa:** Principal requisito técnico e de negócio da refatoração.
-   **Sub-tarefas Críticas:**
    1.  **Migração de Embedding:** O modelo a ser utilizado é o `text-embedding-004`, que gera vetores de **768 dimensões**.
    2.  **Ação no `backend`:** Criar uma nova migração Alembic para alterar a coluna `embedding` na tabela `document_chunks` para a nova dimensão.
    3.  **Ação no `transcritor-pdf`:** Limpar os dados das tabelas `document_chunks` e `documents` para evitar inconsistência de dimensões.
-   **Resultado Esperado:** O serviço utiliza exclusivamente os modelos Gemini.

**2.2. Implementar Extração Híbrida (Digital + OCR)**
-   **Tarefa:** Ativar e integrar a lógica de extração de texto de imagens (OCR) para criar um pipeline que decide a melhor estratégia para cada página do PDF.
-   **Justificativa:** Habilita o processamento de documentos escaneados, requisito fundamental para a viabilidade do produto.
-   **Implementação Sugerida:** Utilizar `pypdfium2` para detectar a presença de texto e decidir se a página deve passar pelo pipeline de OCR.
-   **Resultado Esperado:** O sistema processa de forma transparente e eficiente tanto PDFs com texto digital quanto PDFs escaneados.

---

### Fase 3: Qualidade e Robustez do Pipeline
*Garantir que o fluxo de ponta-a-ponta seja confiável e produza resultados de alta qualidade.*

**3.1. Otimizar o Processamento de Texto (Chunking)**
-   **Tarefa:** Substituir a função de chunking atual por `RecursiveCharacterTextSplitter` da Langchain, configurando um `chunk_overlap` de aproximadamente 20% do tamanho do chunk.
-   **Justificativa:** Melhora a coerência semântica dos chunks, o que impacta diretamente a qualidade dos resultados do RAG.
-   **Resultado Esperado:** Melhor qualidade no contexto recuperado para as consultas do LLM.

**3.2. Aumentar a Robustez das Tarefas Assíncronas (Celery)**
-   **Tarefa:** Implementar políticas de retentativa automática com backoff exponencial e tratamento de falha final nas tarefas Celery.
-   **Justificativa:** Garante que falhas temporárias (ex: instabilidade de APIs externas) não resultem em falhas permanentes no processamento.
-   **Resultado Esperado:** Tarefas assíncronas resilientes a erros transientes e com tratamento de falha final.

---

## SEGUNDA ENTREGA: PÓS-MVP (FASES 4-5)

Após a validação do MVP, as seguintes tarefas devem ser planejadas para elevar a qualidade técnica e a manutenibilidade do serviço.

#### Fase 4: Qualidade de Código e Observabilidade

**4.1. Implementar Estratégia de Testes e Observabilidade**
-   **Tarefa:** Desenvolver testes unitários e de integração (usando `pytest-asyncio` e mocks) e implementar logging estruturado em JSON com a biblioteca `structlog`.
-   **Justificativa:** Essencial para operar o serviço em produção de forma confiável e permitir futuras refatorações com segurança.
-   **Resultado Esperado:** Um serviço testável e observável.

**4.2. Otimizar o Ambiente de Execução e Padrões de Código**
-   **Tarefa:** Implementar multi-stage builds no Dockerfile para reduzir o tamanho da imagem de produção e adotar `Ruff` e `Black` para linting e formatação.
-   **Justificativa:** Melhora a segurança, a performance e a consistência do código.
-   **Resultado Esperado:** Imagens Docker menores e mais seguras; código padronizado.

---

#### Fase 5: Segurança

**5.1. Garantir a Segurança da API**
-   **Tarefa:** Isolar o serviço na rede interna do Docker e implementar autenticação via chave de API (`X-Internal-API-Key`) para a comunicação entre o `backend` e o `transcritor-pdf`.
-   **Justificativa:** Impede o acesso não autorizado ao microsserviço.
-   **Resultado Esperado:** O serviço só aceita requisições autenticadas vindas de componentes autorizados da aplicação.
