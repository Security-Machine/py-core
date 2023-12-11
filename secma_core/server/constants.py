from typing import Any

e404: Any = {
    "404": {
        "description": "The requested resource was not found.",
    }
}

e409: Any = {
    "409": {
        "description": (
            "The resource cannot be created or edited due to a conflict "
            "with existing database data."
        ),
    }
}

MANAGEMENT_APP = "management"
MANAGEMENT_TENANT = "sec-ma"

MANAGEMENT_PERMS = {
    "version:r": "Get at the `/version` endpoint.",
    "stats:r": "Get at the `/stats` endpoint.",
    "apps:r": "Get at the `/mng/` endpoint (the list of applications).",
    "app:c": "Put at the `/mng/` endpoint (create a new application).",
    "app:r": "Get at the `/mng/xxx` endpoint (read the properties of an application).",
    "app:u": "Post at the `/mng/xxx` endpoint (update the properties of an application).",
    "app:d": "Delete at the `/mng/xxx` endpoint (remove an application).",

    "tenants:r": "Get at the `/tenants/app/` endpoint (the list of tenants in an application).",
    "tenant:c": "Put at the `/tenants/app/` endpoint (create a new tenant).",
    "tenant:r": "Get at the `/tenants/app/xxx` endpoint (read the properties of a tenant).",
    "tenant:u": "Post at the `/tenants/app/xxx` endpoint (update the properties of a tenant).",
    "tenant:d": "Delete at the `/tenants/app/xxx` endpoint (remove a tenant).",

    "users:r": "Get at the `/users/app/t/` endpoint (the list of users of a tenant in an application).",
    "user:c": "Put at the `/users/app/t/` endpoint (create a new user).",
    "user:r": "Get at the `/users/app/t/xxx` endpoint (read the properties of a user).",
    "user:u": "Post at the `/users/app/t/xxx` endpoint (update the properties of a user).",
    "user:d": "Delete at the `/users/app/t/xxx` endpoint (remove a user).",

    "roles:r": "Get at the `/roles/app/t/` endpoint (the list of roles belonging to a tenant in an application).",
    "role:c": "Put at the `/roles/app/t/` endpoint (create a new role).",
    "role:r": "Get at the `/roles/app/t/xxx` endpoint (read the properties of a role).",
    "role:u": "Post at the `/roles/app/t/xxx` endpoint (update the properties of a role).",
    "role:d": "Delete at the `/roles/app/t/xxx` endpoint (remove a role).",

    "perms:r": "Get at the `/perm/app/t/` endpoint (the list of permissions belonging to a tenant in an application).",
    "perm:c": "Put at the `/perm/app/t/` endpoint (create a new permission).",
    "perm:r": "Get at the `/perm/app/t/xxx` endpoint (read the properties of a permission).",
    "perm:u": "Post at the `/perm/app/t/xxx` endpoint (update the properties of a permission).",
    "perm:d": "Delete at the `/perm/app/t/xxx` endpoint (remove a permission).",

}
