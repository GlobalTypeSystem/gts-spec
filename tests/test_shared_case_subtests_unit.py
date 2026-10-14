"""Regression checks for shared case diagnostics in pytest's CI reports."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "failure_statement,error_detail",
    [
        pytest.param(
            "assert False, 'wrong verdict'",
            "AssertionError: wrong verdict",
            id="assertion",
        ),
        pytest.param(
            "raise KeyError('ok')", "KeyError: 'ok'", id="missing_response_key"
        ),
    ],
)
def test_failed_case_subtest_reports_context_and_continues(
    tmp_path, failure_statement, error_detail
):
    (tmp_path / "pytest.ini").write_text("[pytest]\nminversion = 9.0\n")
    (tmp_path / "test_probe.py").write_text(
        "from pathlib import Path\n"
        "from tests.helpers.shared_cases import case_subtest\n"
        "def test_shared_cases(subtests):\n"
        "    for case in ('bad_vector', 'good_vector'):\n"
        "        with case_subtest(subtests, case=case, expected=True):\n"
        "            with Path('visited.txt').open('a') as visited:\n"
        "                visited.write(case + '\\n')\n"
        "            if case == 'bad_vector':\n"
        f"                {failure_statement}\n"
    )
    repo = str(Path(__file__).resolve().parent.parent)
    python_path = [repo]
    if os.environ.get("PYTHONPATH"):
        python_path.append(os.environ["PYTHONPATH"])
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(python_path))
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "test_probe.py",
            "-q",
            "-p",
            "no:cacheprovider",
            "--junitxml=report.xml",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert (tmp_path / "visited.txt").read_text().splitlines() == [
        "bad_vector",
        "good_vector",
    ]
    for report in (result.stdout, (tmp_path / "report.xml").read_text()):
        assert "Test case bad_vector" in report
        assert "'expected': True" in report
        assert "test_probe.py" in report
        assert error_detail in report
