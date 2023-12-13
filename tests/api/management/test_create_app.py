from secma_core.server.constants import MANAGEMENT_APP


def test_create_app_unauthenticated(client):
    response = client.put("/mng/apps/")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.headers["Content-Type"] == "application/json"


def test_create_app_slug_exists(client, token_factory):
    response = client.put(
        "/mng/apps/",
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=["app:c"])
        },
        json={
            "slug": MANAGEMENT_APP,
            "title": "title",
            "description": "description",
        },
    )
    assert response.status_code == 409
    reply = response.json()
    assert reply == {
        "message": (
            f"An application with a `{MANAGEMENT_APP}` slug already exists."
        ),
        "code": "duplicate-app",
        "field": "slug",
        "params": {"appSlug": MANAGEMENT_APP},
    }


def test_create_app_ok(client, token_factory):
    response = client.put(
        "/mng/apps/",
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=["app:c"])
        },
        json={
            "slug": "string",
            "title": "title",
            "description": "description",
        },
    )
    assert response.status_code == 200
    reply = response.json()
    assert reply["slug"] == "string"
    assert reply["title"] == "title"
    assert reply["description"] == "description"
    assert reply["created"]
    assert reply["updated"]
