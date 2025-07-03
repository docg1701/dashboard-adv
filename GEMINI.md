# GEMINI.md for the Modular Dashboard API Project

This document provides project-specific context and instructions for the Gemini CLI to ensure its responses are tailored to this project's needs and conventions.

## Project Overview

This project is a modular dashboard application with a frontend, a backend API, and a separate service for processing PDF documents.

*   **Frontend:** A single-page application (SPA) built with **React**, **Vite**, **TypeScript**, and **Material-UI (MUI)**. It uses **Zustand** for state management and **React Router** for routing.
*   **Backend:** A **FastAPI** application that serves as the main API. It's responsible for handling business logic, authentication (using JWT), and orchestrating the `transcritor-pdf` service. It uses **PostgreSQL** with **SQLAlchemy** and `pgvector` for data storage and vector similarity search.
*   **Transcritor PDF Service:** A separate **FastAPI** service that handles the asynchronous processing of PDF files. It uses **Celery** and **Redis** for task queuing and `langchain` for interacting with language models.

The entire application is containerized using **Docker** and orchestrated with **Docker Compose**.

## General Instructions

*   When generating new code, please follow the existing coding style and conventions of the project.
*   Ensure all new functions and classes have appropriate documentation (JSDoc for TypeScript, docstrings for Python).
*   All code should be compatible with the existing versions of the technologies used in the project.

## Frontend (React/TypeScript)

*   **Styling:** Use Material-UI (MUI) components and the existing theme located in `frontend/src/styles/theme.ts`.
*   **State Management:** Use Zustand for managing global state.
*   **API Calls:** All API calls should be made through the `api.ts` service file.
*   **Components:** Create new components in the `frontend/src/components` directory.

## Backend (FastAPI/Python)

*   **Database:** Use SQLAlchemy for all database interactions.
*   **API Endpoints:** New API endpoints should be added to the appropriate module in the `backend/app/modules` directory.
*   **Dependencies:** Add any new Python dependencies to the `backend/requirements.txt` file.

## Development Commands

Here are some common commands for this project:

*   **Start all services:** `docker-compose up -d`
*   **Stop all services:** `docker-compose down`
*   **View logs for all services:** `docker-compose logs -f`
*   **View logs for a specific service:** `docker-compose logs -f <service_name>` (e.g., `api`, `frontend`, `transcritor_pdf`)
*   **Run frontend tests:** `cd frontend && npm test`
*   **Run backend tests:** `cd backend && pytest`

## File Aliases

Here are some aliases for frequently accessed files:

*   `@frontend/app`: `frontend/src/App.tsx`
*   `@frontend/api`: `frontend/src/services/api.ts`
*   `@frontend/package`: `frontend/package.json`
*   `@backend/main`: `backend/app/main.py`
*   `@backend/api_router`: `backend/app/api_router.py`
*   `@backend/requirements`: `backend/requirements.txt`
*   `@transcritor/main`: `transcritor-pdf/src/main.py`
*   `@transcritor/tasks`: `transcritor-pdf/src/tasks.py`
*   `@docker-compose`: `docker-compose.yml`