"""Document-level x-gts-* keyword placement — §9.7.1/§9.11.

All four document-level keywords describe the GTS Type as a whole and MUST
appear at the **top level** of the GTS Type Schema document (adjacent to
`$id` / `$schema`):

- x-gts-final
- x-gts-abstract
- x-gts-traits-schema
- x-gts-traits

A keyword nested inside any subschema (an `allOf`/`anyOf`/… entry, a
`properties` value, a `$defs` entry, …) is a **misplacement** and MUST be
rejected (fail fast) on registration when validation is enabled
(`?validate=true`), per §9.7.1 / §9.11.5. The implementation MUST NOT silently
ignore it.

These tests assert that:
- the four keywords are accepted at the top level (positive control);
- each keyword nested inside an `allOf` entry is rejected (422);
- the rule applies to *any* subschema, not just `allOf` — modifiers nested in
  `properties` / `$defs` and traits nested in `properties` are also rejected.

Note: the rule constrains only the *position* of the keyword, not the
*contents* of `x-gts-traits-schema` (which is an ordinary JSON Schema subschema
and may freely use `$ref` / `allOf` internally — covered by OP#13 tests).
"""

from .conftest import get_gts_base_url
from .helpers.http_run_helpers import (
    register as _register,
)
from httprunner import HttpRunner, Config, Step, RunRequest

_SCHEMA = "http://json-schema.org/draft-07/schema#"


# ---------------------------------------------------------------------------
# x-gts-traits-schema / x-gts-traits — positive control (top-level accepted)
# ---------------------------------------------------------------------------


