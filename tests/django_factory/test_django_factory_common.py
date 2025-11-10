import asyncio
import datetime
import os
import re
from decimal import Decimal

import django
import pytest

from polyfactory.factories.django_factory import DjangoFactory, DjangoSyncPersistence
from tests.django_factory.utils import setup_models

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_factory.settings")
django.setup()

from django.core import validators
from django.db import models
from django.test.utils import isolate_apps


@isolate_apps("tests.django_factory")
def test_python_type_handling():
    class Author(models.Model):
        auto_type = models.AutoField(primary_key=True)
        bigint_type = models.BigIntegerField()
        binary_type = models.BinaryField()
        boolean_type = models.BooleanField()
        str_type = models.CharField()
        slug_type = models.SlugField()
        url_type = models.URLField()
        int_type = models.IntegerField()
        float_type = models.FloatField()
        date_type = models.DateField()
        decimal_type = models.DecimalField()
        datetime_type = models.DateTimeField()
        email_type = models.EmailField()
        duration_type = models.DurationField()
        file_path_type = models.FilePathField(path=os.getcwd())

    class AuthorFactory(DjangoFactory[Author]):
        __use_defaults__ = False

    instance = AuthorFactory.build()
    assert isinstance(instance.auto_type, int)
    assert isinstance(instance.bigint_type, int)
    assert isinstance(instance.binary_type, bytes)
    assert isinstance(instance.boolean_type, bool)
    assert isinstance(instance.str_type, str)
    assert isinstance(instance.slug_type, str)
    assert isinstance(instance.url_type, str)
    assert isinstance(instance.int_type, int)
    assert isinstance(instance.float_type, float)
    assert isinstance(instance.date_type, datetime.date)
    assert isinstance(instance.decimal_type, Decimal)
    assert isinstance(instance.datetime_type, datetime.datetime)
    assert isinstance(instance.email_type, str)
    assert isinstance(instance.duration_type, datetime.timedelta)
    assert isinstance(instance.file_path_type, str)


class Status(models.TextChoices):
    DRAFT = "draft"
    PUBLISHED = "published"


class StatusInt(models.IntegerChoices):
    DRAFT = 1
    PUBLISHED = 2


@pytest.mark.parametrize(
    "choices, result",
    [
        (
            [("draft", "Draft"), ("published", "Published")],
            ("draft", "published"),
        ),
        (
            {"draft": "Draft", "published": "Published"},
            ("draft", "published"),
        ),
        (
            lambda: {"draft": "Draft", "published": "Published"},
            ("draft", "published"),
        ),
        (
            Status,
            ("draft", "published"),
        ),
        (
            StatusInt,
            (1, 2),
        ),
    ],
)
@isolate_apps("tests.django_factory")
def test_choices_field(choices, result):
    class Author(models.Model):
        choice_field = models.CharField(choices=choices)

    class AuthorFactory(DjangoFactory[Author]):
        __use_defaults__ = False

    instance = AuthorFactory.build()
    assert instance.choice_field in result


@isolate_apps("tests.django_factory")
def test_foreign_key_relationship():
    class Parent(models.Model):
        name = models.CharField(max_length=10, unique=True)

    class Child(models.Model):
        parent = models.ForeignKey(Parent, on_delete=models.CASCADE)

    class ParentFactory(DjangoFactory[Parent]):
        pass

    class ChildFactory(DjangoFactory[Child]):
        pass

    with setup_models(Parent, Child):
        parent = ParentFactory.create_sync()
        child = ChildFactory.create_sync(parent=parent)

        assert child.parent == parent
        assert Parent.objects.count() == 1
        assert Child.objects.count() == 1


@isolate_apps("tests.django_factory")
def test_explicit_constrainted_fields():
    class Author(models.Model):
        string = models.CharField(max_length=5)
        binary = models.BinaryField(max_length=5)
        decimal = models.DecimalField(max_digits=4, decimal_places=2)

    class AuthorFactory(DjangoFactory[Author]):
        __use_defaults__ = False

    instance = AuthorFactory.build()
    assert len(instance.string) <= 5
    assert len(instance.binary) <= 5
    assert abs(len(instance.decimal.as_tuple().digits) - abs(int(instance.decimal.as_tuple().exponent))) <= 2


@isolate_apps("tests.django_factory")
def test_implicit_constrainted_fields():
    class Author(models.Model):
        slug = models.SlugField()
        positive_integer = models.PositiveIntegerField()
        url = models.URLField()

    class AuthorFactory(DjangoFactory[Author]):
        __use_defaults__ = False

    instance = AuthorFactory.build()

    assert re.match(r"^[-a-zA-Z0-9_]+\Z", instance.slug)
    assert instance.positive_integer >= 0
    assert validators.URLValidator.regex.match(instance.url)


@isolate_apps("tests.django_factory")
def test_sync_persistence():
    class Author(models.Model):
        pass

    class AuthorFactory(DjangoFactory[Author]):
        __sync_persistence__ = DjangoSyncPersistence

    with setup_models(Author):
        instance = AuthorFactory.create_sync()

        assert instance.pk is not None
        assert hasattr(instance, "_state") and not instance._state.adding


@isolate_apps("tests.django_factory")
def test_async_persistence_not_supported():
    class Author(models.Model):
        pass

    class AuthorFactory(DjangoFactory[Author]):
        __sync_persistence__ = DjangoSyncPersistence

    with setup_models(Author):
        msg = "DjangoFactory does not support async persistence"

        async def call_create_async() -> None:
            await AuthorFactory.create_async()

        async def call_create_batch_async() -> None:
            await AuthorFactory.create_batch_async(size=1)

        with pytest.raises(NotImplementedError, match=msg):
            asyncio.run(call_create_async())

        with pytest.raises(NotImplementedError, match=msg):
            asyncio.run(call_create_batch_async())
