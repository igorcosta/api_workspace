import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from main import app
from database import Base, get_db
from models import Profile

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_retrieve_user_profile():
    # Assuming there's a user with id 1 and a profile in the test database
    response = client.get("/users/1/profile")
    assert response.status_code == 200
    assert "bio" in response.json()

def test_update_user_profile():
    # Assuming there's a user with id 1 and a profile in the test database
    response = client.put("/users/1/profile", json={"bio": "Updated bio"})
    assert response.status_code == 200
    assert response.json()["bio"] == "Updated bio"

def test_retrieve_user_profile_not_found():
    response = client.get("/users/999/profile")
    assert response.status_code == 404

def test_update_user_profile_not_found():
    response = client.put("/users/999/profile", json={"bio": "This should not work"})
    assert response.status_code == 404

def test_unauthorized_access():
    # Assuming endpoint requires authorization
    response = client.get("/users/1/profile")
    assert response.status_code == 403
