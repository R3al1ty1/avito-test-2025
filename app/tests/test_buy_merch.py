import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_buy_merch():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        auth_response = await client.post("/api/auth", json={"username": "testuser", "password": "testpass"})
        assert auth_response.status_code == 200, auth_response.text
        token = auth_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        info_response = await client.get("/api/info", headers=headers)
        assert info_response.status_code == 200, info_response.text
        initial_balance = info_response.json()["coin_balance"]

        buy_response = await client.get("/api/buy/socks", headers=headers)
        assert buy_response.status_code == 200, buy_response.text
        assert "Товар 'socks' успешно куплен" in buy_response.json()["detail"]

        updated_info = await client.get("/api/info", headers=headers)
        assert updated_info.status_code == 200, updated_info.text
        updated_balance = updated_info.json()["coin_balance"]
        inventory = updated_info.json()["inventory"]

        assert updated_balance < initial_balance

        item_names = [item["type"] for item in inventory]
        assert "TestMerch" in item_names
