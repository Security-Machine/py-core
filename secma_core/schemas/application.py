from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from secma_core.server.utils import SlugField, slug_is_valid


class Common(BaseModel):
    """Common fields for input an output."""

    slug: str = SlugField

    title: Optional[str] = Field(
        default="",
        description="A title for the application.",
    )

    description: Optional[str] = Field(
        default="",
        description="A description of the application.",
    )


class ApplicationData(Common):
    """The data provided about an application by the core."""

    model_config = ConfigDict(from_attributes=True)

    created: datetime = Field(
        ...,
        description="The moment when this record was created.",
    )

    updated: datetime = Field(
        ...,
        description="The last time when this record was updated.",
    )


class ApplicationInput(Common):
    """The data creating or editing an application."""

    @field_validator("slug")
    def slug_is_valid(cls, v):
        """Validate the slug."""
        return slug_is_valid(v)

    @model_validator(mode="after")
    def model_validation(self):
        """Use the slug as title if not provided."""
        if not self.title:
            self.title = self.slug.title()
        return self
