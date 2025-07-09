# Dockerfile for the transcritor-pdf service

# Use uma imagem base do Python
FROM python:3.11-slim

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Instala as dependências do sistema, incluindo curl para o healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

# Copia o arquivo de requisitos e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o diretório de trabalho
COPY . .

# Expõe a porta que a aplicação vai rodar
EXPOSE 8002

# Comando para rodar a aplicação com Uvicorn
# O host 0.0.0.0 torna a aplicação acessível de fora do contêiner
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]
