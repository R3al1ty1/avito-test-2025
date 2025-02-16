import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.models.user import User, UserItem
from core.models.transaction import Transaction
from core.models.merch import MerchItem

from main import app
from core.models.db_helper import db_helper

client = TestClient(app)

@pytest.fixture(scope="function")
async def session():
    async with db_helper.session_factory() as session:
        yield session
        await session.close()

@pytest.fixture(autouse=True)
async def cleanup(session: AsyncSession):
    yield
    await session.rollback()

TEST_USER = {"username": "testuser", "password": "testpass"}
TEST_ITEM = {"name": "sword", "price": 50}

async def test_auth_new_user(session: AsyncSession):
    user = await session.get(User, 1)
    response = client.post("/api/auth", json=TEST_USER)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    
    user = await session.get(User, 1)
    assert user.username == TEST_USER["username"]

async def test_auth_existing_user(session: AsyncSession):
    client.post("/api/auth", json=TEST_USER)
    
    # Проверка входа существующего пользователя
    response = client.post("/api/auth", json=TEST_USER)
    assert response.status_code == status.HTTP_200_OK

def test_auth_validation_errors():
    response = client.post("/api/auth", json={"username": "", "password": ""})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Неверный пароль
    response = client.post("/api/auth", json={"username": TEST_USER["username"], "password": "wrong"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_info_endpoint(session: AsyncSession):
    user = User(**TEST_USER, balance=100)
    session.add(user)
    await session.commit()
    
    item = UserItem(name="shield", user_id=user.id)
    txn = Transaction(sender=2, receiver=user.id, amount=30)
    session.add_all([item, txn])
    await session.commit()
    
    response = client.get("/api/info", headers={"Authorization": "Bearer testtoken"})
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["coin_balance"] == 100
    assert {"type": "shield", "quantity": 1} in data["inventory"]
    assert len(data["transactions_in"]) == 1


async def test_send_coin_success(session: AsyncSession):
    sender = User(**TEST_USER, balance=100)
    receiver = User(username="receiver", password="pass", balance=0)
    session.add_all([sender, receiver])
    await session.commit()
    
    response = client.post(
        "/api/sendCoin",
        json={"to_user": "receiver", "amount": 50},
        headers={"Authorization": "Bearer testtoken"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert (await session.get(User, sender.id)).balance == 50
    assert (await session.get(User, receiver.id)).balance == 50

def test_send_coin_validation_errors():
    # Отправка самому себе
    response = client.post(
        "/api/sendCoin",
        json={"to_user": TEST_USER["username"], "amount": 50},
        headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

async def test_buy_item_success(session: AsyncSession):
    user = User(**TEST_USER, balance=100)
    merch = MerchItem(**TEST_ITEM)
    session.add_all([user, merch])
    await session.commit()
    
    response = client.post(
        f"/api/buy/{TEST_ITEM['name']}",
        headers={"Authorization": "Bearer testtoken"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert (await session.get(User, user.id)).balance == 50
    assert await session.scalar(select(UserItem)) is not None

async def test_buy_item_errors(session: AsyncSession):
    # Недостаточно средств
    user = User(**TEST_USER, balance=10)
    merch = MerchItem(**TEST_ITEM)
    session.add_all([user, merch])
    await session.commit()
    
    response = client.post(
        f"/api/buy/{TEST_ITEM['name']}",
        headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