class TestCaseTraits_TopLevelAccepted(HttpRunner):
    """x-gts-traits-schema (base) and x-gts-traits (derived) at the top level are accepted.

    Positive control for §9.7.1/§9.11: correct top-level placement must register
    cleanly even with validation enabled.
    """

    config = Config("placement: traits top-level accepted").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.testkp.traitsok.base.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {
                        "topicRef": {"type": "string"},
                        "retention": {"type": "string"},
                    },
                },
                "properties": {"id": {"type": "string"}},
            },
            "register base with x-gts-traits-schema at top level",
        ),
        Step(
            RunRequest("register derived with x-gts-traits at top level should be accepted")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testkp.traitsok.base.v1~x.testkp._.derived.v1~",
                "$$schema": _SCHEMA,
                "type": "object",
                "x-gts-traits": {
                    "topicRef": "gts.x.core.events.topic.v1~x.testkp._.orders.v1",
                    "retention": "P90D",
                },
                "allOf": [
                    {"$$ref": "gts://gts.x.testkp.traitsok.base.v1~"},
                ],
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


# ---------------------------------------------------------------------------
# x-gts-traits — misplacement rejected
# ---------------------------------------------------------------------------


class TestCaseTraits_InsideAllOfRejected(HttpRunner):
    """x-gts-traits inside an allOf entry MUST be rejected (§9.7.1/§9.11).

    x-gts-traits is a type-level keyword; placing it inside an allOf subschema
    attaches it to a subschema rather than the type. Registration with
    validation MUST reject this rather than silently dropping the trait values.
    """

    config = Config("placement: x-gts-traits inside allOf rejected").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.testkp.traitsallof.base.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"topicRef": {"type": "string"}},
                },
                "properties": {"id": {"type": "string"}},
            },
            "register base with x-gts-traits-schema",
        ),
        Step(
            RunRequest("register derived with x-gts-traits inside allOf should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testkp.traitsallof.base.v1~x.testkp._.derived.v1~",
                "$$schema": _SCHEMA,
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.testkp.traitsallof.base.v1~"},
                    {
                        "type": "object",
                        "x-gts-traits": {
                            "topicRef": "gts.x.core.events.topic.v1~x.testkp._.orders.v1",
                        },
                    },
                ],
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseTraits_InsidePropertiesRejected(HttpRunner):
    """x-gts-traits nested inside a `properties` subschema MUST be rejected (§9.7.1/§9.11).

    Confirms the rule is about *any* subschema, not specifically allOf: a
    keyword buried inside a property's subschema is still a misplacement.
    """

    config = Config("placement: x-gts-traits inside properties rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.testkp.traitsprop.base.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"topicRef": {"type": "string"}},
                },
                "properties": {"id": {"type": "string"}},
            },
            "register base with x-gts-traits-schema",
        ),
        Step(
            RunRequest("register derived with x-gts-traits inside a property should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testkp.traitsprop.base.v1~x.testkp._.derived.v1~",
                "$$schema": _SCHEMA,
                "type": "object",
                "allOf": [{"$$ref": "gts://gts.x.testkp.traitsprop.base.v1~"}],
                "properties": {
                    "nested": {
                        "type": "object",
                        "x-gts-traits": {
                            "topicRef": "gts.x.core.events.topic.v1~x.testkp._.orders.v1",
                        },
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


# ---------------------------------------------------------------------------
# x-gts-traits-schema — misplacement rejected
# ---------------------------------------------------------------------------


class TestCaseTraitsSchema_InsideAllOfRejected(HttpRunner):
    """x-gts-traits-schema inside an allOf entry MUST be rejected (§9.7.1/§9.11).

    A descendant declaring a new trait shape must place x-gts-traits-schema at
    the document top level, not inside an allOf subschema. (This constrains the
    *position* of the keyword; the registry still chain-aggregates top-level
    x-gts-traits-schema declarations via allOf per §9.7.5.)
    """

    config = Config("placement: x-gts-traits-schema inside allOf rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        _register(
            "gts://gts.x.testkp.tschemaallof.base.v1~",
            {
                "type": "object",
                "x-gts-traits-schema": {
                    "type": "object",
                    "properties": {"topicRef": {"type": "string"}},
                },
                "properties": {"id": {"type": "string"}},
            },
            "register base with x-gts-traits-schema",
        ),
        Step(
            RunRequest("register derived with x-gts-traits-schema inside allOf should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testkp.tschemaallof.base.v1~x.testkp._.derived.v1~",
                "$$schema": _SCHEMA,
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.testkp.tschemaallof.base.v1~"},
                    {
                        "type": "object",
                        "x-gts-traits-schema": {
                            "type": "object",
                            "properties": {"auditRetention": {"type": "string"}},
                        },
                    },
                ],
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


# ---------------------------------------------------------------------------
# x-gts-final / x-gts-abstract — misplacement in NON-allOf subschemas
# (allOf cases live in test_refimpl_x_gts_final_abstract.py; these extend the
#  coverage to other subschema positions to exercise the "any subschema" rule.)
# ---------------------------------------------------------------------------


class TestCaseFinal_InsidePropertiesRejected(HttpRunner):
    """x-gts-final nested inside a `properties` subschema MUST be rejected (§9.7.1/§9.11)."""

    config = Config("placement: x-gts-final inside properties rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with x-gts-final inside a property should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testkp.finalprop.base.v1~",
                "$$schema": _SCHEMA,
                "type": "object",
                "properties": {
                    "nested": {
                        "type": "object",
                        "x-gts-final": True,
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseAbstract_InsideDefsRejected(HttpRunner):
    """x-gts-abstract nested inside a `definitions` entry MUST be rejected (§9.7.1/§9.11)."""

    config = Config("placement: x-gts-abstract inside definitions rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with x-gts-abstract inside definitions should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testkp.absdefs.base.v1~",
                "$$schema": _SCHEMA,
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "definitions": {
                    "Sub": {
                        "type": "object",
                        "x-gts-abstract": True,
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


# ---------------------------------------------------------------------------
# Matrix completion — remaining (keyword × subschema-position) cells
#
# The cases above cover most (keyword, position) pairs across this file and
# test_refimpl_x_gts_final_abstract.py (allOf cases). These three fill the
# still-missing cells so every document-level keyword is proven to be rejected
# in allOf, `properties`, and `definitions` positions:
#   - x-gts-traits-schema inside `properties`
#   - x-gts-final inside `definitions`
#   - x-gts-abstract inside `properties`
# ---------------------------------------------------------------------------


class TestCaseTraitsSchema_InsidePropertiesRejected(HttpRunner):
    """x-gts-traits-schema nested inside a `properties` subschema MUST be rejected.

    Complements TestCaseTraitsSchema_InsideAllOfRejected: the placement rule is
    about *any* subschema, so a trait-schema buried in a property is equally a
    misplacement (§9.7.1/§9.11).
    """

    config = Config("placement: x-gts-traits-schema inside properties rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with x-gts-traits-schema inside a property should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testkp.tschemaprop.base.v1~",
                "$$schema": _SCHEMA,
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "nested": {
                        "type": "object",
                        "x-gts-traits-schema": {
                            "type": "object",
                            "properties": {"topicRef": {"type": "string"}},
                        },
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseFinal_InsideDefsRejected(HttpRunner):
    """x-gts-final nested inside a `definitions` entry MUST be rejected (§9.7.1/§9.11).

    Complements TestCaseFinal_InsidePropertiesRejected (this file) and the allOf
    case in test_refimpl_x_gts_final_abstract.py.
    """

    config = Config("placement: x-gts-final inside definitions rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with x-gts-final inside definitions should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testkp.finaldefs.base.v1~",
                "$$schema": _SCHEMA,
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "definitions": {
                    "Sub": {
                        "type": "object",
                        "x-gts-final": True,
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseAbstract_InsidePropertiesRejected(HttpRunner):
    """x-gts-abstract nested inside a `properties` subschema MUST be rejected (§9.7.1/§9.11).

    Complements TestCaseAbstract_InsideDefsRejected (this file) and the allOf
    case in test_refimpl_x_gts_final_abstract.py.
    """

    config = Config("placement: x-gts-abstract inside properties rejected").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with x-gts-abstract inside a property should be rejected")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.testkp.absprop.base.v1~",
                "$$schema": _SCHEMA,
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "nested": {
                        "type": "object",
                        "x-gts-abstract": True,
                    },
                },
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]
