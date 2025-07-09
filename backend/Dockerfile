# Use an official Python runtime as a parent image
FROM python:3.11-slim AS base

# --- Configurações Iniciais ---
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# --- Instalação de Dependências de Sistema ---
# Instalar dependências de sistema em uma camada separada para melhor cache
# Atualizar listas de pacotes, instalar dependências de build/runtime e limpar
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dependências de build/runtime (ex: psycopg2, outras libs C)
    build-essential \
    libpq-dev \
    # ---- DEPENDÊNCIAS REMOVIDAS (Fase 1 Refactor) ----
    # OCR (Tesseract) - Não mais necessário pelo Core API
    # tesseract-ocr tesseract-ocr-por \
    # -------------------------------------------------
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Instalação de Dependências Python ---
# Copiar apenas o requirements.txt primeiro para aproveitar o cache do Docker
COPY ./requirements.txt /app/requirements.txt
# Instalar dependências Python
# Usar --no-cache-dir para reduzir tamanho; --upgrade pip é boa prática
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Copiar Código da Aplicação ---
# Copiar o restante do código da aplicação
# Como estamos rodando como root, não precisamos de chown aqui.
COPY . /app/

# --- Configurações Finais ---
# (Não é necessário USER, pois continuaremos como root)

# Expor a porta configurada
EXPOSE 8000

# Comando para rodar a aplicação
# Usar python -m uvicorn para garantir que o PYTHONPATH seja corretamente manipulado, especialmente com --reload
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- NOTA SOBRE MULTI-STAGE BUILD ---
# Para uma imagem ainda menor, considere um multi-stage build:
# 1. Um estágio 'builder' (baseado em python:3.11) que instala build-essential, etc.,
#    cria um virtualenv, instala requirements.txt nele.
# 2. Um estágio final (baseado em python:3.11-slim) que copia apenas o virtualenv
#    do estágio 'builder' e o código da aplicação (COPY --from=builder /path/to/venv /path/to/venv).
#    Este estágio final não precisaria ter build-essential, etc., tornando a imagem menor.

