def common_asserts(response):
    reply = response.json()
    assert reply["field"] is None
    assert reply["params"]["uniqueId"] is not None
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers["WWW-Authenticate"] == 'Bearer scope="version:r"'


def test_get_version_unauthenticated(client):
    response = client.get("/mng/version")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.headers["Content-Type"] == "application/json"


def test_get_version_authenticated_no_perm(client, token_factory):
    response = client.get(
        "/mng/version",
        headers={
            "Authorization": "bearer " + token_factory(client.super_user)
        },
    )
    assert response.status_code == 401
    reply = response.json()
    assert reply["code"] == "no-permission"
    assert "Not enough permissions (trace ID: " in reply["message"]
    common_asserts(response)


def test_get_version_authenticated_no_user(client, token_factory):
    response = client.get(
        "/mng/version",
        headers={"Authorization": "bearer " + token_factory("")},
    )
    assert response.status_code == 401
    reply = response.json()
    assert reply["code"] == "invalid-credentials"
    assert "Could not validate credentials (trace ID: " in reply["message"]
    common_asserts(response)


def test_get_version_wrong_perm(client, token_factory):
    response = client.get(
        "/mng/version",
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=["app:r"])
        },
    )
    assert response.status_code == 401
    reply = response.json()
    assert reply["code"] == "no-permission"
    assert "Not enough permissions (trace ID: " in reply["message"]
    common_asserts(response)


def test_get_version_ok(client, token_factory):
    from secma_core.__version__ import __version__

    response = client.get(
        "/mng/version",
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=["version:r"])
        },
    )
    assert response.status_code == 200
    reply = response.json()
    assert reply == {
        "api": __version__,
        "fastapi": "0.104.1",
        "pydantic": "2.5.2",
    }
