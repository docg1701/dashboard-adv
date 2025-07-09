# Roadmap Detalhado: dashboard-adv

Este documento detalha o plano de desenvolvimento do projeto, com tarefas organizadas por fases e prioridades.

**Legenda de Status:**
* ✅ - Concluído
* 🎯 - Foco Atual / Em Andamento
* 📝 - A Fazer
* 🔭 - Visão Futura
* ⚠️ - Bloqueado

---
## Manutenção e Refatoração Contínua 🎯

* ✅ **REFACTOR-DOC: Renomear "modular-dashboard" / "modular-dashboard-adv" para "dashboard-adv"** - Atualizar todas as menções nos arquivos de documentação para refletir o nome correto do projeto "dashboard-adv". (Concluído)
* ✅ **REFACTOR-DOC: Documentar Remoção do `pdf_processor_service`** - Atualizar a documentação de arquitetura (`01_ARQUITETURA.md`) e outros documentos relevantes para refletir a remoção do `pdf_processor_service` e a consolidação do fluxo de processamento de PDF via `transcritor_pdf_service`. (Concluído)
* ✅ **REFACTOR-ALEMBIC: Unificar Configuração do Alembic (Backend)** - Investigar os arquivos `alembic.ini`, manter apenas um, e garantir que `env.py` carregue a URL do banco de dados das configurações centrais, removendo senhas hardcoded. (Concluído)
* ✅ **REFACTOR-PDF-SERVICE: Remover Completamente `pdf_processor_service` (Backend)** - Remover a variável de configuração, o endpoint associado, o diretório do serviço e atualizar testes. (Concluído)

---

## Fase 1: Fundação e MVP ✅

**Épico:** Construir a base sólida da aplicação.
*Esta fase representa o estado atual do projeto, com a arquitetura modular e funcionalidades essenciais já implementadas.*

* ✅ **Estrutura do Backend:** Implementada com FastAPI.
* ✅ **Estrutura do Frontend:** Desenvolvida com React, TypeScript e Vite.
* ✅ **Containerização:** Aplicação totalmente containerizada com Docker e Docker Compose.
* ✅ **Sistema de Modularidade:** Implementado no backend e frontend.
* ✅ **Módulo de Autenticação:** Módulo central (`core_module`) com autenticação via JWT.
* ✅ **Banco de Dados:** Configurado com PostgreSQL e Alembic.
* ✅ **Módulos de Exemplo:** Criados `gerador_quesitos`, `ai_test`, `info`.
* ✅ **Documentação Inicial:** Criada a documentação base do projeto.
* ✅ **Pesquisa de Documentação (Docker, Redis, Celery):** Documentação oficial e melhores práticas pesquisadas.
* ✅ **Resumo de Documentação (Docker, Redis, Celery):** Sumários criados em `docs/reference/`.
* ✅ **Planejamento de Testes (Fase 1 Infra):** Plano de teste para a configuração da infraestrutura da Fase 1 criado.
* ✅ **Implementação de Testes (Fase 1 Infra):** Scripts de teste de integração para configuração da infraestrutura criados.
* ⚠️ **Execução de Testes (Fase 1 Infra):** - BLOCKED: Pendente de execução manual devido a limitações ambientais.

---

## Fase 1.5: Implementação do Sistema Jules-Flow ✅

**Épico:** Configurar o sistema de gerenciamento de tarefas Jules-Flow.
*Objetivo: Estabelecer a estrutura e os processos para que Jules (AI Agent) possa gerenciar suas próprias tarefas de desenvolvimento de forma organizada e rastreável.*

* ✅ **Criação da Estrutura Inicial do Jules-Flow:** Diretórios, arquivos base (`README.md`, `INSTRUCTIONS_FOR_JULES.md`, `TASK_INDEX.md`), e o template de tarefas (`task_template.md`) foram configurados.
* ✅ **Centralização de Documentos de Referência:** Documentos de referência do `transcritor-pdf` movidos para `docs/reference`.
* ✅ **Revisão de .env.example Pós-Fase 1:** Arquivos `.env.example` verificados e considerados adequados.
* ✅ **Definição do Processo de Criação de Tarefas On-Demand:** Documentação atualizada para permitir que o Desenvolvedor solicite tarefas diretamente, além daquelas geradas pelo Roadmap. (Referência: Commit de atualização de documentação do Jules-Flow)

---

## Fase 2: Integração Robusta com Serviço Transcritor PDF 🎯

**Épico:** Garantir a integração eficaz e segura do backend principal com o `transcritor_pdf_service` para processamento de documentos.
*Objetivo: Consolidar o fluxo de processamento de PDF, utilizando o `transcritor_pdf_service` como o único responsável pela manipulação de documentos, e o backend principal como gateway.*

#### Tarefas Priorizadas:

