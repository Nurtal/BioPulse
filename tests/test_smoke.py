import biopulse


def test_package_has_version() -> None:
    assert isinstance(biopulse.__version__, str)
    assert biopulse.__version__
