"""OP#1 and OP#3 enforce the version range in README §2.3."""

import pytest


@pytest.mark.parametrize("endpoint,key", [("validate-id", "valid"), ("parse-id", "ok")])
@pytest.mark.parametrize(
    "template,index",
    [
        ("gts.x.bounds._.base.v{}~", 0),
        ("gts.x.bounds._.base.v1~acme.app._.derived.v{}~", 1),
        ("gts.x.bounds._.base.v1~acme.app._.item.v{}", 1),
    ],
    ids=["base_type", "derived_type", "instance"],
)
@pytest.mark.parametrize("component", ["major", "minor"])
@pytest.mark.parametrize(
    "number,valid",
    [(0, True), (4294967295, True), (4294967296, False), (10**80, False)],
    ids=["zero", "u32_max", "overflow", "large_overflow"],
)
def test_version_component_bounds(
    gts_api, endpoint, key, template, index, component, number, valid
):
    version = str(number) if component == "major" else f"1.{number}"
    identifier = template.format(version)
    result = gts_api.request("GET", "/" + endpoint, params={"gts_id": identifier})
    assert result["id"] == identifier, result
    assert result[key] is valid, result
    if not valid:
        assert result.get("error"), result
    elif endpoint == "parse-id":
        segment = result["segments"][index]
        assert segment["ver_major"] == (number if component == "major" else 1), result
        assert segment["ver_minor"] == (number if component == "minor" else None), result
