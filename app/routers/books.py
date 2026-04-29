from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.book import Book
from app.schemas import BookCreate, BookResponse, BorrowResponse
from app.auth import get_current_user
from app.models.user import User
from typing import List

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=List[BookResponse])
def get_books(search: str = "", db: Session = Depends(get_db)):
    if search:
        return db.query(Book).filter(
            Book.title.ilike(f"%{search}%") | Book.author.ilike(f"%{search}%")
        ).all()
    return db.query(Book).all()


# ВАЖНО: /search/ и другие статические пути — ДО /{book_id}
@router.get("/search/", response_model=List[BookResponse])
def search_books(q: str, db: Session = Depends(get_db)):
    """Поиск книг по названию или автору"""
    return db.query(Book).filter(
        Book.title.ilike(f"%{q}%") | Book.author.ilike(f"%{q}%")
    ).all()


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book


@router.get("/{book_id}/history", response_model=List[BorrowResponse])
def get_book_history(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """История всех выдач конкретной книги"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    from app.models.borrowed import BorrowedBook
    return db.query(BorrowedBook).filter(BorrowedBook.book_id == book_id).all()


@router.post("/", response_model=BookResponse, status_code=201)
def create_book(
    book_data: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if book_data.isbn:
        existing = db.query(Book).filter(Book.isbn == book_data.isbn).first()
        if existing:
            raise HTTPException(status_code=400, detail="Книга с таким ISBN уже существует")

    book = Book(**book_data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@router.put("/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book_data: BookCreate, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    for key, value in book_data.model_dump().items():
        setattr(book, key, value)

    db.commit()
    db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    db.delete(book)
    db.commit()