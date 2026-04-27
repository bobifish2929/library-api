from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ===== КНИГИ =====

class BookCreate(BaseModel):
    title: str
    author: str
    year: Optional[int] = None
    isbn: Optional[str] = None
    copies: int = 1
    description: Optional[str] = None

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    year: Optional[int] = None
    isbn: Optional[str] = None
    copies: int
    description: Optional[str] = None

    model_config = {"from_attributes": True}


# ===== ЧИТАТЕЛИ =====

class ReaderCreate(BaseModel):
    name: str
    email: EmailStr

class ReaderResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


# ===== ПОЛЬЗОВАТЕЛИ (библиотекари) =====

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str

    model_config = {"from_attributes": True}


# ===== ТОКЕН =====

class Token(BaseModel):
    access_token: str
    token_type: str


# ===== ВЫДАЧА КНИГ =====

class BorrowCreate(BaseModel):
    book_id: int
    reader_id: int

class BorrowResponse(BaseModel):
    id: int
    book_id: int
    reader_id: int
    borrow_date: datetime
    return_date: Optional[datetime] = None

    model_config = {"from_attributes": True}