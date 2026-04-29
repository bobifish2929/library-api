from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app import models  # noqa: F401
from app.routers import books, readers, auth, borrow, stats

app = FastAPI(title="Library API")

# Разрешаем запросы с любого адреса (для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(readers.router)
app.include_router(borrow.router)
app.include_router(stats.router)

@app.get("/")
def root():
    return {"message": "Добро пожаловать в Library API!"}