* ✅ **DOC-SEARCH: Pesquisar Documentação (FastAPI)** - Relevante para a API Gateway.
* ✅ **DOC-SUMMARIZE: Resumir Documentação (FastAPI para Gateway)** - Relevante para a API Gateway.
* ✅ **DEV: Criar Módulo `documents` na API Principal** - Estrutura base do módulo de documentos no backend.
* ✅ **TEST-PLAN: Planejar Testes para Módulo `documents` (Estrutura)** - Testes para a estrutura do módulo.
* ✅ **TEST-IMPL: Implementar Testes para Módulo `documents` (Estrutura)** - Testes para a estrutura do módulo.
* ✅ **DB-SYNC: Resolver Incompatibilidade de Schema de Documentos (Backend & Transcritor)** - Decisão arquitetural: O backend acessará os dados dos chunks (incluindo texto e embeddings) exclusivamente através da API do `transcritor_pdf_service` (Opção C). Isso significa que os modelos `DocumentChunk` do backend não armazenarão dados processados pelo transcritor. Os schemas permanecem distintos, respeitando a separação de responsabilidades. A "sincronização" ocorre via chamadas de API. (Concluído pela definição da estratégia de interação)
* ✅ **DOCKER: Configuração `docker-compose.yml` (Transcritor PDF)** - Revisar e garantir que `docker-compose.yml` configura corretamente o `transcritor_pdf_service` e remove quaisquer referências ao `pdf_processor_service` obsoleto. (Concluído)
* ✅ **Endpoint Gateway Upload: `/api/documents/upload` (Backend Principal)** - Implementado para upload e encaminhamento ao `transcritor_pdf_service`.
* ✅ **Plano de Testes Upload: `/api/documents/upload`** - Criado plano de testes para o endpoint de upload.
* ✅ **Testes Integração Upload: `/api/documents/upload`** - Implementados testes de integração (com ressalvas sobre execução ambiental).
* 📝 **TEST-EXEC: Executar Testes da Fase 2 (Integração Transcritor PDF)** - Executar todos os testes relevantes para a integração do gateway com o `transcritor_pdf_service`.

---

## Fase 3: Habilitando a Interação e Diálogo com Documentos (Backend do Transcritor-PDF) 📝

**Épico:** Habilitar a interação e diálogo com documentos através do backend do Transcritor-PDF.
*Objetivo: Desenvolver o backend do `transcritor-pdf` para suportar busca semântica e interação baseada em LLM com os textos extraídos. Esta fase foca na construção dos componentes de backend que permitem ao sistema 'entender' e responder perguntas sobre os documentos processados.*

