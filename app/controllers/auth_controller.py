from app.services.auth_service import AuthService
from app.exceptions.base_exception import AppException


class AuthController:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def _handle_response(self, action):
        try:
            result = action()
            return {"status": "success", **result}
        except AppException as e:
            return {"status": "error", "code": e.status_code, "message": e.message}
        except ValueError as e:
            return {"status": "error", "code": 400, "message": str(e)}
        except Exception:
            return {"status": "error", "code": 500, "message": "Internal server error"}

    def register_user(self, email: str, password: str, name: str, address: str = None):
        try:
            user = self.auth_service.register_user(email, password, name, address)
            return {"status": "success", "user_id": user.id}
        except AppException as e:
            return {"status": "error", "code": e.status_code, "message": e.message}
        except ValueError as e:
            return {"status": "error", "code": 400, "message": str(e)}
        except Exception:
            return {"status": "error", "code": 500, "message": "Internal server error"}

    def authenticate_user(self, email: str, password: str):
        try:
            user, token = self.auth_service.authenticate_user(email, password)
            return {"status": "success", "user_id": user.id, "token": token}
        except AppException as e:
            return {"status": "error", "code": e.status_code, "message": e.message}
        except ValueError as e:
            return {"status": "error", "code": 400, "message": str(e)}
        except Exception:
            return {"status": "error", "code": 500, "message": "Internal server error"}

    def verify_email(self, email: str, code: str):
        try:
            user_id = self.auth_service.verify_email(email, code)
            return {"status": "success", "user_id": user_id}
        except AppException as e:
            return {"status": "error", "code": e.status_code, "message": e.message}
        except Exception:
            return {"status": "error", "code": 500, "message": "Internal server error"}

    def resend_verification(self, email: str):
        try:
            user_id = self.auth_service.resend_verification(email)
            return {"status": "success", "message": "If the email exists and is not yet verified, a new verification code has been sent."}
        except AppException as e:
            return {"status": "error", "code": e.status_code, "message": e.message}
        except Exception:
            return {"status": "error", "code": 500, "message": "Internal server error"}

    def validate_token(self, token: str):
        try:
            user_id = self.auth_service.validate_token(token)
            return {"status": "success", "user_id": user_id}
        except AppException as e:
            return {"status": "error", "code": e.status_code, "message": e.message}
        except Exception:
            return {"status": "error", "code": 500, "message": "Internal server error"}

    def update_user_profile(self, user_id: int, email: str = None, password: str = None,
                            name: str = None, address: str = None):
        return self._handle_response(lambda: {
            "user_id": self.auth_service.update_user_profile(
                user_id, email=email, password=password, name=name, address=address
            ).id
        })

    def delete_user(self, user_id: int):
        return self._handle_response(lambda: {
            "deleted": self.auth_service.delete_user(user_id)
        })

    def update_user_role(self, target_user_id: int, new_role: str, admin_user_id: int):
        try:
            user = self.auth_service.update_user_role(target_user_id, new_role, admin_user_id)
            return {"status": "success", "user_id": user.id, "role": user.role}
        except AppException as e:
            return {"status": "error", "code": e.status_code, "message": e.message}
        except Exception:
            return {"status": "error", "code": 500, "message": "Internal server error"}