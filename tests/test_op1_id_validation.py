import pytest
from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest, Parameters


class TestCaseTestOp1IdValidationAllValid(HttpRunner):
    config = Config(
        "OP#1 - Validate ID (all valid cases)"
    ).base_url(
        get_gts_base_url()
    )

    @pytest.mark.parametrize(
        "param",
        Parameters(
            {
                "id": [
                    "gts.x.test1.events.type.v1~",
                    "gts.abc.commerce.orders.order.v2.15~",
                    "gts.vendor.pkg.ns.type.v0~",
                    "gts.v123.p456.n789.t000.v999.888~",
                    "gts.x.pkg._.type.v1~",
                    "gts.myvendor.mypackage.mynamespace.mytype.v1.0~",
                    "gts.x.test1.events.type.v1~abc.app._.custom_event.v1~",
                    "gts.x.test1.events.type.v1~abc.app._.custom_event.v1.2",
                    "gts.a.b.c.d.v1~e.f.g.h.v2~i.j.k.l.v3~",
                    "gts.vendor_name.pkg_123.ns_abc.type_xyz.v10.5~",
                    "gts.a1.b2.c3.d4.v100.200~",
                    (
                        "gts.x.test1.events.type.v1~vendor.app."
                        "derived.event.v2~"
                        "vendor.app._.event.v2.0"
                    ),
                    (
                        "gts.longvendorname.longpackagename."
                        "longnamespacename.longtypename.v1~"
                    ),
                    "gts._a.b2.c3._d4.v1~",
                    (
                        "gts.x.test1.events.type.v1~a.b.c.d.v1~"
                        "e.f.g.h.v1~i.j.k.l.v1.0"
                    ),
                    "gts.v.v.v.v.v1~",
                    "gts.a.b.c.d.v0~",
                    "gts._._._._.v1~",
                    "gts.x.y.z.a.v999999.888888~",
                ]
            }
        ),
    )
    def test_start(self, param):
        super().test_start(param)

    teststeps = [
        Step(
            RunRequest("validate gts_id is valid (all valid)")
            .get("/validate-id")
            .with_params(**{"gts_id": "${id}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.id", "${id}")
            .assert_equal("body.valid", True)
        ),
    ]


class TestCaseTestOp1IdValidationInvalid(HttpRunner):
    config = Config(
        "OP#1 - Validate ID (all invalid cases)"
    ).base_url(
        get_gts_base_url()
    )

    @pytest.mark.parametrize(
        "param",
        Parameters(
            {
                "id": [
                    "GTS.x.test1.events.type.v1~",
                    "gts.X.core.events.type.v1~",
                    "gts.x.test1.events.type.V1~",
                    "x.test1.events.type.v1~",
                    "gts.x.test1.events.type.1~",
                    "gts.x.test1.events.type.v1.2.3~",
                    "gts.x.test1.events.type.v-1~",
                    "gts.x.test1.events.type.v1.~",
                    "gts.x.test1.events.type.v01~",
                    "gts.x.test1.events.type.v1.01~",
                    "gts.x.mq.messages._._.v1",
                    "gts.1vendor.core.events.type.v1~",
                    "gts.x.core-events.events.type.v1~",
                    "gts.x.test1.events..event.v1~",
                    "gts.x.test1.events.type.v1.0~~",
                    "gts.x.test1.events.type.v1~gts.abc.app._.custom.v1~",
                    "gts.x.test1.events.type.v1.abc.app.namespace.custom.v1",
                    "gts.x.test1.events.event~",
                    "gts.x.test1.events.v1~",
                    "gts.x.test1.namespace.type.v1~a.b.c.v1",
                    "gts.x.test1.events.type.v1.0.0~",
                ]
            }
        ),
    )
    def test_start(self, param):
        super().test_start(param)

    teststeps = [
        Step(
            RunRequest("validate gts_id is invalid")
            .get("/validate-id")
            .with_params(**{"gts_id": "${id}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.id", "${id}")
            .assert_equal("body.valid", False)
            .assert_not_equal("body.error", "")
        ),
    ]


class TestCaseTestOp1IdValidation_MaxLengthSegments(HttpRunner):
    """OP#1 Extended - IDs with maximum length segments"""
    config = Config(
        "OP#1 Extended - Max Length Segments"
    ).base_url(
        get_gts_base_url()
    )

    @pytest.mark.parametrize(
        "param",
        Parameters(
            {
                "id": [
                    "gts.verylongvendorname123456789.pkg.ns.type.v1~",
                    "gts.x.verylongpackagename123456789.ns.type.v1~",
                    "gts.x.pkg.verylongnamespacename123456789.type.v1~",
                    "gts.x.pkg.ns.verylongtypename123456789.v1~",
                    (
                        "gts.vendor_with_many_underscores_123."
                        "package_with_many_underscores_456."
                        "namespace_with_many_underscores_789."
                        "type_with_many_underscores_000.v1~"
                    ),
                ]
            }
        ),
    )
    def test_start(self, param):
        super().test_start(param)

    teststeps = [
        Step(
            RunRequest("validate max length segments")
            .get("/validate-id")
            .with_params(**{"gts_id": "${id}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.valid", True)
        ),
    ]


class TestCaseTestOp1IdValidation_VersionEdgeCases(HttpRunner):
    """OP#1 Extended - Version number edge cases"""
    config = Config(
        "OP#1 Extended - Version Edge Cases"
    ).base_url(
        get_gts_base_url()
    )

    @pytest.mark.parametrize(
        "param",
        Parameters(
            {
                "id": [
                    "gts.x.pkg.ns.type.v999999~",
                    "gts.x.pkg.ns.type.v1.999999~",
                    "gts.x.pkg.ns.type.v0.0~",
                    "gts.x.pkg.ns.type.v0.1~",
                    "gts.x.pkg.ns.type.v0~",
                ]
            }
        ),
    )
    def test_start(self, param):
        super().test_start(param)

    teststeps = [
        Step(
            RunRequest("validate version edge cases")
            .get("/validate-id")
            .with_params(**{"gts_id": "${id}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.valid", True)
        ),
    ]


class TestCaseTestOp1IdValidation_UnderscorePlaceholder(HttpRunner):
    """OP#1 Extended - Underscore placeholder usage"""
    config = Config(
        "OP#1 Extended - Underscore Placeholder"
    ).base_url(
        get_gts_base_url()
    )

    @pytest.mark.parametrize(
        "param",
        Parameters(
            {
                "id": [
                    "gts.vendor.pkg._.type.v1~",
                    "gts._.pkg.ns.type.v1~",
                    "gts.vendor._.ns.type.v1~",
                    "gts.vendor.pkg.ns._.v1~",
                    "gts.vendor_name.pkg_name.ns_name.type_name.v1~",
                ]
            }
        ),
    )
    def test_start(self, param):
        super().test_start(param)

    teststeps = [
        Step(
            RunRequest("validate underscore usage")
            .get("/validate-id")
            .with_params(**{"gts_id": "${id}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.valid", True)
        ),
    ]


class TestCaseTestOp1IdValidation_InvalidVersionFormats(HttpRunner):
    """OP#1 Extended - Invalid version formats"""
    config = Config(
        "OP#1 Extended - Invalid Version Formats"
    ).base_url(
        get_gts_base_url()
    )

    @pytest.mark.parametrize(
        "param",
        Parameters(
            {
                "id": [
                    "gts.x.pkg.ns.type.v01~",
                    "gts.x.pkg.ns.type.v1.01~",
                    "gts.x.pkg.ns.type.v001.001~",
                    "gts.x.pkg.ns.type.v-1~",
                    "gts.x.pkg.ns.type.v1.-1~",
                    "gts.x.pkg.ns.type.v1.2.3~",
                    "gts.x.pkg.ns.type.~",
                    "gts.x.pkg.ns.type.V1~",
                    "gts.x.pkg.ns.type.version1~",
                ]
            }
        ),
    )
    def test_start(self, param):
        super().test_start(param)

    teststeps = [
        Step(
            RunRequest("validate invalid version formats")
            .get("/validate-id")
            .with_params(**{"gts_id": "${id}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.valid", False)
        ),
    ]


class TestCaseTestOp1IdValidation_InvalidSegmentFormats(HttpRunner):
    """OP#1 Extended - Invalid segment formats"""
    config = Config(
        "OP#1 Extended - Invalid Segment Formats"
    ).base_url(
        get_gts_base_url()
    )

    @pytest.mark.parametrize(
        "param",
        Parameters(
            {
                "id": [
                    "gts.1vendor.pkg.ns.type.v1~",
                    "gts.vendor.2pkg.ns.type.v1~",
                    "gts.vendor.pkg.3ns.type.v1~",
                    "gts.vendor.pkg.ns.4type.v1~",
                    "gts.vendor-name.pkg.ns.type.v1~",
                    "gts.vendor.pkg.name.space.type.v1~",
                    "gts.vendor.pkg.ns.type@name.v1~",
                    "gts..pkg.ns.type.v1~",
                    "gts.vendor..ns.type.v1~",
                    "gts.Vendor.pkg.ns.type.v1~",
                    "gts.vendor.Pkg.ns.type.v1~",
                ]
            }
        ),
    )
    def test_start(self, param):
        super().test_start(param)

    teststeps = [
        Step(
            RunRequest("validate invalid segment formats")
            .get("/validate-id")
            .with_params(**{"gts_id": "${id}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.valid", False)
        ),
    ]


class TestCaseIssueOp1SingleSegmentInstancesProhibited(HttpRunner):
    """
    Issue #37: Well-known instances without left-hand type segment must be prohibited.

    Single-segment instance IDs (e.g., gts.x.pkg.ns.type.v1) are now invalid.
    Instance IDs MUST be chained with at least one type segment.
    """
    config = Config(
        "Issue #37 - Single-segment instance IDs must be rejected"
    ).base_url(
        get_gts_base_url()
    )

    @pytest.mark.parametrize(
        "param",
        Parameters(
            {
                "id": [
                    # Single-segment instance IDs (no trailing ~) - all should be INVALID
                    "gts.x.test1.events.type.v1",
                    "gts.x.test1.objects_registry.object_a.v1.0",
                    "gts.abc.commerce.orders.order.v2.15",
                    "gts.vendor.pkg.ns.type.v0",
                    "gts.v123.p456.n789.t000.v999.888",
                    "gts.x.pkg._.type.v1",
                    "gts.myvendor.mypackage.mynamespace.mytype.v1.0",
                    "gts.vendor_name.pkg_123.ns_abc.type_xyz.v10.5",
                    "gts.x.test1.api.endpoint.v0.1",
                    "gts.a1.b2.c3.d4.v100.200",
                ]
            }
        ),
    )
    def test_start(self, param):
        super().test_start(param)

    teststeps = [
        Step(
            RunRequest("validate single-segment instance IDs are rejected")
            .get("/validate-id")
            .with_params(**{"gts_id": "${id}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.id", "${id}")
            .assert_equal("body.valid", False)
            .assert_not_equal("body.error", "")
        ),
    ]


class TestCaseIssueOp1ChainedInstancesValid(HttpRunner):
    """
    Issue #37: Chained instance IDs (with left-hand type segment) are valid.

    Instance IDs with at least 2 segments (type~instance) should be accepted.
    """
    config = Config(
        "Issue #37 - Chained instance IDs must be accepted"
    ).base_url(
        get_gts_base_url()
    )

    @pytest.mark.parametrize(
        "param",
        Parameters(
            {
                "id": [
                    # Chained instance IDs (type~instance) - all should be VALID
                    "gts.x.test1.events.type.v1~abc.app._.custom_event.v1.2",
                    "gts.x.test1.events.type.v1~vendor.app.derived.event.v2.0",
                    "gts.x.core.events.topic.v1~x.commerce._.orders.v1.0",
                    "gts.a.b.c.d.v1~e.f.g.h.v2~i.j.k.l.v3.0",
                    "gts.x.test1.events.type.v1~a.b.c.d.v1~e.f.g.h.v1~i.j.k.l.v1.0",
                ]
            }
        ),
    )
    def test_start(self, param):
        super().test_start(param)

    teststeps = [
        Step(
            RunRequest("validate chained instance IDs are accepted")
            .get("/validate-id")
            .with_params(**{"gts_id": "${id}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.id", "${id}")
            .assert_equal("body.valid", True)
        ),
    ]


class TestCaseOp1WildcardEdgeCasesInvalid(HttpRunner):
    """OP#1 - Wildcard edge cases that should be rejected"""
    config = Config(
        "OP#1 - Wildcard edge cases (invalid)"
    ).base_url(
        get_gts_base_url()
    )

    @pytest.mark.parametrize(
        "param",
        Parameters(
            {
                "id": [
                    # a) '*' not at end of pattern
                    "gts.a.b.c.d.v1~a.*~",
                    # b) '*' not at token boundary
                    "gts.a.b.c.d.v1~a*",
                    # d) '*' in the middle of a type segment
                    "gts.a.b.c.*.v1~a.*",
                ]
            }
        ),
    )
    def test_start(self, param):
        super().test_start(param)

    teststeps = [
        Step(
            RunRequest("validate wildcard invalid cases")
            .get("/validate-id")
            .with_params(**{"gts_id": "${id}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.id", "${id}")
            .assert_equal("body.valid", False)
            .assert_equal("body.is_wildcard", True)
            .assert_not_equal("body.error", "")
        ),
    ]


class TestCaseOp1WildcardEdgeCasesValid(HttpRunner):
    """OP#1 - Wildcard edge cases that should be accepted"""
    config = Config(
        "OP#1 - Wildcard edge cases (valid)"
    ).base_url(
        get_gts_base_url()
    )

    @pytest.mark.parametrize(
        "param",
        Parameters(
            {
                "id": [
                    # c) wildcard at token boundary at the end
                    "gts.a.b.c.d.v1~a.*",
                ]
            }
        ),
    )
    def test_start(self, param):
        super().test_start(param)

    teststeps = [
        Step(
            RunRequest("validate wildcard valid case")
            .get("/validate-id")
            .with_params(**{"gts_id": "${id}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.id", "${id}")
            .assert_equal("body.valid", True)
            .assert_equal("body.is_wildcard", True)
        ),
    ]
