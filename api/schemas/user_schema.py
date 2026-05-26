import re
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


def validate_strong_password(password: str) -> str:
    """Valida se a senha atende aos critérios de força:
    - Mínimo de 8 caracteres
    - Pelo menos uma letra maiúscula
    - Pelo menos uma letra minúscula
    - Pelo menos um dígito
    - Pelo menos um caractere especial
    """
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
    if errors:
        raise ValueError(f"Senha fraca: falta {', '.join(errors)}")
    return password


class RegisterUserRequest(BaseModel):
    email: EmailStr = Field(..., max_length=50, examples=["user@example.com"])
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=120)
    address: str | None = Field(None, max_length=150)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        return validate_strong_password(v)


class AuthenticateUserRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateUserProfileRequest(BaseModel):
    email: EmailStr | None = Field(None, max_length=50)
    password: str | None = Field(None, min_length=8, max_length=128)
    name: str | None = Field(None, min_length=1, max_length=120)
    address: str | None = Field(None, max_length=150)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        if v is not None:
            return validate_strong_password(v)
        return v


class ValidateTokenRequest(BaseModel):
    token: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^[A-Za-z0-9]{6}$")


class ResendVerificationRequest(BaseModel):
    email: EmailStr



class RegisterResponse(BaseModel):
    status: str = "success"
    user_id: int


class TokenResponse(BaseModel):
    status: str = "success"
    user_id: int
    token: str


class UserResponse(BaseModel):
    status: str = "success"
    user_id: int


class VerifyEmailResponse(BaseModel):
    status: str = "success"
    user_id: int


class ResendVerificationResponse(BaseModel):
    status: str = "success"
    message: str


class UpdateUserRoleRequest(BaseModel):
    role: Literal["admin", "customer"] = Field(..., description="Novo role do usuário: 'admin' ou 'customer'")


class UpdateUserRoleResponse(BaseModel):
    status: str = "success"
    user_id: int
    role: str


class DeleteResponse(BaseModel):
    status: str = "success"
    deleted: bool


class ErrorResponse(BaseModel):
    status: str = "error"
    code: int
    message: str
