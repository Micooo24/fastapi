from pydantic import BaseModel
from datetime import date

class User(BaseModel):
    username: str
    email: str
    password: str
    birthday: date = None
    img_path: str = None
    disabled: bool = None