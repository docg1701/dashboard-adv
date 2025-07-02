# Plano de Refatoração: Microsserviço Transcritor-PDF
**Versão:** 6.1 (Plano Base + Análise e Refinamento)
**Data:** 26 de junho de 2025
**Autor:** Gemini (Análise e Refinamento)

## 1. Resumo Executivo

Este documento apresenta o plano de trabalho completo para a refatoração e modernização do microsserviço `transcritor-pdf`. O plano está organizado em fases sequenciais, priorizando a entrega de um **Produto Mínimo Viável (MVP)** que seja funcional, seguro, testável e observável.

O objetivo final é transformar o serviço em um componente robusto, eficiente e de fácil manutenção, alinhado com a arquitetura do ecossistema `dashboard-adv` e capaz de lidar com os principais tipos de documentos encontrados no domínio jurídico.

---

## PRIMEIRA ENTREGA: MVP (FASES 1-4)

As quatro primeiras fases constituem o escopo do MVP e devem ser executadas em sequência. O objetivo é entregar o núcleo de valor da refatoração o mais rápido possível, garantindo uma fundação técnica sólida.

### Fase 1: Fundação e Segurança (Prioridade Máxima)
*O alicerce do serviço. A conclusão desta fase é não negociável para que o sistema seja considerado estável e seguro.*

#### 1.1. Unificar Configuração e Padronizar Acesso a Dados
- **Tarefa:** Agrupar as tarefas de unificar o arquivo `.env` com o do backend, adotar o **SQLAlchemy** para todo o acesso ao banco de dados e usar **Pydantic** para carregar e validar as configurações de ambiente.
- **Justificativa:** Resolve vulnerabilidades críticas de gestão de conexão, elimina configurações "hardcoded" e estabelece um padrão arquitetural consistente com o restante do sistema.
- **Resultado Esperado:** Código mais limpo, seguro e de fácil manutenção, com um pool de conexões ao banco de dados gerenciado de forma eficiente e segura.

### Fase 2: Funcionalidades de Negócio (Prioridade Alta)
*O núcleo de valor que a refatoração se propõe a entregar ao utilizador final, agora incluindo a capacidade crítica de processamento de documentos escaneados.*

#### 2.1. Análise e Migração de OpenAI para Google Gemini
- **Tarefa:** Realizar uma análise de viabilidade e, em seguida, substituir todas as chamadas e dependências da OpenAI pelas do Google Gemini para geração de embeddings e processamento de linguagem.
- **Justificativa:** Cumpre um dos principais objetivos técnicos e de negócio da refatoração, centralizando a tecnologia de IA, que é pré-requisito para a extração híbrida.
- **Sub-tarefas Críticas (Análise de Viabilidade):**
    1.  **Mapeamento de API:** Mapear as funcionalidades da API da OpenAI para suas equivalentes na API do Gemini.
    2.  **Análise de Embedding:** Verificar a dimensão dos vetores de embedding do Gemini. Se for diferente do modelo atual, planejar a **migração do esquema do banco de dados** (alterar a coluna `VECTOR(dimensao)` via Alembic).
    3.  **Avaliação de Custo/Performance:** Estimar as diferenças de custo e performance entre as duas plataformas.
- **Resultado Esperado:** O serviço não possui mais dependências da API da OpenAI e utiliza exclusivamente os modelos Gemini para todas as operações de IA.

#### 2.2. Implementar Extração Híbrida de Texto (OCR + IA)
- **Tarefa:** Desenvolver uma lógica que, para cada página do PDF, decida entre a extração rápida de texto digital e a extração via IA para páginas que são imagens (PDFs escaneados).
- **Justificativa:** É um requisito fundamental para o produto ser viável no mercado jurídico. Sem essa capacidade, o sistema falharia em processar uma grande parte dos documentos do mundo real (laudos, petições antigas, etc.).
- **Detalhe da Implementação (Heurística de Decisão):**
    1.  Para cada página, tentar a extração digital (`page.get_text()`).
    2.  Se o texto retornado for vazio ou tiver menos que um limiar `X` de caracteres, a página é considerada uma imagem.
    3.  Nesse caso, a página é enviada para o pipeline de extração via IA (`extract_text_from_image`).
- **Resultado Esperado:** O sistema é capaz de processar tanto PDFs digitais quanto escaneados de forma eficiente e econômica.

#### 2.3. Implementar Detecção de Arquivos Duplicados
- **Tarefa:** Desenvolver o mecanismo de verificação via hash (SHA-256) do conteúdo binário do arquivo para evitar o reprocessamento de documentos idênticos.
- **Justificativa:** Aumenta a eficiência, gera economia direta de custos de processamento e de armazenamento, e melhora a velocidade de resposta para arquivos já conhecidos.
- **Dependência:** Esta tarefa requer uma **alteração no esquema do banco de dados do `backend`**, adicionando uma coluna para o hash na tabela `documents`. A mudança deve ser coordenada e gerenciada via Alembic.
- **Resultado Esperado:** Ao receber um PDF, o sistema calcula seu hash, verifica no banco de dados se já existe, e só inicia um novo processamento se o hash for inédito.

