from pathlib import Path
from typing import Annotated, Literal
from datetime import date, time
from dataclasses import dataclass

from pydantic import Field, BaseModel, model_validator
from pytypeinput.types import (Color, Email, ImageFile, VideoFile,
                         AudioFile, DataFile, TextFile, DocumentFile,
                         File, OptionalEnabled, OptionalDisabled, Dropdown,
                         IsPassword, Placeholder, Step, PatternMessage,
                         Description, Label, Rows, Slider)

__all__ = [
    # deliberate re-exports
    "Field",
    "Annotated",
    "Literal",
    "date",
    "time",
    # this module
    "FileResponse",
    "Params",
    # pytypeinput types
    "Color",
    "Email",
    "ImageFile",
    "VideoFile",
    "AudioFile",
    "DataFile",
    "TextFile",
    "DocumentFile",
    "File",
    "OptionalEnabled",
    "OptionalDisabled",
    "Dropdown",
    "IsPassword",
    "Placeholder",
    "Step",
    "PatternMessage",
    "Description",
    "Label",
    "Rows",
    "Slider",
]


class FileResponse(BaseModel):
    """Return a file from a function as a downloadable result.

    Provide either `data` or `path`, not both.

    Examples:
        return FileResponse(data=b"hello", filename="result.txt")
        return FileResponse(path="/tmp/report.pdf")
        return [FileResponse(...), FileResponse(...)]
    """
    data: bytes | None = None
    path: str | None = None
    filename: Annotated[str, Field(max_length=150)] | None= None

    @model_validator(mode="after")
    def _validate_data_or_path(self):
        if self.data is None and self.path is None:
            raise ValueError("Either 'data' or 'path' must be provided")
        if self.data is not None and self.path is not None:
            raise ValueError("Cannot provide both 'data' and 'path'")
        if self.data is not None and self.filename is None:
            raise ValueError("'filename' is required when providing 'data'")
        if self.path is not None and self.filename is None:
            self.filename = Path(self.path).name
        return self


class Params:
    """Immutable group of parameters.

    Subclass with annotated fields. Subclasses become frozen
    dataclasses automatically: constructible with keyword arguments,
    comparable, hashable, immutable. Use __post_init__ for
    cross-field validation or derived fields (raise ValueError there
    and the form shows it as a 422 validation error).

    Example:
        class UserData(Params):
            name: Annotated[str, Field(min_length=2)]
            email: Email
            age: int = 18

        UserData(name="Ana", email="a@b.com")    # usable anywhere
    """
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        dataclass(frozen=True)(cls)
