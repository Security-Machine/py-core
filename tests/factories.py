from factory import Factory, Faker, Sequence

from secma_core.db.models.application import Application as ApplicationModel
from secma_core.db.models.tenant import Tenant as TenantModel
from secma_core.db.models.user import User as UserModel
from secma_core.db.models.role import Role as RoleModel
from secma_core.db.models.permission import Permission as PermissionModel


class Application(Factory):
    class Meta:
        model = ApplicationModel

    slug = Sequence(lambda n: f"app-{n}")
    title = Faker("sentence")
    description = Faker("paragraph")


class Tenant(Factory):
    class Meta:
        model = TenantModel

    slug = Sequence(lambda n: f"tnt-{n}")
    title = Faker("sentence")
    description = Faker("paragraph")


class User(Factory):
    class Meta:
        model = UserModel

    name = Sequence(lambda n: f"user-{n}")
    suspended = False
    description = Faker("paragraph")


class Role(Factory):
    class Meta:
        model = RoleModel

    name = Sequence(lambda n: f"user-{n}")
    description = Faker("paragraph")


class Permission(Factory):
    class Meta:
        model = PermissionModel

    name = Sequence(lambda n: f"user-{n}")
    description = Faker("paragraph")
