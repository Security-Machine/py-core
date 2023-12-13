from secma_core.server.constants import MANAGEMENT_APP


def test_get_apps_unauthenticated(client):
    response = client.get("/mng/apps/")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.headers["Content-Type"] == "application/json"


def test_get_apps_ok(client, token_factory):
    response = client.get(
        "/mng/apps/",
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=["apps:r"])
        },
    )
    assert response.status_code == 200
    reply = response.json()
    assert reply == [MANAGEMENT_APP]
