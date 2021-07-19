"""
# BaseModel and FileModel

Nice *description*.

"""
from abc import ABC, abstractclassmethod, abstractmethod
from hydrolib.core.io.base import DummmyParser, DummySerializer
from pathlib import Path
from typing import Any, Callable, List, Optional, Protocol, Type, Union

from pydantic import BaseModel as PydanticBaseModel
from pydantic.types import DirectoryPath


class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        use_enum_values = True
        extra = "allow"


class FileModel(BaseModel, ABC):
    """Base class to represent models with a file representation.

    It therefore always has a `filepath` and if it is given on
    initilization, it will parse that file.

    This class extends the `validate` option of Pydantic,
    so when when a Path is given to a field with type `FileModel`,
    it doesn't error, but actually initializes the `FileModel`.
    """

    filepath: Optional[Path] = None

    def __init__(self, filepath: Optional[Path] = None, *args, **kwargs):
        # Parse the file if path is given
        if filepath:
            data = self._load(filepath)
            data["filepath"] = filepath
            kwargs.update(data)
        super().__init__(*args, **kwargs)

    @classmethod
    def validate(cls: Type["FileModel"], value: Any) -> "FileModel":
        # Enable initialization with a Path.
        if isinstance(value, Path):
            # Pydantic Model init requires a dict
            value = {"filepath": value}
        return super().validate(value)

    def _load(self, filepath: Path):
        return self._parse(filepath)

    def save(self, folder: Path):
        """Save model and child models to set filepaths."""

        if not self.filepath:
            self.filepath = folder / self._generate_name()

        # Convert child FileModels first
        exclude = {"filepath"}
        filemodel_fields = {}
        for name, value in self:
            if isinstance(value, FileModel):
                filepath = value.save(folder)
                filemodel_fields[name] = filepath
                exclude.add(name)

        # Convert other values to dict
        data = self.dict(
            exclude=exclude,
            exclude_none=True,  # either skip it here, or in serializer
        )
        data.update(filemodel_fields)

        self._serialize(data)

        return str(self.filepath.absolute())

    def _serialize(self, data: dict):
        self._get_serializer()(self.filepath, data)

    @classmethod
    def _parse(cls, path: Path):
        return cls._get_parser()(path)

    @classmethod
    def _generate_name(cls):
        name, ext = cls._filename(), cls._ext()
        return Path(f"{name}{ext}")

    @abstractclassmethod
    def _filename(cls):
        return "test"

    @abstractclassmethod
    def _ext(cls):
        return ".test"

    @abstractclassmethod
    def _get_serializer(cls) -> Callable:
        return DummySerializer.serialize

    @abstractclassmethod
    def _get_parser(cls) -> Callable:
        return DummmyParser.parse
