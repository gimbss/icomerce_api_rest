# iCommerce API

Uma API RESTful para uma plataforma de e-commerce, construída com FastAPI e SQLAlchemy. O projeto foi pensado para ser direto naquilo que faz, com regras de negócio claras e proteções onde importa.

## O que essa API faz

Gerencia o fluxo completo de um e-commerce: cadastro e autenticação de usuários, catálogo de produtos e pedidos. Tudo isso com camadas de proteção que vão além do CRUD básico.

## Funcionalidades principais

### Autenticação e segurança

- Registro e login com e-mail e senha
- **Verificação de email**: ao registrar, o usuário recebe um código de 6 dígitos que deve ser confirmado antes de poder fazer login
- **Senha forte obrigatória**: mínimo 8 caracteres, com maiúscula, minúscula, dígito e caractere especial
- Senhas armazenadas com hash Argon2, que é o padrão atual para armazenamento de senhas
- Tokens JWT para autenticação em cada requisição
- Cada token tem um identificador único (jti) e data de expiração configurável
- Os tokens são persistidos no banco de dados com hash SHA-256, nunca em texto plano
- Ao fazer login, todos os tokens anteriores do usuário são revogados automaticamente, garantindo que apenas uma sessão esteja ativa
- Validação dupla de token: assinatura JWT e consulta ao banco de dados, impedindo o uso de tokens revogados ou expirados
- Usuários só podem alterar seus próprios dados. Tentar modificar outro perfil retorna 403 Forbidden

### Roles e permissões

- Dois papéis: `admin` e `customer` (padrão no registro)
- Apenas administradores podem criar, atualizar e deletar produtos
- Apenas administradores podem alterar o status de pedidos
- Administradores podem promover ou rebaixar outros usuários via `PATCH /api/v1/auth/users/{user_id}/role`
- Proteção contra rebaixar o último admin (impede lockout do sistema)
- Clientes podem visualizar produtos, criar pedidos e gerenciar seus próprios pedidos

### Criação do primeiro admin

O primeiro administrador pode ser criado via script CLI:

```bash
# Configurar variáveis de ambiente
export ADMIN_EMAIL=admin@icomerce.com
export ADMIN_PASSWORD=Admin@1234
export ADMIN_NAME=Admin

# Criar o admin
python -m app.create_admin
```

O script é idempotente: se já existe um admin, ele avisa e não cria outro. O admin criado já nasce com `is_verified=True`, pulando a verificação de email.

Se o email já está em uso por um customer, o script avisa para usar o endpoint de promoção:

```
PATCH /api/v1/auth/users/{user_id}/role
Body: {"role": "admin"}
```

### Verificação de email

- Ao registrar, um código de verificação de 6 caracteres é gerado e armazenado no banco
- O código expira em 15 minutos
- O endpoint `POST /api/v1/auth/validate` confirma o email com o código
- O endpoint `POST /api/v1/auth/resend-verification` reenvia um novo código
- Usuários não verificados não podem fazer login (retorna 403)
- Envio de email configurável: backend `console` (dev) ou `smtp` (produção)

### Status de pedidos

- Pedidos possuem ciclo de vida: `pending` → `confirmed` → `shipped` → `delivered`
- Pedidos podem ser cancelados (`cancelled`) a qualquer momento
- Ao cancelar, o estoque dos produtos é restaurado automaticamente
- Timestamps `created_at` e `updated_at` para rastrear mudanças

### Controle de deleção

A deleção no sistema nunca é cega. Cada tipo de entidade tem suas próprias regras:

- **Produtos**: não podem ser deletados se já participaram de algum pedido. Isso preserva o histórico de compras e evita dados corrompidos. A tentativa retorna 409 Conflict com uma mensagem explicando o motivo
- **Pedidos**: ao deletar um pedido, o estoque de cada produto envolvido é restaurado automaticamente. Se um pedido tinha 3 unidades de um produto, essas 3 voltam ao estoque
- **Usuários**: podem remover sua própria conta, mas não a de outros

### Controle de estoque

- Ao criar um pedido, o sistema verifica se cada produto tem estoque suficiente antes de confirmar
- Se algum produto não tem estoque suficiente, o pedido inteiro é rejeitado com uma mensagem que informa o produto, a quantidade disponível e a quantidade solicitada
- O estoque é decrementado no momento da criação do pedido e restaurado caso o pedido seja cancelado ou deletado
- Não há condição de corrida simples porque o Unit of Work garante que as operações de leitura e escrita acontecem na mesma transação

