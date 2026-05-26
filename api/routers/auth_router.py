from fastapi import APIRouter, Depends, HTTPException, status
from api.dependencies import get_auth_controller, get_current_user_id, get_current_admin_user_id
from api.schemas import (
    RegisterUserRequest,
    AuthenticateUserRequest,
    UpdateUserProfileRequest,
    UpdateUserRoleRequest,
    ValidateTokenRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
    VerifyEmailResponse,
    ResendVerificationResponse,
    UpdateUserRoleResponse,
    DeleteResponse,
    ErrorResponse,
)
from app.controllers.auth_controller import AuthController
from app.database.unit_of_work import UnitOfWork
from app.security.jwt import JwtService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def register(body: RegisterUserRequest, ctrl: AuthController = Depends(get_auth_controller)):
    ''' Registrar um novo usuário. Um código de verificação de email é gerado automaticamente. Use /validate para verificar o email antes de fazer login. '''
    result = ctrl.register_user(body.email, body.password, body.name, body.address)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def login(body: AuthenticateUserRequest, ctrl: AuthController = Depends(get_auth_controller)):
    ''' Verificar se as credenciais são válidas e se o email foi verificado, criar um token JWT e retornar o token e o user_id associado. '''
    result = ctrl.authenticate_user(body.email, body.password)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.post(
    "/validate",
    response_model=VerifyEmailResponse,
    responses={400: {"model": ErrorResponse}},
)
def verify_email(body: VerifyEmailRequest, ctrl: AuthController = Depends(get_auth_controller)):
    ''' Verificar o email do usuário usando o código de verificação enviado no registro. Após a verificação, o usuário pode fazer login. '''
    result = ctrl.verify_email(body.email, body.code)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    responses={200: {"model": ResendVerificationResponse}},
)
def resend_verification(body: ResendVerificationRequest, ctrl: AuthController = Depends(get_auth_controller)):
    ''' Reenviar o código de verificação de email. Retorna mensagem genérica por segurança. '''
    result = ctrl.resend_verification(body.email)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.post(
    "/validate-token",
    response_model=UserResponse,
    responses={401: {"model": ErrorResponse}},
)
def validate_token(body: ValidateTokenRequest, ctrl: AuthController = Depends(get_auth_controller)):
    ''' Verificar se o token JWT é válido e retornar o user_id associado. '''
    result = ctrl.validate_token(body.token)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_profile(
    user_id: int,
    body: UpdateUserProfileRequest,
    ctrl: AuthController = Depends(get_auth_controller),
    _token_user_id: int = Depends(get_current_user_id),
):
    ''' Atualiza os dados do usuário autenticado, envie apenas os campos que deseja alterar. Verificar se o usuário autenticado é o mesmo que está sendo atualizado antes de permitir a alteração. '''
    if _token_user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot modify another user")
    result = ctrl.update_user_profile(
        user_id,
        email=body.email,
        password=body.password,
        name=body.name,
        address=body.address,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.delete(
    "/users/{user_id}",
    response_model=DeleteResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def delete_user(
    user_id: int,
    ctrl: AuthController = Depends(get_auth_controller),
    _token_user_id: int = Depends(get_current_user_id),
):
    ''' Verificar se o usuário autenticado é o mesmo que está sendo deletado antes de permitir a exclusão. '''
    if _token_user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete another user")
    result = ctrl.delete_user(user_id)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.post(
    "/logout",
    response_model=DeleteResponse,
    responses={401: {"model": ErrorResponse}},
)
def logout(
    user_id: int = Depends(get_current_user_id),
):
    """Revoga o token atual do usuário autenticado."""
    with UnitOfWork() as uow:
        count = uow.tokens.revoke_all_user_tokens(user_id)
    return {"status": "success", "deleted": count > 0}


@router.patch(
    "/users/{user_id}/role",
    response_model=UpdateUserRoleResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def update_user_role(
    user_id: int,
    body: UpdateUserRoleRequest,
    ctrl: AuthController = Depends(get_auth_controller),
    admin_user_id: int = Depends(get_current_admin_user_id),
):
    """Atualiza o role de um usuário. Apenas admins podem alterar roles. Não é possível rebaixar o último admin."""
    result = ctrl.update_user_role(user_id, body.role, admin_user_id)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result
