"""
Sistema de Autenticação JWT para ConcursAI
Implementa autenticação segura com JWT tokens
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
import hashlib
import secrets

from app.config import get_settings

# Configurações
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Models
class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

class TokenData(BaseModel):
    username: Optional[str] = None

# Simulação de banco de dados de usuários (substituir por SQLAlchemy)
fake_users_db = {
    "admin": {
        "id": 1,
        "username": "admin",
        "email": "admin@concursai.com",
        "hashed_password": pwd_context.hash("admin123"),
        "is_active": True,
        "is_admin": True,
        "created_at": datetime.now(),
        "last_login": None
    },
    "user": {
        "id": 2,
        "username": "user",
        "email": "user@concursai.com", 
        "hashed_password": pwd_context.hash("user123"),
        "is_active": True,
        "is_admin": False,
        "created_at": datetime.now(),
        "last_login": None
    }
}

class AuthManager:
    """Gerenciador de autenticação"""
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Gera hash da senha"""
        return self.pwd_context.hash(password)
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Busca usuário por username"""
        return fake_users_db.get(username)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Autentica usuário"""
        user = self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user["hashed_password"]):
            return None
        
        # Atualizar último login
        user["last_login"] = datetime.now()
        return user
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Cria token JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verifica e decodifica token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return TokenData(username=username)
        except JWTError:
            return None
    
    def create_user(self, user_data: UserCreate) -> User:
        """Cria novo usuário"""
        if user_data.username in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        hashed_password = self.get_password_hash(user_data.password)
        user_id = max([u["id"] for u in fake_users_db.values()]) + 1
        
        new_user = {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_admin": False,
            "created_at": datetime.now(),
            "last_login": None
        }
        
        fake_users_db[user_data.username] = new_user
        
        return User(
            id=new_user["id"],
            username=new_user["username"],
            email=new_user["email"],
            is_active=new_user["is_active"],
            is_admin=new_user["is_admin"],
            created_at=new_user["created_at"],
            last_login=new_user["last_login"]
        )

# Instância global do gerenciador
auth_manager = AuthManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency para obter usuário atual"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = auth_manager.verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    user = auth_manager.get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return User(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        is_active=user["is_active"],
        is_admin=user["is_admin"],
        created_at=user["created_at"],
        last_login=user["last_login"]
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency para usuário ativo"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency para usuário admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def generate_api_key() -> str:
    """Gera uma API key única"""
    return "ck_" + secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """Gera hash da API key para armazenamento"""
    return hashlib.sha256(api_key.encode()).hexdigest()

async def verify_api_key(api_key: str) -> bool:
    """Verifica API key (implementar conforme necessário)"""
    # TODO: Implementar verificação real de API keys
    return api_key.startswith("ck_") and len(api_key) > 20