### Paginação

- Listagem de produtos e pedidos suporta paginação com parâmetros `skip` e `limit`
- Respostas incluem metadados `skip`, `limit` e `total` para facilitar a navegação
- Limite máximo de 100 itens por página

### Controle de acesso por propriedade

- Um usuário só consegue visualizar e deletar seus próprios pedidos
- Tentar acessar o pedido de outro usuário retorna 403 Forbidden
- A listagem de pedidos também é filtrada pelo ID do usuário autenticado

## Arquitetura

O projeto segue uma separação em camadas bem definida:

```
api/              # Camada de apresentação (rotas, schemas, dependências)
app/
  config/          # Configuração (email settings)
  controllers/     # Orquestração das regras de negócio
  services/        # Lógica de autenticação e envio de email
  repositories/    # Acesso ao banco de dados
  models/          # Definição das tabelas (SQLAlchemy ORM)
  database/        # Configuração de conexão e Unit of Work
  security/        # Serviços de segurança (senha e token)
  exceptions/      # Exceções customizadas com códigos HTTP
```

O fluxo de uma requisição segue sempre: Rota -> Controller -> Repository -> Banco de dados. O Controller captura exceções de negócio e retorna respostas padronizadas com status e mensagem.

### Unit of Work

Todas as operações que modificam dados passam pelo padrão Unit of Work. Isso significa que ou a transação inteira funciona, ou nada é salvo. Se algo falhar no meio do caminho, o rollback é automático.

## Banco de dados

O projeto usa SQLite por padrão, configurado pela variável de ambiente `DATABASE_URL`. Para criar o banco:

```bash
python -m app.create_db
```

As tabelas são criadas automaticamente pelo SQLAlchemy a partir dos models.

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto (ou copie do `.env.example`):

```
DATABASE_URL=sqlite:///app/database/ecommerce.db
JWT_SECRET=sua-chave-secreta-aqui
JWT_EXPIRATION_HOURS=24

# Admin Seed (para criar o primeiro admin via python -m app.create_admin)
ADMIN_EMAIL=admin@icomerce.com
ADMIN_PASSWORD=Admin@1234
ADMIN_NAME=Admin

# Email Configuration
MAIL_BACKEND=console          # "console" para dev, "smtp" para produção
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587
MAIL_SMTP_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM_NAME=iCommerce
MAIL_FROM_ADDRESS=noreply@icomerce.com
```

## Como rodar

### Desenvolvimento local (SQLite)

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie o banco de dados e rode o servidor:

```bash
python -m app.create_db
```

Opcionalmente, popule o banco com dados de teste:

```bash
# Criar o primeiro admin
python -m app.create_admin

# Popular com produtos de teste (idempotente)
python -m app.seed_products

# Rodar o servidor
fastapi run main.py
```

### Produção (Docker + PostgreSQL)

```bash
docker compose up -d --build
```

A documentação interativa fica disponível em `http://127.0.0.1:8000/docs`, com botão de autorização Bearer já configurado no Swagger.

## Endpoints

### Autenticação

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| POST | `/api/v1/auth/register` | Registra um novo usuário | Pública |
| POST | `/api/v1/auth/login` | Autentica e retorna um token JWT | Pública |
| POST | `/api/v1/auth/validate` | Verifica email com código de 6 dígitos | Pública |
| POST | `/api/v1/auth/resend-verification` | Reenvia código de verificação | Pública |
| POST | `/api/v1/auth/validate-token` | Valida um token JWT existente | Pública |
| PUT | `/api/v1/auth/users/{user_id}` | Atualiza perfil do usuário | Bearer |
| DELETE | `/api/v1/auth/users/{user_id}` | Remove a conta do usuário | Bearer |
| POST | `/api/v1/auth/logout` | Revoga o token atual | Bearer |
| PATCH | `/api/v1/auth/users/{user_id}/role` | Promove ou rebaixa o role de um usuário | Admin |

### Produtos

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| POST | `/api/v1/products` | Cria um produto | Admin |
| GET | `/api/v1/products` | Lista produtos (paginado) | Bearer |
| GET | `/api/v1/products/{id}` | Busca produto por ID | Bearer |
| GET | `/api/v1/products/category/{category}` | Lista por categoria (paginado) | Bearer |
| PUT | `/api/v1/products/{id}` | Atualiza um produto | Admin |
| DELETE | `/api/v1/products/{id}` | Remove um produto (se não houver pedidos) | Admin |

