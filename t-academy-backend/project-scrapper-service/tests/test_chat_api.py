from httpx import AsyncClient


async def test_register_chat(client: AsyncClient) -> None:
    response = await client.post("/tg-chat/1")
    assert response.status_code == 200


async def test_register_same_chat_twice_is_idempotent(client: AsyncClient) -> None:
    await client.post("/tg-chat/1")
    response = await client.post("/tg-chat/1")
    assert response.status_code == 200


async def test_delete_chat(client: AsyncClient) -> None:
    await client.post("/tg-chat/1")
    response = await client.delete("/tg-chat/1")
    assert response.status_code == 200


async def test_delete_nonexistent_chat_returns_404(client: AsyncClient) -> None:
    response = await client.delete("/tg-chat/999")
    assert response.status_code == 404
