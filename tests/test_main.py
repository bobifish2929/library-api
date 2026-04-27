import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Отдельная тестовая БД чтобы не трогать рабочую
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_library.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Подменяем рабочую БД тестовой
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Создаём таблицы перед каждым тестом и удаляем после"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def get_auth_token():
    """Вспомогательная функция — регистрируем и логинимся"""
    client.post("/auth/register", json={
        "email": "test@test.com",
        "password": "123456"
    })
    response = client.post("/auth/login", data={
        "username": "test@test.com",
        "password": "123456"
    })
    return response.json()["access_token"]


def auth_headers():
    """Возвращаем заголовок с токеном"""
    token = get_auth_token()
    return {"Authorization": f"Bearer {token}"}


# ===== ТЕСТЫ АУТЕНТИФИКАЦИИ =====

def test_protected_endpoint_without_token():
    """Защищённый эндпоинт без токена должен вернуть 401"""
    response = client.get("/borrow/reader/1")
    assert response.status_code == 401


def test_protected_endpoint_with_token():
    """Защищённый эндпоинт с токеном должен работать"""
    # Сначала создаём читателя
    client.post("/readers/", json={
        "name": "Иван",
        "email": "ivan@test.com"
    }, headers=auth_headers())

    response = client.get("/borrow/reader/1", headers=auth_headers())
    assert response.status_code == 200


# ===== ТЕСТЫ БИЗНЕС-ЛОГИКИ =====

def test_borrow_book_no_copies():
    """Нельзя взять книгу если нет экземпляров"""
    headers = auth_headers()

    # Создаём книгу с 0 экземпляров
    client.post("/books/", json={
        "title": "Тестовая книга",
        "author": "Автор",
        "copies": 0
    }, headers=headers)

    # Создаём читателя
    client.post("/readers/", json={
        "name": "Иван",
        "email": "ivan@test.com"
    }, headers=headers)

    # Пытаемся взять книгу
    response = client.post("/borrow/", json={
        "book_id": 1,
        "reader_id": 1
    }, headers=headers)

    assert response.status_code == 400
    assert "доступных экземпляров" in response.json()["detail"]


def test_borrow_more_than_3_books():
    """Читатель не может взять более 3 книг"""
    headers = auth_headers()

    # Создаём 4 книги
    for i in range(4):
        client.post("/books/", json={
            "title": f"Книга {i+1}",
            "author": "Автор",
            "copies": 5
        }, headers=headers)

    # Создаём читателя
    client.post("/readers/", json={
        "name": "Иван",
        "email": "ivan@test.com"
    }, headers=headers)

    # Берём 3 книги успешно
    for book_id in range(1, 4):
        client.post("/borrow/", json={
            "book_id": book_id,
            "reader_id": 1
        }, headers=headers)

    # Пытаемся взять 4-ю
    response = client.post("/borrow/", json={
        "book_id": 4,
        "reader_id": 1
    }, headers=headers)

    assert response.status_code == 400
    assert "максимальное количество" in response.json()["detail"]


def test_return_book_not_borrowed():
    """Нельзя вернуть книгу которую не брали"""
    headers = auth_headers()

    client.post("/books/", json={
        "title": "Тестовая книга",
        "author": "Автор",
        "copies": 3
    }, headers=headers)

    client.post("/readers/", json={
        "name": "Иван",
        "email": "ivan@test.com"
    }, headers=headers)

    # Пытаемся вернуть книгу которую не брали
    response = client.post("/borrow/return", json={
        "book_id": 1,
        "reader_id": 1
    }, headers=headers)

    assert response.status_code == 400
    assert "не была выдана" in response.json()["detail"]