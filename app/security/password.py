from argon2 import PasswordHasher, exceptions


class PasswordService:
    """Encapsula toda responsabilidade de hash e verificação de senhas."""

    def __init__(self):
        self._ph = PasswordHasher()

    def hash(self, password: str) -> str:
        """Gera o hash argon2 de uma senha."""
        return self._ph.hash(password)

    def verify(self, hashed: str, password: str) -> bool:
        """Verifica se a senha corresponde ao hash. Retorna True/False sem exceções."""
        try:
            return self._ph.verify(hashed, password)
        except exceptions.VerifyMismatchError:
            return False
        except Exception:
            return False

    def needs_rehash(self, hashed: str) -> bool:
        """Verifica se o hash precisa ser atualizado (mudança de parâmetros)."""
        return self._ph.check_needs_rehash(hashed)
