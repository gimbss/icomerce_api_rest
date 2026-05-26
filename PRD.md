# PRD — iCommerce API

**Versão:** 2.0  
**Data:** 25/05/2026  
**Autor:** Gilberto Neto  

---

## 1. Visão Geral

A iCommerce API é uma plataforma RESTful de e-commerce construída com **FastAPI + SQLAlchemy + SQLite**, seguindo arquitetura em camadas (Router → Controller → Service/Repository → Model). O sistema gerencia o fluxo completo de um e-commerce: autenticação de usuários, catálogo de produtos e pedidos, com proteções de segurança robustas.

### 1.1 Estado Atual

| Módulo | Funcionalidade | Status |
|--------|---------------|--------|
| **Auth** | Registro, Login, Validação de Token, Verificação de Email, Reenvio de Código, Atualização de Perfil, Deleção de Usuário | ✅ Estável |
| **Products** | CRUD completo + filtro por categoria + paginação (criar/editar/deletar = admin only) + seed de 26 produtos | ✅ Estável |
| **Orders** | Criação, Listagem paginada por usuário, Busca por ID, Deleção, Atualização de Status (admin only) | ✅ Estável |
| **Security** | JWT com dupla validação (assinatura + DB), Argon2 para senhas, Senha forte obrigatória, Revogação de tokens | ✅ Estável |
| **Roles** | Campo `role` no User (admin/customer), restrição de admin em produtos e status de pedidos, endpoint de promoção de role, proteção do último admin | ✅ Estável |
| **Email** | Verificação de email com código de 6 dígitos, bloqueio de login para não verificados | ✅ Estável |
| **Testes** | 190 testes cobrindo todas as camadas | ✅ Estável |

### 1.2 Arquitetura

```
api/              → Camada de apresentação (rotas, schemas, dependências)
app/
  controllers/    → Orquestração das regras de negócio
  services/       → Lógica de autenticação (hash, JWT, validação)
  repositories/   → Acesso ao banco de dados
  models/         → Definição das tabelas (SQLAlchemy ORM)
  database/       → Configuração de conexão e Unit of Work
  security/       → Serviços de segurança (senha e token)
  exceptions/     → Exceções customizadas com códigos HTTP
```

---

## 2. Próximos Passos (Roadmap Prioritário)

### 2.1 🔴 P0 — Validação de Email na Criação de Usuário ✅ IMPLEMENTADO

**Status:** ✅ Implementado e testado (171 testes passando)

**O que foi implementado:**
- Campo `is_verified` no modelo `User` (default=False)
- Modelo `EmailVerification` com código de 6 dígitos alfanuméricos e expiração de 15 minutos
- `POST /api/v1/auth/validate` agora valida email com código (ao invés de token JWT)
- `POST /api/v1/auth/validate-token` preserva a funcionalidade antiga de validação de token
- `POST /api/v1/auth/resend-verification` para reenvio de código
- Login bloqueado para usuários não verificados (retorna 403)
- Exceções `EmailNotVerifiedError` e `InvalidVerificationCodeError`

---

### 2.2 🔴 P0 — Exigência de Senha Forte ✅ IMPLEMENTADO

**Status:** ✅ Implementado e testado

**O que foi implementado:**
- Validação de senha forte: mínimo 8 caracteres, maiúscula, minúscula, dígito, caractere especial
- `validate_strong_password()` em `api/schemas/user_schema.py`
- `field_validator("password")` em `RegisterUserRequest` e `UpdateUserProfileRequest`
- Mensagens de erro detalhadas indicando quais critérios faltam
- 7 testes de senha forte no `test_api_routers.py`

---

### 2.3 🟡 P1 — Alterar `validate` para Validar Email ao Invés de Token ✅ IMPLEMENTADO

**Status:** ✅ Implementado e testado

**O que foi implementado:**
- `POST /api/v1/auth/validate` → recebe `{"email": "...", "code": "A3B9K2"}` → verifica email
- `POST /api/v1/auth/validate-token` → preserva funcionalidade antiga de validação de token JWT
- `POST /api/v1/auth/resend-verification` → reenvia código de verificação

---

## 3. Funcionalidades Sugeridas (Backlog)

### 3.1 🟢 P2 — Roles e Permissões (Admin/User) ✅ IMPLEMENTADO

**Status:** ✅ Implementado e testado

**O que foi implementado:**
- Campo `role` no modelo `User` com valores `admin` e `customer` (default="customer")
- Dependência `get_current_admin_user_id()` que verifica se o usuário é admin
- Endpoints de criar, atualizar e deletar produtos restritos a admin (retorna 403 se não admin)
- Endpoint `PATCH /api/v1/orders/{order_id}/status` restrito a admin
- Testes: 3 testes de restrição admin em produtos, 2 testes de restrição admin em status de pedidos

---

### 3.2 🟢 P2 — Status de Pedido e Histórico ✅ IMPLEMENTADO

**Status:** ✅ Implementado e testado

