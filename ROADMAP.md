# Roadmap de Desenvolvimento - dashboard-adv

Este documento detalha o plano de desenvolvimento do projeto, com tarefas organizadas por fases e prioridades.

**Legenda de Status:**
* ✅ - Concluído
* 🎯 - Foco Atual / Em Andamento
* 📝 - A Fazer
* 🔭 - Visão Futura

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
* ✅ **Pesquisa de Documentação (Docker, Redis, Celery):** Documentação oficial e melhores práticas pesquisadas (TASK-003).
* ✅ **Resumo de Documentação (Docker, Redis, Celery):** Sumários criados em `docs/reference/` (TASK-004).
* ✅ **Planejamento de Testes (Fase 1 Infra):** Plano de teste para a configuração da infraestrutura da Fase 1 criado (TASK-005).
* ✅ **Implementação de Testes (Fase 1 Infra):** Scripts de teste de integração para configuração da infraestrutura criados (TASK-006).
* ⚠️ **Execução de Testes (Fase 1 Infra):** BLOCKED - Pending manual execution due to environment limitations (TASK-007).

---

## Fase 1.2: Implementação do Sistema Jules-Flow ✅

**Épico:** Configurar o sistema de gerenciamento de tarefas Jules-Flow.
*Objetivo: Estabelecer a estrutura e os processos para que Jules (AI Agent) possa gerenciar suas próprias tarefas de desenvolvimento de forma organizada e rastreável.*

* ✅ **Criação da Estrutura Inicial do Jules-Flow:** Diretórios, arquivos base (`README.md`, `INSTRUCTIONS_FOR_JULES.md`, `TASK_INDEX.md`), e o template de tarefas (`task_template.md`) foram configurados.
* ✅ **Centralização de Documentos de Referência:** Documentos de referência do `transcritor-pdf` movidos para `docs/reference` (TASK-001).
* ✅ **Revisão de .env.example Pós-Fase 1:** Arquivos `.env.example` verificados e considerados adequados (TASK-002).
* ✅ **Definição do Processo de Criação de Tarefas On-Demand:** Documentação atualizada para permitir que o Desenvolvedor solicite tarefas diretamente, além daquelas geradas pelo Roadmap. (Referência: Commit de atualização de documentação do Jules-Flow)

---

## Fase 1.4: Melhorias do Frontend Core ✅

**Épico:** Aprimorar a usabilidade, consistência e performance da interface principal da aplicação.
*Objetivo: Refinar a experiência do usuário no 'core' da aplicação, estabelecendo uma base sólida para todos os módulos.*

* ✅ **Implementar Notificações Globais (Toasts/Snackbars) no Core:** Implementar um mecanismo de notificação global (toasts/snackbars) no layout principal para dar feedback claro ao usuário sobre ações, erros ou informações importantes em pt-BR. Este sistema deverá ser utilizável por qualquer módulo.
* ✅ **Revisão da Responsividade e Layout do Core:** Realizar uma auditoria e otimizar o layout do `MainLayout` e componentes centrais (como navegação, cabeçalho, rodapé, se houver) para garantir uma experiência de usuário consistente e agradável em dispositivos móveis e tablets. Manter o idioma pt-BR.
* ✅ **Padronização de Componentes Visuais do Core:** Revisar os componentes visuais utilizados na interface principal (core) e criar/documentar um guia de estilo ou componentes reutilizáveis (ex: botões padrão, modais, cards) para garantir consistência visual. Todo o conteúdo em pt-BR.
* ✅ **Melhoria na Navegação Principal e Feedback Visual do Core:** Avaliar a usabilidade da navegação principal (menu lateral, cabeçalho) e implementar melhorias no feedback visual de interações (ex: estados de hover, active, focus) para tornar a experiência mais intuitiva. Manter o idioma pt-BR.
* ✅ **Otimização de Performance do Carregamento Inicial (Core):** Analisar e otimizar o tempo de carregamento inicial da aplicação principal, investigando o tamanho dos bundles, a estratégia de code splitting para o core e o carregamento de assets essenciais.

