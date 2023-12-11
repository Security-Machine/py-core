"""Server settings."""
import os
from typing import List, Optional

from db4me import AllDatabaseSettings
from log4me import LogSettings
from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict
from pydantic_settings_yaml import YamlBaseSettings


class YamlSettingsConfigDict(SettingsConfigDict):
    yaml_file: str


# TODO: YamlBaseSettings changed by hand because the order is wrong.
# Needs to be forked.


class ManagementSettings(BaseModel):
    token_secret: str = Field(
        ...,
        description="The secret used to sign the JWT tokens.",
    )
    token_algorithm: Optional[str] = Field(
        "HS256",
        description="The algorithm used to sign the JWT tokens.",
    )
    token_expiration: Optional[int] = Field(
        30,
        description="The expiration time of the JWT tokens in minutes.",
    )

    super_role: Optional[str] = Field(
        "super",
        description=(
            "The name of the super role that will get "
            "all known permissions."
        ),
    )
    super_user: Optional[str] = Field(
        "super-user",
        description=(
            "The name of user that will always exist in the management app "
            "and will have all permissions."
        ),
    )
    super_password: str = Field(
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
        default_factory=LogSettings, description="Logging settings."
    )

    database: AllDatabaseSettings = Field(
        description="Database settings.",
    )

    management: ManagementSettings = Field(
        default_factory=ManagementSettings,
        description="Management settings.",
    )

    net: NetworkSettings = Field(
        default_factory=NetworkSettings,
        description="CORS settings.",
    )
