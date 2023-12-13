def test_get_stats_unauthenticated(client):
    response = client.get("/mng/stats")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.headers["Content-Type"] == "application/json"


def test_get_stats_ok(client, token_factory):
    response = client.get(
        "/mng/stats",
        headers={
            "Authorization": "bearer "
            + token_factory(client.super_user, permissions=["stats:r"])
        },
    )
    assert response.status_code == 200
    reply = response.json()
    assert reply == {
        "apps": 1,
        "apps_no_tenants": 0,
        "tenants": 1,
        "tenants_no_users": 0,
        "tenants_no_roles": 0,
        "tenants_no_perms": 0,
        "users": 1,
        "users_no_roles": 0,
        "roles": 1,
        "roles_no_perms": 0,
        "perms": 27,
    }