**O que foi implementado:**
- Campo `status` no modelo `Order` com valores: `pending`, `confirmed`, `shipped`, `delivered`, `cancelled`
- Campos `created_at` e `updated_at` no modelo `Order`
- `PATCH /api/v1/orders/{order_id}/status` (admin only) para atualizar status
- Cancelamento (`cancelled`) restaura estoque automaticamente
- `InvalidOrderStatusError` para status inválidos
- Schemas `UpdateOrderStatusRequest` e respostas com status/timestamps
- Testes: 5 testes de status de pedido (atualização, admin-only, cancelamento com estoque, status inválido, timestamps)

---

### 3.3 🟢 P2 — Paginação e Filtros ✅ IMPLEMENTADO

**Status:** ✅ Implementado e testado

**O que foi implementado:**
- `GET /api/v1/products?skip=0&limit=20` — Lista produtos com paginação
- `GET /api/v1/products/category/{category}?skip=0&limit=20` — Lista por categoria com paginação
- `GET /api/v1/orders/user/{user_id}?skip=0&limit=20` — Lista pedidos do usuário com paginação
- Parâmetros `skip` (default=0, ge=0) e `limit` (default=20, ge=1, le=100)
- Respostas incluem `skip`, `limit` e `total` para metadados de paginação
- `api/schemas/pagination_schema.py`: Schemas genéricos `PaginationParams` e `PaginatedMeta`
- Repositories retornam tupla `(items, total)` com `offset()` e `limit()`
- 2 testes de paginação (produtos e pedidos)

---

### 3.4 🟢 P2 — Criação e Gestão de Admins ✅ IMPLEMENTADO

**Status:** ✅ Implementado e testado

**O que foi implementado:**
- `PATCH /api/v1/auth/users/{user_id}/role` — endpoint admin-only para promover/rebaixar usuários
- Schema `UpdateUserRoleRequest` com `Literal["admin", "customer"]` para validação
- `CannotDemoteLastAdminError` (403) — impede rebaixar o último admin (proteção contra lockout)
- `UserRepository.get_admin_users()` — retorna lista de admins para verificação
- `UserRepository.update_user()` agora aceita parâmetro `role`
- `AuthService.update_user_role()` — lógica de negócio com proteção do último admin
- `AuthController.update_user_role()` — orquestração e tratamento de erros
- Seed script `python -m app.create_admin` — cria o primeiro admin via CLI com env vars
- Admin criado via seed já nasce com `is_verified=True` (pula verificação de email)
- Script idempotente: se já existe admin, avisa e não cria outro
- Se email já está em uso por customer, avisa para usar o endpoint de promoção
- 7 testes de integração (API) + 4 testes unitários (service)

**Variáveis de ambiente do seed script:**
```
ADMIN_EMAIL=admin@icomerce.com
ADMIN_PASSWORD=Admin@1234
ADMIN_NAME=Admin
ADMIN_ADDRESS=opcional
```

---

### 3.5 🟢 P2 — Seed de Produtos para Teste ✅ IMPLEMENTADO

**Status:** ✅ Implementado e testado

**O que foi implementado:**
- `app/seed_products.py` — Script CLI para popular o banco com 26 produtos de teste
- `ProductRepository.get_product_by_name()` — Método para buscar produto por nome (idempotência)
- Categorias: Hardware (6), Periféricos (5), Monitores (3), Armazenamento (3), Redes (3), Notebooks (2), Mobiliário (2), Áudio (2)
- Script idempotente: produtos com nomes já existentes são ignorados
- Integrado ao `docker-compose.yml` (executado no startup após create_db e create_admin)
- Executável via `python -m app.seed_products`

---

### 3.6 🟢 P2 — Recuperação de Senha

**Justificativa:** Usuários não têm como recuperar acesso à conta se esquecerem a senha.

| ID | Requisito | Prioridade |
|----|-----------|------------|
| PWD-01 | Endpoint `POST /api/v1/auth/forgot-password` — envia código de recuperação para o email | Média |
| PWD-02 | Endpoint `POST /api/v1/auth/reset-password` — redefine a senha com o código | Média |
| PWD-03 | Código de recuperação expira em 15 minutos | Média |
| PWD-04 | Reutilizar modelo `EmailVerification` com tipo `password_reset` | Baixa |

---

### 3.7 🟢 P3 — Soft Delete para Produtos

**Justificativa:** Produtos com pedidos não podem ser deletados, mas deveriam poder ser desativados.

| ID | Requisito | Prioridade |
|----|-----------|------------|
| SDL-01 | Adicionar campo `is_active` no modelo `Product` (default `True`) | Baixa |
| SDL-02 | `DELETE /api/v1/products/{id}` muda `is_active=False` ao invés de deletar | Baixa |
| SDL-03 | `GET /api/v1/products` retorna apenas produtos ativos por padrão | Baixa |
| SDL-04 | Admin pode ver produtos inativos com query param `?include_inactive=true` | Baixa |

---

### 3.8 🟢 P3 — Logging e Auditoria

**Justificativa:** Não há registro de ações dos usuários para fins de auditoria.

| ID | Requisito | Prioridade |
|----|-----------|------------|
| LOG-01 | Criar modelo `AuditLog` com `user_id`, `action`, `resource_type`, `resource_id`, `timestamp` | Baixa |
| LOG-02 | Registrar ações de criação, atualização e deleção | Baixa |
| LOG-03 | Endpoint `GET /api/v1/admin/audit` para consultar logs (apenas admin) | Baixa |

