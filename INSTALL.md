# Guia de Instalação e Execução

Este documento descreve os passos exatos para clonar, configurar e executar o projeto `dashboard-adv` em um novo ambiente de desenvolvimento.

## 1. Instalação dos Pré-requisitos

Os comandos abaixo são para sistemas baseados em Debian/Ubuntu. Para outros sistemas operacionais (como macOS ou Windows), consulte a documentação oficial de cada ferramenta.

### Git
```bash
sudo apt-get update
sudo apt-get install git -y
```

### Docker e Docker Compose
Siga o guia oficial do Docker para instalar o Docker Engine e o plugin do Docker Compose:
[https://docs.docker.com/engine/install/ubuntu/](https://docs.docker.com/engine/install/ubuntu/)

### Node.js e npm
Recomendamos usar o `nvm` (Node Version Manager) para instalar o Node.js e o `npm`.

```bash
# Instalar nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Recarregar o shell para usar o nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Instalar Node.js v18 (que inclui o npm)
nvm install 18
```

## 2. Clonagem e Configuração Inicial

### 2.1. Clonar o Repositório

Abra seu terminal e execute os seguintes comandos para clonar o repositório e navegar para a branch correta:

```bash
# Clone o repositório a partir da URL fornecida
git clone https://github.com/docg1701/dashboard-adv.git

# Entre no diretório do projeto
cd dashboard-adv

# Mude para a branch específica do desenvolvimento
git checkout dia12
```

### 2.2. Configurar Variáveis de Ambiente do Backend

O backend precisa de chaves de API e segredos para funcionar.

1.  **Navegue até a pasta do backend:**
    ```bash
    cd backend
    ```

2.  **Crie o arquivo `.env` a partir do exemplo:**
    ```bash
    cp .env.example .env
    ```

3.  **Edite o arquivo `.env`** com um editor de texto e preencha, no mínimo, as seguintes variáveis:
    - `GOOGLE_API_KEY`: Cole sua chave de API do Google.
    - `SECRET_KEY`: Gere e cole uma chave segura para JWT. Use o comando abaixo no seu terminal para gerar uma:
      ```bash
      openssl rand -hex 32
      ```

### 2.3. Configurar Variáveis de Ambiente do Frontend

O frontend precisa saber onde a API está rodando.

1.  **Navegue até a pasta do frontend:**
    ```bash
    # A partir da raiz do projeto
    cd berry
    ```

2.  **Crie o arquivo `.env` e adicione a URL da API:**
    ```bash
    # Cria o arquivo .env e insere a variável de ambiente
    echo "VITE_API_BASE_URL=http://127.0.0.1:8000" > .env
    ```
    *Nota: `127.0.0.1:8000` é o endereço onde o contêiner do backend estará acessível a partir da sua máquina (host).*

## 3. Construção e Execução dos Serviços

### 3.1. Iniciar os Contêineres Docker

Volte para a raiz do projeto e use o Docker Compose para construir e iniciar o backend e o banco de dados.

```bash
# A partir da raiz do projeto
cd ..

# Construa as imagens e inicie os serviços em segundo plano (-d)
docker-compose up --build -d
```

Para verificar se os contêineres iniciaram corretamente, execute `docker-compose ps`. Você deve ver os serviços `dashboard_adv_api` e `dashboard_adv_db` com o status `running` ou `healthy`.

### 3.2. Executar as Migrações do Banco de Dados

Com os serviços rodando, aplique o schema do banco de dados executando o Alembic dentro do contêiner da API.

```bash
docker-compose exec api alembic upgrade head
```
*Isso criará todas as tabelas necessárias no banco de dados `appdb`.*

### 3.3. Criar o Usuário Administrador

Crie o primeiro usuário para poder acessar o sistema.

```bash
# Substitua com seu e-mail e uma senha forte
docker-compose exec api python scripts/create_admin_user.py --email admin@example.com --password your_strong_password
```

### 3.4. Iniciar o Frontend

Finalmente, instale as dependências do Node.js e inicie o servidor de desenvolvimento do frontend.

1.  **Navegue até a pasta `berry/`:**
    ```bash
    cd berry
    ```

2.  **Instale as dependências:**
    ```bash
    npm install
    ```

3.  **Inicie o servidor de desenvolvimento:**
    ```bash
    npm start
    ```

## 4. Acessando a Aplicação

- **Frontend (UI):** Abra seu navegador e acesse **[http://localhost:5173](http://localhost:5173)**.
- **Backend (API Docs):** A documentação interativa da API está disponível em **[http://localhost:8000/docs](http://localhost:8000/docs)**.

Faça o login com as credenciais de administrador criadas no passo 3.3.