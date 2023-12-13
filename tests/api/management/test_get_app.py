from secma_core.server.constants import MANAGEMENT_APP


def test_get_app_unauthenticated(client):
    response = client.get("/mng/apps/" + MANAGEMENT_APP)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.headers["Content-Type"] == "application/json"


def test_get_app_unknown(client, token_factory):
    response = client.get(
        "/mng/apps/123",
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=["app:r"])
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


def test_get_app_no_permission(client, token_factory):
    response = client.get(
        "/mng/apps/" + MANAGEMENT_APP,
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=[])
        },
    )
    reply = response.json()
    assert response.status_code == 401
    assert reply["message"].startswith("Not enough permissions (trace ID: ")
    assert reply["code"] == "no-permission"
    assert reply["field"] is None
    assert reply["params"]["uniqueId"] is not None
    assert len(reply["params"]) == 1