---

### 3.9 🟢 P3 — Rate Limiting

**Justificativa:** Endpoints públicos (register, login, validate) estão expostos sem limitação.

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RAT-01 | Limitar `POST /api/v1/auth/register` a 5 requisições por minuto por IP | Baixa |
| RAT-02 | Limitar `POST /api/v1/auth/login` a 10 requisições por minuto por IP | Baixa |
| RAT-03 | Limitar `POST /api/v1/auth/validate` a 10 requisições por minuto por IP | Baixa |

---

## 4. Plano de Implementação

### Fase 1 — P0 (Imediata) ✅ CONCLUÍDA

| # | Tarefa | Status |
|---|--------|--------|
| 1 | Campo `is_verified` no modelo `User` | ✅ |
| 2 | Modelo `EmailVerification` | ✅ |
| 3 | `EmailVerificationRepository` | ✅ |
| 4 | `AuthService.register_user` gera código de verificação | ✅ |
| 5 | `AuthService.authenticate_user` checa `is_verified` | ✅ |
| 6 | `POST /validate` valida email com código | ✅ |
| 7 | `POST /resend-verification` | ✅ |
| 8 | Validação de senha forte | ✅ |
| 9 | `UnitOfWork` inclui novo repositório | ✅ |
| 10 | Testes atualizados e novos | ✅ (190 testes) |
| 11 | `PUBLIC_PATH_PREFIXES` atualizado | ✅ |

### Fase 2 — P1 ✅ CONCLUÍDA

| # | Tarefa | Status |
|---|--------|--------|
| 1 | Roles e Permissões (Admin/User) | ✅ |
| 2 | Status de Pedido e Histórico | ✅ |
| 3 | Criação e Gestão de Admins (seed + endpoint) | ✅ |

### Fase 3 — P2 ✅ CONCLUÍDA

| # | Tarefa | Status |
|---|--------|--------|
| 1 | Paginação e Filtros | ✅ |
| 2 | Criação e Gestão de Admins | ✅ |
| 3 | Seed de Produtos para Teste | ✅ |

### Fase 4 — P3 (Backlog)

| # | Tarefa | Estimativa |
|---|--------|------------|
| 1 | Recuperação de Senha | ~2 horas |
| 2 | Soft Delete para Produtos | ~1 hora |
| 3 | Logging e Auditoria | ~2 horas |
| 4 | Rate Limiting | ~1 hora |

---

## 5. Considerações Técnicas

### 5.1 Envio de Email ✅ IMPLEMENTADO

**Status:** ✅ Implementado com backends console e SMTP

**O que foi implementado:**
- `app/config/mail_config.py`: Configuração de email via variáveis de ambiente (`MailSettings` dataclass)
- `app/services/email_service.py`: `EmailService` com dois backends:
  - `console`: Imprime o email no stdout (para desenvolvimento e testes)
  - `smtp`: Envia via servidor SMTP real (para produção)
- `MAIL_BACKEND` no `.env` controla qual backend usar
- `AuthService` agora recebe `email_service` por injeção de dependência
- Envio automático de código de verificação no registro e reenvio
- Testes unitários usam `MagicMock(spec=EmailService)` para isolar o envio
- 5 testes específicos do EmailService (console, SMTP, falha, env config, defaults)

**Configuração do `.env`:**
```
MAIL_BACKEND=console          # "console" para dev, "smtp" para produção
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587
MAIL_SMTP_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM_NAME=iCommerce
MAIL_FROM_ADDRESS=noreply@icomerce.com
```

### 5.2 Migração de Banco

Como o projeto usa SQLite sem Alembic, a adição de novos campos requer:
- Recriar o banco (em desenvolvimento) ou
- Adicionar migração manual com `ALTER TABLE`

**Recomendação:** Adicionar Alembic para migrações futuras.

### 5.3 Breaking Changes

A mudança do endpoint `/validate` é uma **breaking change**:
- Clientes que usam `POST /validate` com `{"token": "..."}` precisarão ser atualizados
- A resposta muda de `{"status": "success", "user_id": N}` para `{"status": "success", "user_id": N, "email": "...", "verified": true}`

---

## 6. Métricas de Sucesso

| Métrica | Meta |
|---------|------|
| Cobertura de testes | Manter >90% após cada fase |
| Tempo de resposta da API | <200ms para endpoints existentes |
| Zero regressões | Todos os testes continuam passando (178 atualmente) |
| Validação de email | 100% dos novos registros requerem verificação |
| Validação de nome | 0 registros com nome < 4 caracteres alfanuméricos |

---

## 7. Referências

- [README.md](README.md) — Documentação atual do projeto
- [Memória: token-auth-flow.md](memories/repo/token-auth-flow.md) — Fluxo de autenticação JWT
- [Memória: stock-and-orders.md](memories/repo/stock-and-orders.md) — Lógica de estoque e pedidos
- [Memória: project-review.md](memories/repo/project-review.md) — Revisão anterior do projeto