from httpx import AsyncClient

CHAT_ID = 42
GITHUB_URL = "https://github.com/octocat/Hello-World"
SO_URL = "https://stackoverflow.com/questions/11227809/why-is-sorted-faster"
INVALID_URL = "https://example.com/not-supported"


async def _register(client: AsyncClient, chat_id: int = CHAT_ID) -> None:
    await client.post(f"/tg-chat/{chat_id}")


async def test_add_github_link(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/links",
        json={"link": GITHUB_URL, "tags": ["python"]},
        headers={"Tg-Chat-Id": str(CHAT_ID)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == GITHUB_URL
    assert "python" in data["tags"]
    assert isinstance(data["id"], int)


async def test_add_stackoverflow_link(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/links",
        json={"link": SO_URL},
        headers={"Tg-Chat-Id": str(CHAT_ID)},
    )
    assert response.status_code == 200
    assert response.json()["url"] == SO_URL


async def test_add_invalid_link_returns_400(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/links",
        json={"link": INVALID_URL},
        headers={"Tg-Chat-Id": str(CHAT_ID)},
    )
    assert response.status_code == 400


async def test_add_link_to_nonexistent_chat_returns_404(client: AsyncClient) -> None:
    response = await client.post(
        "/links",
        json={"link": GITHUB_URL},
        headers={"Tg-Chat-Id": "999"},
    )
    assert response.status_code == 404


async def test_add_duplicate_link_returns_409(client: AsyncClient) -> None:
    await _register(client)
    await client.post(
        "/links", json={"link": GITHUB_URL}, headers={"Tg-Chat-Id": str(CHAT_ID)}
    )
    response = await client.post(
        "/links",
        json={"link": GITHUB_URL},
        headers={"Tg-Chat-Id": str(CHAT_ID)},
    )
    assert response.status_code == 409


async def test_list_links(client: AsyncClient) -> None:
    await _register(client)
    await client.post(
        "/links", json={"link": GITHUB_URL}, headers={"Tg-Chat-Id": str(CHAT_ID)}
    )
    response = await client.get("/links", headers={"Tg-Chat-Id": str(CHAT_ID)})
    assert response.status_code == 200
    data = response.json()
    assert data["size"] == 1
    assert data["links"][0]["url"] == GITHUB_URL


async def test_list_links_empty(client: AsyncClient) -> None:
    await _register(client)
    response = await client.get("/links", headers={"Tg-Chat-Id": str(CHAT_ID)})
    assert response.status_code == 200
    assert response.json()["size"] == 0


async def test_list_links_nonexistent_chat_returns_404(client: AsyncClient) -> None:
    response = await client.get("/links", headers={"Tg-Chat-Id": "999"})
    assert response.status_code == 404


async def test_remove_link(client: AsyncClient) -> None:
    await _register(client)
    await client.post(
        "/links", json={"link": GITHUB_URL}, headers={"Tg-Chat-Id": str(CHAT_ID)}
    )
    response = await client.request(
        "DELETE",
        "/links",
        json={"link": GITHUB_URL},
        headers={"Tg-Chat-Id": str(CHAT_ID)},
    )
    assert response.status_code == 200
    assert response.json()["url"] == GITHUB_URL


async def test_remove_link_then_list_is_empty(client: AsyncClient) -> None:
    await _register(client)
    await client.post(
        "/links", json={"link": GITHUB_URL}, headers={"Tg-Chat-Id": str(CHAT_ID)}
    )
    await client.request(
        "DELETE",
        "/links",
        json={"link": GITHUB_URL},
        headers={"Tg-Chat-Id": str(CHAT_ID)},
    )
    response = await client.get("/links", headers={"Tg-Chat-Id": str(CHAT_ID)})
    assert response.json()["size"] == 0


async def test_remove_nonexistent_link_returns_404(client: AsyncClient) -> None:
    await _register(client)
    response = await client.request(
        "DELETE",
        "/links",
        json={"link": GITHUB_URL},
        headers={"Tg-Chat-Id": str(CHAT_ID)},
    )
    assert response.status_code == 404


async def test_remove_link_nonexistent_chat_returns_404(client: AsyncClient) -> None:
    response = await client.request(
        "DELETE",
        "/links",
        json={"link": GITHUB_URL},
        headers={"Tg-Chat-Id": "999"},
    )
    assert response.status_code == 404
