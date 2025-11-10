import contextlib

from django.db import connection
from django.test.utils import (
    setup_databases,
    setup_test_environment,
    teardown_databases,
    teardown_test_environment,
)


@contextlib.contextmanager
def setup_models(*models):
    setup_test_environment()
    config = setup_databases(verbosity=0, interactive=False)

    try:
        with connection.schema_editor() as schema_editor:
            for model in models:
                schema_editor.create_model(model)

        yield

    finally:
        with connection.schema_editor() as schema_editor:
            for model in models:
                schema_editor.delete_model(model)
        teardown_databases(config, verbosity=0)
        teardown_test_environment()
