"""Shared case subtests with diagnostics preserved by terminal and JUnit reports."""

from contextlib import contextmanager


@contextmanager
def case_subtest(subtests, *, case, **context):
    with subtests.test(case=case, **context):
        try:
            yield
        except Exception as error:
            # Reporters do not all preserve pytest's subtest context metadata.
            # Keep it in the exception too, retaining the original traceback.
            raise AssertionError(
                f"Test case {case}: {context!r}\n{type(error).__name__}: {error}"
            ).with_traceback(error.__traceback__) from None
