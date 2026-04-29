from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.book import Book
from app.models.reader import Reader
from app.models.borrowed import BorrowedBook
from app.schemas import BorrowCreate, BorrowResponse
from app.auth import get_current_user
from app.models.user import User
from typing import List

router = APIRouter(prefix="/borrow", tags=["borrow"])


@router.post("/", response_model=BorrowResponse, status_code=201)
def borrow_book(
    borrow_data: BorrowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == borrow_data.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    reader = db.query(Reader).filter(Reader.id == borrow_data.reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="Читатель не найден")

    if book.copies < 1:
        raise HTTPException(status_code=400, detail="Нет доступных экземпляров книги")

    active_borrows = db.query(BorrowedBook).filter(
        BorrowedBook.reader_id == borrow_data.reader_id,
        BorrowedBook.return_date == None  # noqa: E711
    ).count()
    if active_borrows >= 3:
        raise HTTPException(status_code=400, detail="Читатель уже взял максимальное количество книг (3)")

    book.copies -= 1

    borrow = BorrowedBook(
        book_id=borrow_data.book_id,
        reader_id=borrow_data.reader_id
    )
    db.add(borrow)
    db.commit()
    db.refresh(borrow)
    return borrow


@router.post("/return", response_model=BorrowResponse)
def return_book(
    borrow_data: BorrowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    borrow = db.query(BorrowedBook).filter(
        BorrowedBook.book_id == borrow_data.book_id,
        BorrowedBook.reader_id == borrow_data.reader_id,
        BorrowedBook.return_date == None  # noqa: E711
    ).first()

    if not borrow:
        raise HTTPException(
            status_code=400,
            detail="Эта книга не была выдана этому читателю или уже возвращена"
        )

    book = db.query(Book).filter(Book.id == borrow_data.book_id).first()
    book.copies += 1

    from datetime import datetime
    borrow.return_date = datetime.utcnow()

    db.commit()
    db.refresh(borrow)
    return borrow


@router.get("/reader/{reader_id}", response_model=List[BorrowResponse])
def get_active_borrows(
    reader_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Список всех книг которые читатель взял и ещё не вернул"""
    reader = db.query(Reader).filter(Reader.id == reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="Читатель не найден")

    borrows = db.query(BorrowedBook).filter(
        BorrowedBook.reader_id == reader_id,
        BorrowedBook.return_date == None  # noqa: E711
    ).all()
    return borrows


@router.get("/history/", dependencies=[Depends(get_current_user)])
def get_history(db: Session = Depends(get_db)):
    """Полная история всех выдач"""
    borrows = db.query(BorrowedBook).all()

    result = []
    for b in borrows:
        book = db.query(Book).filter(Book.id == b.book_id).first()
        reader = db.query(Reader).filter(Reader.id == b.reader_id).first()
        result.append({
            "id": b.id,
            "book_title": book.title if book else "—",
            "reader_name": reader.name if reader else "—",
            "borrow_date": b.borrow_date,
            "return_date": b.return_date
        })

    return result