"""Nox sessions."""
import tempfile

import nox
from nox.sessions import Session


package = "nucoro"
locations = "nucoro",


@nox.session(python="3.7")
def lint(session: Session) -> None:
    """Lint using flake8."""
    args = session.posargs or locations
    session.run("flake8", *args, external=True)


@nox.session(python="3.7")
def safety(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "pip", "freeze", ">", f"{requirements.name}", external=True,
        )
        print(requirements.name)
        session.run("safety", "check", external=True)


@nox.session(python="3.7")
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or locations
    session.run("mypy", *args, external=True)


@nox.session(python="3.7")
def tests(session: Session) -> None:
    """Run the test suite."""
    args = session.posargs or ["run", "--source=" ".", "nucoro/manage.py", "test", "exchanger"]
    session.run("coverage", *args, external=True)


# @nox.session(python="3.7")
# def typeguard(session: Session) -> None:
#     """Runtime type checking using Typeguard."""
#     args = session.posargs or ["-m", "not integration"]
#     session.run("pytest", f"--typeguard-packages={package}", *args, external=True)


@nox.session(python="3.7")
def pytype(session: Session) -> None:
    """Type-check using pytype."""
    args = session.posargs or ["--disable=import-error", *locations]
    session.run("pytype", *args, external=True)


@nox.session(python="3.7")
def coverage(session: Session) -> None:
    """Upload coverage data."""
    session.run("coverage", "report", "--fail-under=0")