### Pedidos

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| POST | `/api/v1/orders` | Cria um pedido | Bearer |
| GET | `/api/v1/orders/{id}` | Busca pedido por ID | Bearer |
| GET | `/api/v1/orders/user/{user_id}` | Lista pedidos do usuário (paginado) | Bearer |
| PATCH | `/api/v1/orders/{id}/status` | Atualiza status do pedido | Admin |
| DELETE | `/api/v1/orders/{id}` | Cancela um pedido e restaura estoque | Bearer |

### Parâmetros de paginação

Os endpoints de listagem aceitam os parâmetros de query:

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `skip` | int | 0 | Número de itens a pular |
| `limit` | int | 20 | Máximo de itens por página (1-100) |

Exemplo: `GET /api/v1/products?skip=10&limit=5`

Resposta inclui metadados de paginação:
```json
{
  "status": "success",
  "products": [...],
  "skip": 10,
  "limit": 5,
  "total": 45
}
```

## Testes

O projeto tem 190 testes de unidade e integração cobrindo controllers, repositories, serviços de segurança, email, roles e rotas da API:

```bash
python -m pytest tests/ -v
```

## Tratamento de erros

As exceções de negócio são organizadas em hierarquia e sempre retornam respostas consistentes:

| Exceção | HTTP | Quando acontece |
|---------|------|-----------------|
| `EmailAlreadyRegisteredError` | 409 | E-mail já cadastrado no registro |
| `InvalidCredentialsError` | 401 | E-mail ou senha incorretos |
| `EmailNotVerifiedError` | 403 | Login com email não verificado |
| `InvalidVerificationCodeError` | 400 | Código de verificação inválido ou expirado |
| `UserNotFoundError` | 404 | Usuário não encontrado |
| `ProductNotFoundError` | 404 | Produto não encontrado |
| `ProductHasOrdersError` | 409 | Tentativa de deletar produto com pedidos |
| `OrderNotFoundError` | 404 | Pedido não encontrado |
| `InsufficientStockError` | 400 | Estoque insuficiente para o pedido |
| `InvalidOrderStatusError` | 400 | Status de pedido inválido |
| `CannotDemoteLastAdminError` | 403 | Tentativa de rebaixar o último admin |

## Tecnologias

- **FastAPI** para a API
- **SQLAlchemy** como ORM
- **Argon2** para hash de senhas
- **PyJWT** para tokens de autenticação
- **SQLite** para desenvolvimento local
- **PostgreSQL** para produção (via Docker)
- **Python-dotenv** para configuração de ambiente
- **Email** com backends console (dev) e SMTP (produção)

## Docker

O projeto inclui configuração Docker para rodar com PostgreSQL em produção.

### Subir com Docker Compose

```bash
# Construir e subir os containers
docker compose up -d --build

# Ver logs
docker compose logs -f app

# Parar os containers
docker compose down
```

A API fica disponível em `http://localhost:8000/docs`.

O `docker-compose.yml` configura:
- **app**: Container da API FastAPI (porta 8000)
- **db**: Container PostgreSQL 17 (porta 5432) com healthcheck
- As tabelas são criadas automaticamente na inicialização

### Variáveis de ambiente para Docker

O `docker-compose.yml` já configura as variáveis padrão. Para personalizar, crie um arquivo `.env`:

```env
DATABASE_URL=postgresql://icomerce:icomerce_secret@db:5432/icomerce_db
JWT_SECRET=sua-chave-secreta-aqui
JWT_EXPIRATION_HOURS=24
MAIL_BACKEND=smtp
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587
MAIL_SMTP_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM_NAME=iCommerce
MAIL_FROM_ADDRESS=noreply@icomerce.com

# Admin Seed (para criar o primeiro admin via python -m app.create_admin)
ADMIN_EMAIL=admin@icomerce.com
ADMIN_PASSWORD=Admin@1234
ADMIN_NAME=Admin
```

### Rodar localmente com SQLite

Para desenvolvimento local sem Docker:

```bash
pip install -r requirements.txt
python -m app.create_db
fastapi run main.py
```

O banco SQLite é criado em `app/database/ecommerce.db`.