# Backend - Django + Django Rest Framework SME - Autosserviço

## 🥞 Stack

- [Python 3.12](https://docs.python.org/3.12/)
- [Django 5.1](https://docs.djangoproject.com/en/5.1/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [drf-spectacular](https://drf-spectacular.readthedocs.io/) (OpenAPI schema)
- [pytest](https://docs.pytest.org/) + [pytest-django](https://pytest-django.readthedocs.io/)
- [Black](https://black.readthedocs.io/) + [Ruff](https://docs.astral.sh/ruff/) + [mypy](https://mypy.readthedocs.io/) + [pre-commit](https://pre-commit.com/)
- [Sphinx](https://www.sphinx-doc.org/) (documentação técnica)
- [Docker](https://docs.docker.com/) / [Docker Compose](https://docs.docker.com/compose/)

## 🛠️ Configurando o projeto

### 🔄 via HTTPS

```bash
git clone https://github.com/<organizacao>/SME-Autosservico-Backend.git
```

### 🔐 via SSH

```bash
git clone git@github.com:<organizacao>/SME-Autosservico-Backend.git
```

### 🐳 Rodando com Docker

**Ambiente de desenvolvimento** (hot-reload, `runserver`, suporte a debug remoto na porta `5678` via [debugpy](https://github.com/microsoft/debugpy)):

```bash
cp .env.example .env
docker compose -f docker-compose-dev.yml up --build
```

**Ambiente "prod-like"** (Gunicorn, `collectstatic` + `migrate` automáticos):

```bash
cp .env.example .env
docker compose up --build
```

Em ambos os casos a aplicação sobe em `http://localhost:8000`. Como ainda não há banco de dados definitivo para o projeto, as migrações são aplicadas em um arquivo SQLite local (dentro do container).

### 🐍 Rodando com virtualenv

#### Criando e ativando uma virtual env

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### Instalando as dependências do projeto

```bash
pip install -r requirements/local.txt
```

#### Configurando as variáveis de ambiente

```bash
cp .env.example .env
```

Ajuste os valores em `.env` conforme necessário. Por padrão, o projeto usa um arquivo SQLite local (`db.sqlite3`) — nenhum banco de dados externo é necessário para rodar o projeto nesta etapa. Quando um banco de dados definitivo for adotado, basta definir a variável `DATABASE_URL` (ex.: `postgres://usuario:senha@host:porta/nome`).

#### Instalando o pre-commit

```bash
pre-commit install
# ou: scripts/executar_precommit.sh
```

#### Rodando as migrações

```bash
python manage.py migrate
```

#### Executando o projeto

```bash
python manage.py runserver
```

#### Opcional: criando um super usuário

```bash
python manage.py createsuperuser
```

## 🔐 Autenticação

Como microsserviço, a autenticação entre serviços é feita por **chave de API** enviada em um header HTTP (nome e valor configuráveis via `API_KEY_HEADER`/`API_KEY` no `.env`). O endpoint de health check é sempre público, independente de autenticação. Usuários administradores autenticados via sessão do Django (`/admin/`) também conseguem acessar a documentação interativa (`/api/v1/docs/`).

## 🧪 Testes

### Executando os testes com Pytest

```bash
pytest
```

### Executando a cobertura dos testes

```bash
coverage run -m pytest
coverage report   # cobertura mínima exigida: 80%
coverage html
```

Testes unitários ficam dentro de cada app, em `apps/<dominio>/tests/`. A pasta `testes/` na raiz é reservada para testes E2E (Cypress/Postman), ainda não configurados.

## 📚 Documentação técnica (Sphinx)

```bash
cd docs
make html      # gera a documentação em docs/_build/html
make livehtml  # build com live-reload em http://localhost:9000
make apidocs   # regenera os .rst de API a partir dos apps
```

A documentação de domínio (regras de negócio, decisões arquiteturais) fica em `docs/dominios/<dominio>/`.

## 📄 API / OpenAPI

- Schema (JSON): `GET /api/v1/schema/`
- Swagger UI: `GET /api/v1/docs/` (requer login de superusuário do Django)
- Health check: `GET /api/v1/health/`

## 🩺 Health Check

O endpoint `GET /api/v1/health/` retorna `{"status": "ok"}` e não exige autenticação. É utilizado por probes de liveness/orquestradores para verificar se o processo da aplicação está no ar.

## 📄 Licença

A definir.
