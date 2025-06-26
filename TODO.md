# Refactoring TODO - transcritor-pdf

## PRIMEIRA ENTREGA: MVP (FASES 1-4)

### Fase 1: Fundação e Segurança (Prioridade Máxima)
- [ ] **1.1. Unificar Configuração e Padronizar Acesso a Dados**
    - [ ] Unificar arquivo `.env` com o do backend.
    - [ ] Adotar SQLAlchemy para todo o acesso ao banco de dados.
    - [ ] Usar Pydantic para carregar e validar as configurações de ambiente.
    - [ ] Implementar gerenciamento de segredos para produção (Docker Secrets ou variáveis de ambiente).
- [ ] **1.2. Garantir a Segurança da API**
    - [ ] Isolar o serviço na rede interna do Docker (remover exposição de portas no `docker-compose.yml`).
    - [ ] Implementar autenticação via chave de API (`X-Internal-API-Key`) em um header HTTP.
    - [ ] Carregar `X-Internal-API-Key` usando o mecanismo de gerenciamento de segredos.

### Fase 2: Funcionalidades de Negócio (Prioridade Alta)
- [ ] **2.1. Análise e Migração de OpenAI para Google Gemini**
    - [ ] **Análise de Viabilidade:**
        - [ ] Mapear funcionalidades da API OpenAI para equivalentes na API Gemini.
        - [ ] Analisar dimensão dos vetores de embedding do Gemini.
        - [ ] Planejar migração do esquema do banco de dados (se necessário, via Alembic).
        - [ ] Estimar diferenças de custo/performance.
    - [ ] Substituir todas as chamadas e dependências da OpenAI pelas do Google Gemini.
- [ ] **2.2. Implementar Extração Híbrida de Texto (OCR + IA)**
    - [ ] Desenvolver lógica para decidir entre extração digital e via IA por página.
    - [ ] Implementar heurística de decisão (ex: `page.get_text()`, limiar de caracteres).
    - [ ] Integrar com pipeline de extração via IA (`extract_text_from_image`).
- [ ] **2.3. Implementar Detecção de Arquivos Duplicados**
    - [ ] Desenvolver mecanismo de verificação via hash (SHA-256) do conteúdo binário.
    - [ ] Coordenar alteração no esquema do banco de dados do backend (adicionar coluna para hash via Alembic).

### Fase 3: Qualidade e Robustez (Prioridade Média)
- [ ] **3.1. Aumentar a Robustez das Tarefas Assíncronas (Celery)**
    - [ ] Implementar políticas de retentativa automática com backoff exponencial (`retry_backoff`, `max_retries`) nas tarefas Celery.
    - [ ] Implementar gestão de falha final:
        - [ ] Atualizar status do documento no BD para "FALHOU".
        - [ ] Registrar erro detalhado em sistema de monitoramento (ex: Sentry).
- [ ] **3.2. Otimizar o Processamento de Texto (Chunking)**
    - [ ] Substituir função de chunking atual por divisor de texto mais sofisticado (ex: `RecursiveCharacterTextSplitter` da Langchain).

### Fase 4: Testes e Observabilidade (Core do MVP)
- [ ] **4.1. Implementar Estratégia de Testes Automatizados**
    - [ ] Desenvolver testes unitários (lógica de chunking, heurística de extração).
    - [ ] Desenvolver testes de integração (BD, APIs externas com mocks).
    - [ ] Desenvolver testes de contrato (API do transcritor-pdf vs backend).
- [ ] **4.2. Implementar Observabilidade Essencial**
    - [ ] Implementar logging estruturado (JSON).
    - [ ] Expor métricas básicas (Prometheus: taxa de sucesso/falha, latência, erros API).

## SEGUNDA ENTREGA: PÓS-MVP (FASE 5)

### Fase 5: Melhoria Contínua (Prioridade Baixa)
- [ ] Otimizar o Ambiente de Execução (Dockerfile com multi-stage builds).
- [ ] Adotar Padrões de Código (Ruff, Black, CI).
- [ ] Refinamento de Métricas e Alertas (Dashboards, alertas automáticos).
