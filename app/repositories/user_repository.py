from app.models.user import User

class UserRepository:
    def __init__(self, session):
        self.session = session

    def get_user_by_id(self, user_id):
        user = self.session.query(User).filter(User.id == user_id).first()
        return user

    def get_user_by_email(self, email):
        user = self.session.query(User).filter(User.email == email).first()
        return user

    def create_user(self, email, password, name, address=None):
        new_user = User(email=email, password=password, name=name, address=address)
        self.session.add(new_user)
        self.session.flush()
        return new_user
    
    def update_user(self, user_id, email=None, password=None, name=None, address=None, is_verified=None, role=None):
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        if email is not None:
            user.email = email
        if password is not None:
            user.password = password
        if name is not None:
            user.name = name
        if address is not None:
            user.address = address
        if is_verified is not None:
            user.is_verified = is_verified
        if role is not None:
            user.role = role
        
        self.session.add(user)
        return user

    def get_admin_users(self):
        """Retorna todos os usuários com role 'admin'."""
        return self.session.query(User).filter(User.role == 'admin').all()
    
    def delete_user(self, user_id):
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        self.session.delete(user)
        self.session.flush()
        return True