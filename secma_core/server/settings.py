"""Server settings."""
import os
from typing import Any, Callable, List, cast

from db4me import AllDatabaseSettings
from log2me import LogSettings
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import SettingsConfigDict
from pydantic_settings_yaml import YamlBaseSettings


class YamlSettingsConfigDict(SettingsConfigDict):
    yaml_file: str


# TODO: YamlBaseSettings changed by hand because the order is wrong.
# Needs to be forked.


class ManagementSettings(BaseModel):
    token_secret: SecretStr = Field(
        ...,
        description="The secret used to sign the JWT tokens.",
    )
    token_algorithm: str = Field(
        "HS256",
        description="The algorithm used to sign the JWT tokens.",
    )
    token_expiration: float = Field(
        30,
        description="The expiration time of the JWT tokens in minutes.",
    )

    super_role: str = Field(
        "super",
        description=(
            "The name of the super role that will get "
            "all known permissions."
        ),
    )
    super_user: str = Field(
        "super-user",
        description=(
            "The name of user that will always exist in the management app "
            "and will have all permissions."
        ),
    )
    super_password: SecretStr = Field(
        ...,
        description=("The password of the super-user."),
    )


class NetworkSettings(BaseModel):
    cors_origins: List[str] = Field(
        ["*"],
        description="The origins allowed to make CORS requests.",
    )
    cors_allow_credentials: bool = Field(
        True,
        description="Whether to allow credentials in CORS requests.",
    )
    cors_allow_methods: List[str] = Field(
        ["*"],
        description="The methods allowed in CORS requests.",
    )
    cors_allow_headers: List[str] = Field(
        ["*"],
        description="The headers allowed in CORS requests.",
    )


class Settings(YamlBaseSettings):
    """Server settings read from config file and from environment."""

    model_config = YamlSettingsConfigDict(
        env_prefix="SECURITY_MACHINE_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        secrets_dir=os.environ.get(
            "SECURITY_MACHINE_SECRETS_LOCATION", "/run/secrets"
        ),
        yaml_file=os.environ.get("SECURITY_MACHINE_CONFIG", "config.yaml"),
    )

    log: LogSettings = Field(
        default_factory=cast(Callable[[], Any], LogSettings),
        description="Logging settings.",
    )

    database: AllDatabaseSettings = Field(
        default_factory=cast(Callable[[], Any], AllDatabaseSettings),
        description="Database settings.",
    )

    management: ManagementSettings = Field(
        default_factory=cast(Callable[[], Any], ManagementSettings),
        description="Management settings.",
    )

    net: NetworkSettings = Field(
        default_factory=cast(Callable[[], Any], NetworkSettings),
        description="CORS settings.",
    )
