from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.book import Book
from app.models.reader import Reader
from app.models.borrowed import BorrowedBook
from app.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/", dependencies=[Depends(get_current_user)])
def get_stats(db: Session = Depends(get_db)):
    """Общая статистика библиотеки"""
    total_books = db.query(Book).count()
    total_readers = db.query(Reader).count()
    active_borrows = db.query(BorrowedBook).filter(
        BorrowedBook.return_date == None  # noqa: E711
    ).count()
    total_copies = db.query(Book).with_entities(
        Book.copies
    ).all()
    available_copies = sum(c[0] for c in total_copies)

    return {
        "total_books": total_books,
        "total_readers": total_readers,
        "active_borrows": active_borrows,
        "available_copies": available_copies
    }