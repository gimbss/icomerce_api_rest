"""
Script CLI para criar o primeiro usuário admin.

Uso:
    python -m app.create_admin

Variáveis de ambiente obrigatórias:
    ADMIN_EMAIL    - Email do admin
    ADMIN_PASSWORD - Senha do admin (mínimo 8 chars, maiúscula, minúscula, dígito, especial)
    ADMIN_NAME     - Nome do admin

Variáveis de ambiente opcionais:
    ADMIN_ADDRESS  - Endereço do admin (padrão: None)

O script é idempotente: se já existir um admin, ele avisa e não cria outro.
Se o email já estiver em uso por um customer, ele avisa que é necessário usar
o endpoint PATCH /auth/users/{user_id}/role para promover o usuário.
"""

import os
import sys

from app.database.unit_of_work import UnitOfWork
from app.security.password import PasswordService


def validate_password_strength(password: str) -> list[str]:
    """Valida a força da senha. Retorna lista de erros (vazia se válida)."""
    import re
    errors = []
    if len(password) < 8:
        errors.append("mínimo de 8 caracteres")
    if not re.search(r"[A-Z]", password):
        errors.append("pelo menos uma letra maiúscula")
    if not re.search(r"[a-z]", password):
        errors.append("pelo menos uma letra minúscula")
    if not re.search(r"\d", password):
        errors.append("pelo menos um dígito")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        errors.append("pelo menos um caractere especial")
    return errors


def create_admin():
    """Cria o primeiro usuário admin a partir de variáveis de ambiente."""
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    name = os.environ.get("ADMIN_NAME")
    address = os.environ.get("ADMIN_ADDRESS")

    # Validar campos obrigatórios
    missing = []
    if not email:
        missing.append("ADMIN_EMAIL")
    if not password:
        missing.append("ADMIN_PASSWORD")
    if not name:
        missing.append("ADMIN_NAME")

    if missing:
        print(f"❌ Variáveis de ambiente obrigatórias não definidas: {', '.join(missing)}")
        print("   Defina ADMIN_EMAIL, ADMIN_PASSWORD e ADMIN_NAME antes de executar.")
        sys.exit(1)

    # Validar força da senha
    password_errors = validate_password_strength(password)
    if password_errors:
        print(f"❌ Senha fraca: falta {', '.join(password_errors)}")
        sys.exit(1)

    password_service = PasswordService()

    with UnitOfWork() as uow:
        # Verificar se já existe algum admin
        admin_users = uow.users.get_admin_users()
        if admin_users:
            print(f"ℹ️  Admin já existe: {admin_users[0].email} (id={admin_users[0].id})")
            print("   Para criar mais admins, use o endpoint PATCH /api/v1/auth/users/{{user_id}}/role")
            return

        # Verificar se o email já está em uso
        existing_user = uow.users.get_user_by_email(email)
        if existing_user:
            print(f"⚠️  Email '{email}' já está em uso por um usuário customer (id={existing_user.id}).")
            print("   Para promover este usuário a admin, use:")
            print(f"   PATCH /api/v1/auth/users/{existing_user.id}/role")
            print('   Body: {"role": "admin"}')
            sys.exit(1)

        # Criar o admin
        hashed_password = password_service.hash(password)
        admin_user = uow.users.create_user(
            email=email,
            password=hashed_password,
            name=name,
            address=address,
        )
        # Definir role e is_verified diretamente
        uow.users.update_user(admin_user.id, role="admin", is_verified=True)

        print(f"✅ Admin criado com sucesso!")
        print(f"   Email: {admin_user.email}")
        print(f"   Nome:  {admin_user.name}")
        print(f"   ID:    {admin_user.id}")
        print(f"   Role:  admin")
        print(f"   Verificado: True")


if __name__ == "__main__":
    create_admin()