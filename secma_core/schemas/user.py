from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from secma_core.server.utils import user_name_is_valid


class Common(BaseModel):
    """Common fields for input an output."""

    name: str = Field(
        ...,
        description="The unique name of this user.",
    )

    suspended: bool = Field(
        default=False,
        description="Whether this user is suspended and cannot log in.",
    )

    description: Optional[str] = Field(
        default="",
        description="A description of the user.",
    )


class UserData(Common):
    """The data provided about a user by the core."""

    model_config = ConfigDict(from_attributes=True)

    created: datetime = Field(
        ...,
        description="The moment when this record was created.",
    )

    updated: datetime = Field(
        ...,
        description="The last time when this record was updated.",
    )


class UserInput(Common):
    """The data for creating or editing a user."""

    @field_validator("name")
    def username_is_valid(cls, v):
        """Validate the slug."""
        return user_name_is_valid(v)
