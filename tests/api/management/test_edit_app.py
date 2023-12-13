import pytest
from datetime import datetime


def test_edit_app_unauthenticated(client):
    response = client.post("/mng/apps/123")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.headers["Content-Type"] == "application/json"


def test_edit_app_non_existing(client, token_factory):
    response = client.post(
        "/mng/apps/123",
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=["app:u"])
        },
        json={
            "slug": "an-app",
            "title": "A new title",
            "description": "A new description",
        },
    )
    reply = response.json()
    assert response.status_code == 404
    assert reply == {
        "message": "No application with a `123` slug was found.",
        "code": "no-app",
        "field": None,
        "params": {"appSlug": "123"},
    }


@pytest.mark.asyncio
async def test_edit_app_ok(client, token_factory, new_app_factory):
    the_app = await (await new_app_factory)("an-app")
    response = client.post(
        "/mng/apps/an-app",
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=["app:u"])
        },
        json={
            "slug": "another-app",
            "title": "A new title",
            "description": "A new description",
        },
    )
    assert response.status_code == 200
    reply = response.json()
    assert reply["slug"] == "another-app"
    assert reply["title"] == "A new title"
    assert reply["description"] == "A new description"
    assert datetime.fromisoformat(reply["created"]) == the_app.created
    assert datetime.fromisoformat(reply["updated"]) == the_app.updated
