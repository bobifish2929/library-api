from fastapi import FastAPI
from app.database import engine, Base
from app import models  # noqa: F401
from app.routers import books, readers, auth, borrow

app = FastAPI(title="Library API")

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(readers.router)
app.include_router(borrow.router)

@app.get("/")
def root():
    return {"message": "Добро пожаловать в Library API!"}