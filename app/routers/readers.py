from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.reader import Reader
from app.schemas import ReaderCreate, ReaderResponse
from typing import List

router = APIRouter(prefix="/readers", tags=["readers"])


@router.get("/", response_model=List[ReaderResponse])
def get_readers(db: Session = Depends(get_db)):
    return db.query(Reader).all()


@router.get("/{reader_id}", response_model=ReaderResponse)
def get_reader(reader_id: int, db: Session = Depends(get_db)):
    reader = db.query(Reader).filter(Reader.id == reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="Читатель не найден")
    return reader


@router.post("/", response_model=ReaderResponse, status_code=201)
def create_reader(reader_data: ReaderCreate, db: Session = Depends(get_db)):
    existing = db.query(Reader).filter(Reader.email == reader_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Читатель с таким email уже существует")
    
    reader = Reader(**reader_data.model_dump())
    db.add(reader)
    db.commit()
    db.refresh(reader)
    return reader


@router.put("/{reader_id}", response_model=ReaderResponse)
def update_reader(reader_id: int, reader_data: ReaderCreate, db: Session = Depends(get_db)):
    reader = db.query(Reader).filter(Reader.id == reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="Читатель не найден")
    
    for key, value in reader_data.model_dump().items():
        setattr(reader, key, value)
    
    db.commit()
    db.refresh(reader)
    return reader


@router.delete("/{reader_id}", status_code=204)
def delete_reader(reader_id: int, db: Session = Depends(get_db)):
    reader = db.query(Reader).filter(Reader.id == reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="Читатель не найден")
    
    db.delete(reader)
    db.commit()