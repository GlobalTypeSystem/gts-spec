"""Offline regression tests for the schema check in validate-schemas.yml.

The workflow's script runs with a stub `ajv` on PATH; no npm or GTS server is
needed. The workflow file is not part of the test-runner image, so these tests
are skipped there.
"""

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

_WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "validate-schemas.yml"

_UNRESOLVED = "error: can't resolve reference gts://gts.x.missing.v1~ from id gts://gts.x.holder.v1~"
_SCHEMA_ERROR = "error: schema is invalid: data/properties/x/type must be equal to one of the allowed values"

# (output, ajv exit code, expected script exit code)
_SCENARIOS = {
    "success": ("schema a.schema.json is valid", 0, 0),
    "schema_error": ("schema a.schema.json is invalid\n" + _SCHEMA_ERROR, 1, 1),
    "unresolved_only": (
        "schema a.schema.json is valid\nschema b.schema.json is invalid\n" + _UNRESOLVED,
        1,
        0,
    ),
    "mixed_known": (_UNRESOLVED + "\n" + _SCHEMA_ERROR, 1, 1),
    "mixed_unknown": (
        "error: can't resolve reference gts://missing\nTypeError: unexpected fatal failure",
        1,
        1,
    ),
    "unknown_failure": ("Segmentation fault", 139, 1),
    "silent_failure": ("", 1, 1),
    "missing_ajv": ("", 127, 1),
}


def _script():
    if not _WORKFLOW.is_file():
        pytest.skip("workflow file is not available")
    workflow = yaml.safe_load(_WORKFLOW.read_text())
    steps = workflow["jobs"]["validate"]["steps"]
    return next(step["run"] for step in steps if step.get("name") == "Validate schemas")


@pytest.mark.parametrize("scenario", sorted(_SCENARIOS))
def test_schema_check_exit_code(tmp_path, scenario):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available")
    output, ajv_code, expected = _SCENARIOS[scenario]
    script = tmp_path / "validate.sh"
    script.write_text(_script())
    stub = tmp_path / "bin" / "ajv"
    stub.parent.mkdir()
    stub.write_text(
        '#!/bin/sh\n[ -n "$AJV_STUB_OUTPUT" ] && printf \'%s\\n\' "$AJV_STUB_OUTPUT" >&2\n'
        'exit "$AJV_STUB_CODE"\n'
    )
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    env = dict(
        os.environ,
        PATH=f"{stub.parent}{os.pathsep}{os.environ.get('PATH', '')}",
        AJV_STUB_OUTPUT=output,
        AJV_STUB_CODE=str(ajv_code),
    )
    # GitHub Actions runs bash steps with -e and pipefail.
    result = subprocess.run(
        [bash, "--noprofile", "--norc", "-eo", "pipefail", str(script)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == expected, (scenario, result.stdout, result.stderr)
    if scenario == "unresolved_only":
        assert "WARN: some $ref targets could not be resolved" in result.stdout
