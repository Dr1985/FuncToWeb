from pathlib import Path
from typing import Annotated, Literal
from datetime import date, time

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
    """Base class for grouping function parameters.
    
    Subclass this to define reusable parameter groups.
    Functoweb expands fields automatically into the form.

    Example:
        class UserData(Params):
            name: Annotated[str, Field(min_length=2)]
            email: Email
            role: Literal["admin", "user"] = "user"

        def create_user(data: UserData): ...
        def edit_user(id: int, data: UserData): ...
    """
    pass
