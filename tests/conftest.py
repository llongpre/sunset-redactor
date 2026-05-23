"""Session-scoped fixtures: run each pipeline once before tests read from outputs."""
import pytest
from redactor.pipeline import run

PROVIDED_INPUT = "tests/data/provided/inputs"
PROVIDED_OUTPUT = "tests/data/provided/outputs"

SYNTHETIC_INPUT = "tests/data/synthetic/inputs"
SYNTHETIC_OUTPUT = "tests/data/synthetic/outputs"


def pytest_addoption(parser):
    parser.addoption(
        "--use-existing",
        action="store_true",
        default=False,
        help="Skip re-running the pipeline and use outputs already in tests/data/*/outputs/",
    )


@pytest.fixture(scope="session")
def pipeline_outputs(request):
    if not request.config.getoption("--use-existing"):
        run(PROVIDED_INPUT, PROVIDED_OUTPUT)


@pytest.fixture(scope="session")
def synthetic_pipeline_outputs(request):
    if not request.config.getoption("--use-existing"):
        run(SYNTHETIC_INPUT, SYNTHETIC_OUTPUT)
