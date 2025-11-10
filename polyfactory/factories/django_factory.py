import datetime
import enum
import uuid
from decimal import Decimal
from typing import Any, TypeVar, TYPE_CHECKING, Generic, Callable, cast, ClassVar, Iterable, Iterator, Literal, Union

from polyfactory import SyncPersistenceProtocol
from polyfactory.factories.base import BaseFactory, BuildContext
from polyfactory.field_meta import FieldMeta, Constraints
from polyfactory.field_meta import Null
from django.db.models import fields as django_fields
from django.db.models.base import ModelBase


if TYPE_CHECKING:
    from typing_extensions import TypeGuard

T = TypeVar("T")


class DjangoSyncPersistence(SyncPersistenceProtocol[T]):

    def save(self, data: T) -> T:
        data.save()
        return data


class DjangoFactory(Generic[T], BaseFactory[T]):
    __is_base_factory__ = True
    __sync_persistence__ = DjangoSyncPersistence
    __async_persistence__: ClassVar[None] = None

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)

        if cls.__model__._meta.abstract:
            msg = f" Abstract model {cls.__model__} cannot be instantiated."
            raise TypeError(
                msg,
            )

    @classmethod
    def is_supported_type(cls, value: Any) -> "TypeGuard[type[T]]":
        return isinstance(value, ModelBase)

    @classmethod
    def get_annotation(cls, field: django_fields.Field) -> type:
        scalars: dict[type[django_fields.Field], type | Any] = {
            django_fields.AutoField: int,
            django_fields.BigIntegerField: int,
            django_fields.BigAutoField: int,
            django_fields.BinaryField: bytes,
            django_fields.PositiveIntegerField: int,
            django_fields.IntegerField: int,
            django_fields.SlugField: str,
            django_fields.FloatField: float,
            django_fields.BooleanField: bool,
            django_fields.CharField: str,
            django_fields.FilePathField: str,
            django_fields.DateField: datetime.date,
            django_fields.DateTimeField: datetime.datetime,
            django_fields.DecimalField: Decimal,
            django_fields.DurationField: datetime.timedelta,
        }

        if not (annotation := scalars.get(type(field))):
            annotation = type(field)

        # Dynamically create a Literal from the field's `choices`.
        if choices := getattr(field, "choices", None):
            literal_values = tuple(cls._flatten_choices(choices))
            annotation = Literal.__getitem__(literal_values)

        if field.is_relation:
            annotation = field.related_model

        if field.null:
            annotation = Union[annotation, None]

        return annotation

    @classmethod
    def get_provider_map(cls) -> dict[Any, Callable[[], Any]]:
        mapping = super().get_provider_map()
        mapping.update(
            {
                django_fields.EmailField: cls.__faker__.email,
                django_fields.URLField: cls.__faker__.url,
                django_fields.FilePathField: lambda: cls.__faker__.file_path(depth=0),
            },
        )
        return mapping

    @classmethod
    async def create_async(cls, **kwargs: Any) -> T:  # type: ignore[override]
        msg = "DjangoFactory does not support async persistence"
        raise NotImplementedError(msg)

    @classmethod
    async def create_batch_async(cls, size: int, **kwargs: Any) -> list[T]:  # type: ignore[override]
        msg = "DjangoFactory does not support async persistence"
        raise NotImplementedError(msg)

    @staticmethod
    def _flatten_choices(choices: Iterable[Any]) -> Iterator[Any]:
        for choice in choices:
            if isinstance(choice, enum.Enum):
                yield choice.value
            elif isinstance(choice, (list, tuple)):
                if len(choice) == 2 and isinstance(choice[1], (list, tuple)):
                    yield from DjangoFactory._flatten_choices(choice[1])
                else:
                    yield choice[0]
            else:
                yield choice

    @classmethod
    def get_default_value(cls, field: django_fields.Field):
        if field.is_relation or not field.has_default():
            return Null

        return field.default

    @classmethod
    def get_constraints(cls, field: django_fields.Field) -> Constraints:
        constraints: Constraints = {}

        provider_map = cls.get_provider_map()
        if type(field) in provider_map:
            return constraints

        constraints["le"] = getattr(field, "max_length", None)
        constraints["decimal_places"] = getattr(field, "decimal_places", None)
        constraints["max_digits"] = getattr(field, "max_digits", None)

        if isinstance(field, django_fields.SlugField):
            constraints["pattern"] = r"^[-a-zA-Z0-9_]+\Z"

        constraints = cast("Constraints", {k: v for k, v in constraints.items() if v is not None})

        return constraints

    @classmethod
    def get_model_fields(cls) -> list[FieldMeta]:
        fields_meta: list[FieldMeta] = []
        fields = cls.__model__._meta.get_fields()

        for field in fields:
            fields_meta.append(
                FieldMeta(
                    name=field.name,
                    annotation=cls.get_annotation(field),
                    default=cls.get_default_value(field),
                    constraints=cls.get_constraints(field),
                )
            )

        return fields_meta
