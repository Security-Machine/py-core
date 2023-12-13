import pytest
from datetime import datetime


def test_delete_app_unauthenticated(client):
    response = client.delete("/mng/apps/123")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.headers["Content-Type"] == "application/json"


def test_delete_app_non_existing(client, token_factory):
    response = client.delete(
        "/mng/apps/123",
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=["app:d"])
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_app_ok(client, token_factory, new_app_factory):
    the_app = await (await new_app_factory)("an-app")
    response = client.delete(
        "/mng/apps/an-app",
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=["app:d"])
        },
    )
    assert response.status_code == 200
    reply = response.json()
    assert reply["slug"] == "an-app"
    assert reply["title"] == the_app.title
    assert reply["description"] == the_app.description
    assert datetime.fromisoformat(reply["created"]) == the_app.created
    assert datetime.fromisoformat(reply["updated"]) == the_app.updated
