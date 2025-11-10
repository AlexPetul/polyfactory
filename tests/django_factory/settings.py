import os

FACTORY_ROOT = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),  # /path/to/fboy/tests/djapp/
    os.pardir,  # /path/to/fboy/tests/
    os.pardir,  # /path/to/fboy
)

DATABASES = {
    "default": {
        "NAME": "default",
        "ENGINE": "django.db.backends.sqlite3",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "tests.django_factory",
]

MIDDLEWARE_CLASSES = ()

SECRET_KEY = "testing."

USE_TZ = True
