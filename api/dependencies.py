from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.unit_of_work import UnitOfWork
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.controllers.auth_controller import AuthController
from app.controllers.product_controller import ProductController
from app.controllers.order_controller import OrderController
from app.security.jwt import JwtService
from app.exceptions.auth_exception import InvalidCredentialsError

security_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


def get_uow() -> UnitOfWork:
    return UnitOfWork()


def get_email_service() -> EmailService:
    return EmailService()


def get_auth_controller() -> AuthController:
    uow = UnitOfWork()
    email_service = get_email_service()
    auth_service = AuthService(uow, email_service=email_service)
    return AuthController(auth_service)


def get_product_controller(uow: UnitOfWork = Depends(get_uow)) -> ProductController:
    return ProductController(uow)


def get_order_controller(uow: UnitOfWork = Depends(get_uow)) -> OrderController:
    return OrderController(uow)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> int:
    """Valida o token JWT (assinatura + banco de dados).
    Retorna o user_id se válido. Levanta HTTPException 401 se ausente ou inválido."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = JwtService().validate_token(token)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: 'sub' must be an integer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with UnitOfWork() as uow:
        db_token = uow.tokens.find_valid_token(token)
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user_id


def get_current_admin_user_id(
    user_id: int = Depends(get_current_user_id),
) -> int:
    """Verifica se o usuário autenticado é admin.
    Retorna o user_id se for admin. Levanta HTTPException 403 se não for admin."""
    with UnitOfWork() as uow:
        user = uow.users.get_user_by_id(user_id)
        if not user or user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
    return user_id