* ✅ **DOC-SEARCH: Pesquisar Documentação (pgvector, LLM Client)**
* ✅ **DOC-SUMMARIZE: Resumir Documentação (pgvector, LLM Client)**
* ✅ **DEV: Implementar Endpoint de Processamento de PDF no Transcritor-PDF**
* ✅ **TEST-PLAN: Planejar Testes para Endpoint \`process-pdf\` (Transcritor)**
* ✅ **TEST-IMPL: Implementar Testes para Endpoint \`process-pdf\` (Transcritor)**
* ✅ **DEV: Desenvolver Inteligência de Busca Vetorial (Transcritor-PDF)**
* ✅ **TEST-PLAN: Planejar Testes para Busca Vetorial (Transcritor-PDF)**
* ✅ **TEST-IMPL: Implementar Testes para Busca Vetorial (Transcritor-PDF)**
* ✅ **DEV: Construir Orquestrador de Respostas com LLM (Transcritor-PDF)**
* ✅ **TEST-PLAN: Planejar Testes para Orquestrador de Respostas (Transcritor-PDF)**
* ✅ **TEST-IMPL: Implementar Testes para Orquestrador de Respostas (Transcritor-PDF)**
* ✅ **DEV: Criar Endpoint de Diálogo no Transcritor-PDF**
* ✅ **TEST-PLAN: Planejar Testes para Endpoint de Diálogo (Transcritor-PDF)**
* ✅ **TEST-IMPL: Implementar Testes para Endpoint de Diálogo (Transcritor-PDF)**
* ✅ **DEV: Expandir Gateway na API Principal para Diálogo**
* ✅ **TEST-PLAN: Planejar Testes para Gateway de Diálogo (API Principal)**
* ✅ **TEST-IMPL: Implementar Testes para Gateway de Diálogo (API Principal)**
* ⚠️ **TEST-EXEC: Executar Testes da Fase 3 (Transcritor-PDF e Gateway Diálogo)** - BLOCKED: Pendente de execução manual.

---

## Fase 4: Construção da Experiência do Usuário (Frontend) 📝

**Épico:** Desenvolver a interface do usuário para o novo módulo de análise e diálogo de documentos.
*Objetivo: Criar uma interface intuitiva no frontend que permita aos usuários fazer upload de documentos, visualizar o status do processamento, e interagir com os documentos processados através de um sistema de chat.*

* ✅ **DOC-SEARCH: Pesquisar Documentação (React, Zustand, Frontend API)**
* ✅ **DOC-SUMMARIZE: Resumir Documentação (Frontend para Analisador)**
* ✅ **DEV: Criar Página 'Analisador de Documentos' (Frontend)**
* ✅ **DEV: Desenvolver Interface de Upload na Página (Frontend)**
* ✅ **DEV: Implementar Feedback de Processamento no Frontend**
* ✅ **DEV: Construir Interface de Chat no Frontend**
* ✅ **DEV: Integrar ao Menu de Navegação Principal (Frontend)**
* ✅ **TEST-PLAN: Planejar Testes para Frontend do Analisador de Documentos**
* ✅ **TEST-IMPL: Implementar Testes para Frontend (Analisador)** - Testes de componente implementados.
* ⚠️ **TEST-EXEC: Executar Testes da Fase 4 (Frontend Analisador)** - BLOCKED: Pendente de execução manual dos testes.


---

## Fase 5: Melhorias do Frontend Core ✅

**Épico:** Aprimorar a usabilidade, consistência e performance da interface principal da aplicação.
*Objetivo: Refinar a experiência do usuário no 'core' da aplicação, estabelecendo uma base sólida para todos os módulos.*

#### Tarefas Sugeridas:

1.  ✅ **Implementar Notificações Globais (Toasts/Snackbars) no Core:** Implementar um mecanismo de notificação global (toasts/snackbars) no layout principal para dar feedback claro ao usuário sobre ações, erros ou informações importantes em pt-BR. Este sistema deverá ser utilizável por qualquer módulo.
2.  ✅ **Revisão da Responsividade e Layout do Core:** Realizar uma auditoria e otimizar o layout do `MainLayout` e componentes centrais (como navegação, cabeçalho, rodapé, se houver) para garantir uma experiência de usuário consistente e agradável em dispositivos móveis e tablets. Manter o idioma pt-BR.
3.  ✅ **Padronização de Componentes Visuais do Core:** Revisar os componentes visuais utilizados na interface principal (core) e criar/documentar um guia de estilo ou componentes reutilizáveis (ex: botões padrão, modais, cards) para garantir consistência visual. Todo o conteúdo em pt-BR.
4.  ✅ **Melhoria na Navegação Principal e Feedback Visual do Core:** Avaliar a usabilidade da navegação principal (menu lateral, cabeçalho) e implementar melhorias no feedback visual de interações (ex: estados de hover, active, focus) para tornar a experiência mais intuitiva. Manter o idioma pt-BR.
5.  ✅ **Otimização de Performance do Carregamento Inicial (Core):** Analisar e otimizar o tempo de carregamento inicial da aplicação principal, investigando o tamanho dos bundles, a estratégia de code splitting para o core e o carregamento de assets essenciais.

---

## Fase 6: Módulo Piloto e Integração (`gerador_quesitos`) 📝

**Épico:** Refatorar o `gerador_quesitos` para usar a nova arquitetura, servindo como modelo para futuros módulos.
*Objetivo: Validar o fluxo de ponta a ponta, desde o upload no frontend até a resposta da IA.*

* ✅ **Refatorar Frontend do Módulo:** Adicionar uma interface de upload de arquivo no módulo `gerador_quesitos` que chame o novo endpoint Gateway.
* ✅ **Refatorar Backend do Módulo (`gerador_quesitos`):** Endpoint `/gerar_com_referencia_documento` agora recebe `document_filename` e busca texto do DB. Endpoint `/gerar` (upload direto) foi removido.
* ✅ **TEST-PLAN (Fase 6 Piloto): Planejar Testes para `gerador_quesitos` Refatorado**.
* ✅ **TEST-IMPL (Fase 6 Piloto): Implementar Testes para `gerador_quesitos` Refatorado**. (Testes de frontend e backend implementados)
* ⚠️ **TEST-EXEC (Fase 6 Piloto): Executar Testes do `gerador_quesitos` Refatorado**. - BLOCKED: Pendente de execução manual dos testes.


---

## Fase 7: Governança e Maturidade 🔭

**Épico:** Amadurecer a plataforma, focando em usabilidade, monitoramento e segurança.
*Objetivo: Tornar a aplicação mais robusta e fácil de manter a longo prazo.*

* ✅ **Notificações no Frontend:** Implementar um mecanismo de notificação global (toasts/snackbars) para dar feedback claro ao usuário. (Coberto pela Fase 5 Core)
* 📝 **Logging e Monitoramento:** Configurar um sistema de logging estruturado para todos os serviços e avaliar uma ferramenta de Application Performance Monitoring (APM).
* 📝 **Sistema de Alertas (Backend):** Configurar alertas proativos via e-mail para falhas críticas, notificando a equipe de desenvolvimento.

---

## Fase 8: Submissão 📝

**Épico:** Preparar a aplicação para a entrega final, garantindo que todos os componentes estejam revisados e a documentação atualizada.
*Objetivo: Realizar as últimas verificações e garantir que o projeto esteja em um estado polido e completo conforme o escopo definido.*

* ⚠️ **ENV-REVIEW: Revisão Final do .env.example - BLOQUEADO: Execução de testes da Fase 4 pendente**
* ⚠️ **SUBMIT: Entregar todas as alterações do Roadmap Completo - BLOQUEADO: Revisão final do .env.example pendente**
