from pydantic import BaseModel

#request res format
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    age:int

class LoginRequest(BaseModel):
    email: str
    password: str