---

## Fase 1.6: Criação da Base dos Módulos Jurídicos 📝

**Épico:** Desenvolver a estrutura base dos módulos jurídicos no frontend.
*Criação da base dos módulos jurídicos no frontend, sem o processamento de pdfs e interação com IA (não crie detalhes para os módulos, eles ainda serão definidos no momento do desenvolvimento)*

* **📝** Gerador de Quesitos
* **📝** Gerador de Impugnação de Laudo Pericial
* **📝** Análise de PPP e LT-CAT com Redação de Correspondência
* **📝** Construção da Tabela de Evolução da Enfermidade e da Ocupação vs. Limitações
* **📝** Analisar e Impugnar Decisão Judicial Previdenciária
* **📝** Organizador de Documentos Médicos
* **📝** Detectar e Corrigir Inconsistências em Documentos Gerados por I.A.
* **📝** Análise e Renovação de Documentação Médica
* **📝** Pesquisa de Jurisprudências em Direito Previdenciário

---

## Fase 2: Infraestrutura de Microserviços 🎯

**Épico:** Construir a pipeline de extração de documentos como um microserviço, utilizando a API principal como um Gateway seguro.
*Objetivo: Criar a fundação de backend necessária para o processamento de PDFs de forma isolada e escalável.*

#### Tarefas Priorizadas:

* ✅ **DOC-SEARCH: Pesquisar Documentação (FastAPI)** (TASK-008)
* ✅ **DOC-SUMMARIZE: Resumir Documentação (FastAPI para Gateway)** (TASK-009)
* ✅ **DEV: Criar Módulo `documents` na API Principal** (TASK-010)
* ✅ **TEST-PLAN: Planejar Testes para Módulo `documents` (Estrutura)** (TASK-011)
* ✅ **TEST-IMPL: Implementar Testes para Módulo `documents` (Estrutura)** (TASK-012)
1. 📝 **DB Schema:** Definir e criar a migração (Alembic) para a nova tabela `pdf_processed_chunks`.
2. 📝 **Orquestração:** Atualizar o `docker-compose.yml` para incluir o novo `pdf_processor_service` e garantir a comunicação entre os containers.
3. 📝 **Estrutura do Microserviço:** Criar a estrutura de pastas e arquivos (`Dockerfile`, `requirements.txt`, etc.) para o `pdf_processor_service`.
4. 📝 **Lógica do Microserviço:** Implementar a lógica de extração de texto e armazenamento no PostgreSQL dentro do `pdf_processor_service`.
5. 📝 **Endpoint do Microserviço:** Criar o endpoint `POST /process-pdf` no `worker`, que ficará acessível apenas dentro da rede do Docker.
6. 📝 **Endpoint Gateway na API Principal:** Implementar o endpoint `POST /api/v1/documents/upload-and-process`. Este endpoint será o único ponto de entrada público, responsável por:
   * Validar a autenticação e autorização do usuário.
   * Atuar como um proxy seguro, chamando o endpoint do microserviço.
   * ✅ Implementado endpoint `/api/documents/upload` (TASK-013) para upload e encaminhamento ao `transcritor_pdf_service`.
   * ✅ Criado plano de testes para o endpoint de upload `/api/documents/upload` (TASK-015).
   * ✅ Implementados testes de integração para `/api/documents/upload` (TASK-016, com ressalvas sobre execução ambiental).

---

## Fase 3: Integração com IA 🔭

**Épico:** Conectar os módulos jurídicos com os serviços de IA.
*integração dos módulos com a o processador de pdfs e modelos de IA*

---

## Fase 4: Governança e Maturidade 🔭

**Épico:** Amadurecer a plataforma, focando em usabilidade, monitoramento e segurança.
*Objetivo: Tornar a aplicação mais robusta e fácil de manter a longo prazo.*

* 📝 **Rever sistema RBAC:** Adaptar o sistema de Role-Based Access Control para perfis de um escritório de advocacia.
* 📝 **Sistema de Logging Robusto:** Implementar um sistema de logging estruturado e centralizado para todos os serviços.
