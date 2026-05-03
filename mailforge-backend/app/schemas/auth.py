from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefresh(BaseModel):
    refresh_token: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    model_config = {"from_attributes": True}
