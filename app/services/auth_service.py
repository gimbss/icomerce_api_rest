import random
import string
from datetime import datetime, timedelta, timezone

from app.database.unit_of_work import UnitOfWork
from app.security import PasswordService, JwtService
from app.services.email_service import EmailService
from app.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UserNotFoundError,
    EmailNotVerifiedError,
    InvalidVerificationCodeError,
    CannotDemoteLastAdminError,
)


class AuthService:
    VERIFICATION_CODE_LENGTH = 6
    VERIFICATION_CODE_EXPIRY_MINUTES = 15

    def __init__(self, uow: UnitOfWork, email_service: EmailService | None = None):
        self.uow = uow
        self.password_service = PasswordService()
        self.jwt_service = JwtService()
        self.email_service = email_service or EmailService()

    @staticmethod
    def _generate_verification_code(length: int = 6) -> str:
        """Gera um código alfanumérico de 6 caracteres."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=length))

    def register_user(self, email: str, password: str, name: str, address: str = None):
        with self.uow as uow:
            existing_user = uow.users.get_user_by_email(email)
            if existing_user:
                raise EmailAlreadyRegisteredError(email)
            hashed_password = self.password_service.hash(password)
            user = uow.users.create_user(email=email, password=hashed_password, name=name, address=address)

            # Generate email verification code
            code = self._generate_verification_code(self.VERIFICATION_CODE_LENGTH)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.VERIFICATION_CODE_EXPIRY_MINUTES)
            uow.email_verifications.create_verification(user_id=user.id, code=code, expires_at=expires_at)

            # Send verification code via email
            self.email_service.send_verification_code(to_email=user.email, code=code)

            return user

    def authenticate_user(self, email: str, password: str):
        with self.uow as uow:
            user = uow.users.get_user_by_email(email)
            if not user:
                raise InvalidCredentialsError()
            if not user.is_verified:
                raise EmailNotVerifiedError(email)
            if not self.password_service.verify(user.password, password):
                raise InvalidCredentialsError()

            uow.tokens.revoke_all_user_tokens(user.id)

            token, expires_at = self.jwt_service.create_token(user.id)
            uow.tokens.save_token(token, user.id, expires_at)
            return user, token

    def verify_email(self, email: str, code: str) -> int:
        """Verifica o email do usuário usando o código de verificação.
        Retorna o user_id se verificado com sucesso."""
        with self.uow as uow:
            verification = uow.email_verifications.find_valid_code_by_email(email, code)
            if not verification:
                raise InvalidVerificationCodeError()

            # Mark code as used
            uow.email_verifications.mark_as_used(verification.id)

            # Mark user as verified
            user = uow.users.get_user_by_id(verification.user_id)
            if user:
                uow.users.update_user(user.id, email=user.email, password=user.password, name=user.name, address=user.address, is_verified=True)

            return verification.user_id

    def resend_verification(self, email: str) -> int:
        """Reenvia o código de verificação para o email informado.
        Retorna o user_id."""
        with self.uow as uow:
            user = uow.users.get_user_by_email(email)
            if not user:
                # Don't reveal whether the email exists for security
                return 0
            if user.is_verified:
                return user.id

            # Invalidate all previous codes
            uow.email_verifications.invalidate_all_user_codes(user.id)

            # Generate new code
            code = self._generate_verification_code(self.VERIFICATION_CODE_LENGTH)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.VERIFICATION_CODE_EXPIRY_MINUTES)
            uow.email_verifications.create_verification(user_id=user.id, code=code, expires_at=expires_at)

            # Send verification code via email
            self.email_service.send_verification_code(to_email=user.email, code=code)

            return user.id

    def validate_token(self, token_str: str) -> int:
        """Valida um token JWT contra assinatura E banco de dados.
        Retorna user_id se válido, ou levanta InvalidCredentialsError."""
        with self.uow as uow:
            payload = self.jwt_service.validate_token(token_str)
            user_id = int(payload["sub"])
            db_token = uow.tokens.find_valid_token(token_str)
            if not db_token:
                raise InvalidCredentialsError("Invalid or revoked token")
            return user_id

    def update_user_profile(
            self, user_id: int,
            email: str = None,
            password: str = None,
            name: str = None,
            address: str = None):

        with self.uow as uow:
            user = uow.users.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(user_id)

            if email and email != user.email:
                existing_user = uow.users.get_user_by_email(email)
                if existing_user:
                    raise EmailAlreadyRegisteredError(email)

            hashed_password = self.password_service.hash(password) if password else user.password
            email = email if email else user.email
            name = name if name else user.name
            address = address if address else user.address
            updated_user = uow.users.update_user(
                user_id, email=email, password=hashed_password, name=name, address=address
            )
            return updated_user

    def delete_user(self, user_id: int):
        with self.uow as uow:
            deleted = uow.users.delete_user(user_id)
            if not deleted:
                raise UserNotFoundError(user_id)
            return True

    def update_user_role(self, target_user_id: int, new_role: str, admin_user_id: int):
        """Atualiza o role de um usuário. Apenas admins podem alterar roles.
        Impede que o último admin seja rebaixado para evitar lockout.
        
        Args:
            target_user_id: ID do usuário cujo role será alterado
            new_role: Novo role ('admin' ou 'customer')
            admin_user_id: ID do admin que está fazendo a alteração
            
        Returns:
            User: O usuário atualizado
            
        Raises:
            UserNotFoundError: Se o usuário alvo não existir
            CannotDemoteLastAdminError: Se tentar rebaixar o último admin
        """
        with self.uow as uow:
            target_user = uow.users.get_user_by_id(target_user_id)
            if not target_user:
                raise UserNotFoundError(target_user_id)

            # Proteção contra rebaixar o último admin
            if target_user.role == "admin" and new_role == "customer":
                admin_users = uow.users.get_admin_users()
                if len(admin_users) <= 1:
                    raise CannotDemoteLastAdminError()

            updated_user = uow.users.update_user(target_user_id, role=new_role)
            return updated_user
            return True
        