### Fase 3: Segurança
#### 3.1. Garantir a Segurança da API
- **Tarefa:** Isolar o serviço na rede interna do Docker (removendo a exposição de portas no `docker-compose.yml`) e implementar a autenticação via chave de API (`X-Internal-API-Key`) em um header HTTP.
- **Justificativa:** É a principal linha de defesa do serviço. Impede o acesso não autorizado de qualquer outra fonte que não seja o backend principal.
- **Resultado Esperado:** O microsserviço `transcritor-pdf` só aceita requisições que contenham a chave de API secreta correta, bloqueando todo o tráfego externo e não autorizado.

### Fase 4: Qualidade e Robustez (Prioridade Média)
*Pequenos ajustes de alto impacto que elevam a qualidade da experiência e a confiabilidade do serviço.*

#### 4.1. Aumentar a Robustez das Tarefas Assíncronas (Celery)
- **Tarefa:** Implementar políticas de retentativa automática com backoff exponencial (`retry_backoff`, `max_retries`) nas tarefas Celery.
- **Justificativa:** Garante que falhas temporárias (ex: instabilidade na rede ao chamar a API do Gemini) não resultem em falhas permanentes no processamento.
- **Gestão de Falha Final:** Se uma tarefa falhar após todas as retentativas, o sistema deve:
    1.  Atualizar o status do documento no banco de dados para "FALHOU".
    2.  Registrar o erro detalhado em um sistema de monitoramento (ex: Sentry) para análise.
- **Resultado Esperado:** Tarefas assíncronas são capazes de se recuperar de erros transientes de forma automática, e falhas permanentes são tratadas de forma graciosa.

#### 4.2. Otimizar o Processamento de Texto (Chunking)
- **Tarefa:** Substituir a função de chunking atual, baseada em tamanho fixo, por um divisor de texto mais sofisticado (ex: `RecursiveCharacterTextSplitter` da Langchain).
- **Justificativa:** A qualidade da divisão do texto (chunking) tem um impacto direto e significativo na eficácia das buscas e nas respostas geradas pelo sistema de RAG.
- **Resultado Esperado:** O texto dos documentos é dividido em pedaços com maior coerência semântica, melhorando a qualidade do contexto recuperado para as consultas do LLM.

### Fase 5: Testes e Observabilidade (Core do MVP)
*Garantir que o MVP seja confiável, testável e transparente em seu funcionamento.*

#### 5.1. Implementar Estratégia de Testes Automatizados
- **Tarefa:** Desenvolver um conjunto de testes automatizados para garantir a qualidade e prevenir regressões.
- **Justificativa:** Testes são essenciais para validar a lógica de negócio, garantir a estabilidade das integrações e permitir refatorações futuras com segurança.
- **Resultado Esperado:**
    - **Testes Unitários:** Para funções puras (lógica de chunking, heurística de extração).
    - **Testes de Integração:** Para a interação com o banco de dados e com as APIs externas (usando mocks).
    - **Testes de Contrato:** Para validar que a API do `transcritor-pdf` adere ao contrato esperado pelo `backend`.

#### 5.2. Implementar Observabilidade Essencial
- **Tarefa:** Integrar ferramentas de logging e monitoramento no serviço.
- **Justificativa:** É impossível operar um serviço em produção de forma confiável sem visibilidade sobre seu comportamento, performance e erros.
- **Resultado Esperado:**
    - **Logging Estruturado:** Logs são escritos em formato JSON para facilitar a busca e análise.
    - **Métricas Básicas:** O serviço expõe métricas (via Prometheus) para monitorar a taxa de sucesso/falha de processamentos, latência das tarefas e taxa de erros da API.

---

## SEGUNDA ENTREGA: PÓS-MVP (FASE 6)

Após a conclusão e validação do MVP, as seguintes tarefas devem ser planejadas para evoluir o produto.

### Fase 6: Melhoria Contínua (Prioridade Baixa)
- **Otimizar o Ambiente de Execução (Dockerfile):** Implementar multi-stage builds para reduzir o tamanho e a superfície de ataque da imagem Docker de produção.
- **Adoção de Padrões de Código:** Implementar `Ruff` e `Black` para linting e formatação automática, e integrar a verificação em um pipeline de CI.
- **Refinamento de Métricas e Alertas:** Expandir a observabilidade com dashboards detalhados e alertas automáticos para condições anômalas.

---

## Anexo: Relatório de Funcionamento Atual da Extração de Dados
*(O anexo original permanece válido e serve como justificativa para a tarefa 2.2)*
