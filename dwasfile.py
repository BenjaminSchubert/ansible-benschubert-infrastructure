# ruff: noqa: D100,D101,D102,D103
import logging
import shutil
import sys
from contextlib import suppress
from pathlib import Path

from dwas import (
    StepRunner,
    managed_step,
    parametrize,
    register_managed_step,
    register_step_group,
)
from dwas.predefined import mypy, pylint, ruff, sphinx

ARTIFACTS_PATH = Path().parent.joinpath("_artifacts")
LOGGER = logging.getLogger(__name__)
PYTHON_FILES = [
    "dwasfile.py",
    "docs/",
    "plugins",
    "molecule/",
    ".github/scripts",
]


def _install_collection(step: StepRunner) -> tuple[dict[str, str], str]:
    ansible_home = step.cache_path / "ansible"
    collection_path = str(
        ansible_home
        / "collections/ansible_collections/benschubert/infrastructure"
    )

    env = {"ANSIBLE_HOME": str(ansible_home)}
    # FIXME: once we can set an environment variable from a step, we should
    #        have the build step take care of the installation and inject
    #        the collections path

    step.run(
        [
            "ansible-galaxy",
            "collection",
            "install",
            "--force",
            *step.get_artifacts("ansible_collections"),
        ],
        env=env,
    )

    # ansible-test sanity ignores the installed part otherwise, since it's
    # in our gitignore
    step.run(
        ["git", "init", collection_path],
        external_command=True,
        silent_on_success=True,
    )

    return env, collection_path


##
# Packaging
##
class Build:
    def gather_artifacts(self, step: "StepRunner") -> dict[str, list[str]]:
        return {
            "ansible_collections": [
                str(collection) for collection in step.cache_path.glob("*")
            ],
        }

    def __call__(self, step: StepRunner) -> None:
        with suppress(FileNotFoundError):
            shutil.rmtree(step.cache_path)

        step.run(
            [
                "ansible-galaxy",
                "collection",
                "build",
                "--output-path",
                str(step.cache_path),
            ],
        )
        files = list(step.cache_path.glob("*"))
        assert len(files) == 1
        dest = ARTIFACTS_PATH / files[0].name
        ARTIFACTS_PATH.mkdir(exist_ok=True)

        shutil.copy(files[0], dest)
        LOGGER.info("Artifact can be found at %s", dest)


register_managed_step(
    Build(),
    ["-rrequirements/requirements.txt"],
    name="build",
    description="Build the collection",
)


##
# Linting
##
register_managed_step(
    mypy(files=PYTHON_FILES),
    dependencies=[
        "mypy",
        "-rrequirements/requirements-docs.txt",
        "-rrequirements/requirements-tests.txt",
        "-rrequirements/requirements-types.txt",
    ],
)
register_managed_step(
    pylint(files=PYTHON_FILES),
    dependencies=[
        "dwas",
        "pylint",
        "-rrequirements/requirements.txt",
        "-rrequirements/requirements-tests.txt",
    ],
)
register_managed_step(ruff())
register_managed_step(
    ruff(additional_arguments=["check", "--fix"]),
    name="ruff:fix",
    run_by_default=False,
)
register_managed_step(
    ruff(additional_arguments=["format", "--diff"]),
    name="format",
)
register_managed_step(
    ruff(additional_arguments=["format"]),
    name="format:fix",
    run_by_default=False,
)


@managed_step(["-rrequirements/requirements.txt"], requires=["build"])
def sanity(step: StepRunner) -> None:
    env, collection_path = _install_collection(step)

    command = [
        "ansible-test",
        "sanity",
        "--local",
        f"--python={sys.version_info.major}.{sys.version_info.minor}",
        # We use asserts to help mypy, not for workflows
        "--skip-test=no-assert",
        # pylint seems to be buggy, we use our own config
        "--skip-test=pylint",
    ]
    if step.config.colors:
        command.append("--color=yes")

    step.run(
        command,
        cwd=collection_path,
        env={"HOME": str(step.cache_path / "home"), **env},
    )


@managed_step(
    ["-rrequirements/requirements.txt", "ansible-lint"],
    requires=["build"],
    name="ansible-lint",
)
def ansible_lint(step: StepRunner) -> None:
    env, collection_path = _install_collection(step)

    command = ["ansible-lint", "--strict"]
    if step.config.colors:
        command.append("--force-color")

    step.run(
        command,
        cwd=collection_path,
        env={"HOME": str(step.cache_path / "home"), **env},
    )


register_step_group(
    "lint",
    ["ansible-lint", "format", "mypy", "pylint", "ruff", "sanity"],
    description="Run all linters on the project",
)
register_step_group(
    "fix",
    ["ruff:fix", "format:fix"],
    description="Fix everything that can be fixed automatically",
    run_by_default=False,
)


##
# Test
##
@managed_step(
    ["-rrequirements/requirements-dev.txt"],
    description="Run molecule tests against the collection",
    passenv=["USER", "HOME"],
)
def molecule(step: StepRunner, user_args: list[str] | None) -> None:
    if user_args is None:
        user_args = ["test"]
    step.run(
        ["molecule", *user_args],
        env={"ANSIBLE_HOME": str(step.cache_path / "ansible")},
    )


##
# Docs
##
@managed_step(
    ["-rrequirements/requirements-docs.txt"],
    requires=["build"],
    run_by_default=False,
)
def autodoc(step: StepRunner) -> None:
    env, collection_path = _install_collection(step)
    home_path = step.cache_path / "home"
    home_path.mkdir(exist_ok=True)
    env["HOME"] = str(home_path)

    with suppress(FileNotFoundError):
        shutil.rmtree("docs/collections")

    step.run(
        [
            "antsibull-docs",
            "--config-file=docs/antsibull-docs.cfg",
            "collection",
            "--use-current",
            "--fail-on-error",
            "--dest-dir=docs",
            "--squash-hierarchy",
            "benschubert.infrastructure",
        ],
        env=env,
    )
    step.run(
        [
            "antsibull-docs",
            "--config-file=docs/antsibull-docs.cfg",
            "lint-collection-docs",
            "--plugin-docs",
            "--validate-collection-refs=all",
            collection_path,
        ],
        env=env,
    )


register_managed_step(
    parametrize(
        ("builder", "output", "description"),
        [
            (
                "html",
                ARTIFACTS_PATH / "docs",
                "Build an HTML version of the docs",
            ),
            ("linkcheck", None, "Check that all links in the docs are valid"),
            ("spelling", None, "Check spelling for the docs"),
        ],
        ids=["html", "linkcheck", "spelling"],
    )(
        sphinx(
            sourcedir="docs",
            warning_as_error=True,
        ),
    ),
    name="docs",
    description="Build and validate the documentation",
    dependencies=["-rrequirements/requirements-docs.txt"],
    requires=["autodoc"],
    run_by_default=False,
)
