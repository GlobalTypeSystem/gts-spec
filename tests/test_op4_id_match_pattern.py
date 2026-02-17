import pytest
from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


# Positive cases (3)
class TestCaseTestOp4WildcardMatch_Positive_1(HttpRunner):
    config = Config("OP#4 - Wildcard Match (pos 1)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("wildcard pattern match (pos 1)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "candidate": (
                        "gts.x.test4.events.type.v1~abc.app._."
                        "custom_event.v1.2"
                    ),
                    "pattern": "gts.x.test4.events.type.v1~abc.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
    ]


class TestCaseTestOp4Wildcard_VersionWildcards(HttpRunner):
    config = Config("OP#4 Extended - Version Wildcard Matching").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("wildcard pattern match (any minor version)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.x.pkg.ns.type.v1~",
                    "candidate": "gts.x.pkg.ns.type.v1.5~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("wildcard pattern match (any minor version)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.x.pkg.ns.type.v1~a.b.c.*",
                    "candidate": "gts.x.pkg.ns.type.v1.5~a.b.c.d.v1",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("wildcard pattern match (any minor version)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.x.pkg.ns.type.v1~a.b.c.d.v1",
                    "candidate": "gts.x.pkg.ns.type.v1.5~a.b.c.d.v1.2",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("wildcard pattern match (specific minor version)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.x.pkg.ns.type.v1.2~",
                    "candidate": "gts.x.pkg.ns.type.v1.2~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("wildcard pattern match (different major versions no match)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.x.pkg.ns.type.v1~",
                    "candidate": "gts.x.pkg.ns.type.v2~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
        ),
    ]


class TestCaseTestOp4Wildcard_ChainedPatterns(HttpRunner):
    config = Config("OP#4 Extended - Chained Pattern Matching").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("match base with wildcard derived")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.x.test4.events.type.v1~abc.*",
                    "candidate": "gts.x.test4.events.type.v1~abc.app._.custom.v1~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("match wildcard in chain middle")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.x.*.events.type.v1~",
                    "candidate": "gts.x.test4.events.type.v1~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
            .assert_not_equal("body.error", None)
            .assert_not_equal("body.error", "")
        ),
    ]


class TestCaseTestOp4Wildcard_MultiLevelWildcards(HttpRunner):
    config = Config("OP#4 Extended - Multi-Level Wildcards").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("wildcard vendor and type")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.*.pkg.ns.*",
                    "candidate": "gts.vendor.pkg.ns.type.v1~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
            .assert_startswith("body.error", "Invalid")
        ),
        Step(
            RunRequest("wildcard all except vendor")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.myvendor.*",
                    "candidate": "gts.myvendor.pkg.ns.type.v1.0~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("match all types in namespace")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.x.pkg.events.*",
                    "candidate": "gts.x.pkg.events.order_placed.v1~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
    ]


class TestCaseTestOp4Wildcard_GlobalPatterns(HttpRunner):
    config = Config("OP#4 Extended - Global wildcard patterns").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("match entire namespace with gts.*")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.*",
                    "candidate": "gts.vendor.pkg.ns.type.v1~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("match vendor prefix with gts.vendor.*")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.vendor.*",
                    "candidate": "gts.vendor.pkg.ns.type.v1~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("match vendor prefix when candidate has wildcard")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.vendor.*",
                    "candidate": "gts.vendor.pkg.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("candidate has minor version, but it matches the pattern")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.a.b.c.d.v1~*",
                    "candidate": "gts.a.b.c.d.v1.0~a.b.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("wildcard match")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.a.b.c.d.v1~*",
                    "candidate": "gts.a.b.c.d.v1.0~a.b.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("wildcard match")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.a.b.c.d.v1~*",
                    "candidate": "gts.a.b.c.d.v1.0~a.b.c.d.v1",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("implicitwildcard match")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.a.b.c.d.v1.1~",
                    "candidate": "gts.a.b.c.d.v1.1~a.b.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("implicitwildcard match")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.a.b.c.d.v1~",
                    "candidate": "gts.a.b.c.d.v1.0~a.b.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("implicit wildcard match")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.a.b.c.d.v1~",
                    "candidate": "gts.a.b.c.d.v1.0~a.b.c.d.v1",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("implicit wildcard match")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.w.x.y.z.v1~",
                    "candidate": "gts.w.x.y.z.v1.0~a.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
        Step(
            RunRequest("reject malformed vendor wildcard")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.vendor*",
                    "candidate": "gts.vendor.pkg.ns.type.v1~a.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
            .assert_not_equal("body.error", "")
        ),
        Step(
            RunRequest("reject malformed vendor wildcard")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.vendor*",
                    "candidate": "gts.vendor.pkg.ns.type.v1~",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
            .assert_not_equal("body.error", "")
        ),
        Step(
            RunRequest("reject malformed vendor wildcard")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.vendor.*",
                    "candidate": "gts.vendor.pkg.ns.type.v1~a*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
            .assert_not_equal("body.error", "")
        ),
        Step(
            RunRequest("reject malformed vendor wildcard")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.vendor.*",
                    "candidate": "gts.vendor.pkg.ns.type.v1~a-b.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
            .assert_not_equal("body.error", "")
        ),
        Step(
            RunRequest("malformed pattern")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.a.b.c.d~",
                    "candidate": "gts.a.b.c.d~a.b.c.d.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
            .assert_not_equal("body.error", "")
        ),
        Step(
            RunRequest("malformed candidate")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.a.b.c.d.v1~",
                    "candidate": "gts.a.b.c.d~a.b.c.d.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
            .assert_not_equal("body.error", "")
        ),
        Step(
            RunRequest("pattern defines explicit minor version only, candidate uses major")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.a.b.c.d.v1.1~*",
                    "candidate": "gts.a.b.c.d.v1~a.b.c.d.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
            .assert_not_equal("body.error", "")
        ),
        Step(
            RunRequest("minor version mismatch")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "pattern": "gts.a.b.c.d.v1.1~*",
                    "candidate": "gts.a.b.c.d.v1.0~a.b.c.d.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
            .assert_not_equal("body.error", "")
        )
    ]


class TestCaseTestOp4WildcardMatch_Positive_2(HttpRunner):
    config = Config("OP#4 - Wildcard Match (pos 2)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("wildcard match (pos 2)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "candidate": "gts.vendor.pkg.ns.type.v0~",
                    "pattern": "gts.vendor.pkg.ns.type.v0~*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
        ),
        Step(
            RunRequest("wildcard match (pos 2)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "candidate": "gts.vendor.pkg.ns.type.v0~a.b.c.d.v1",
                    "pattern": "gts.vendor.pkg.ns.type.v0~*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
    ]


class TestCaseTestOp4WildcardMatch_Positive_3(HttpRunner):
    config = Config("OP#4 - Wildcard Match (pos 3)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("wildcard match (pos 3)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "candidate": "gts.vendor.pkg.ns.type.v0.1~",
                    "pattern": "gts.vendor.pkg.ns.type.v0~*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
        ),
        Step(
            RunRequest("wildcard match (pos 3)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "candidate": "gts.vendor.pkg.ns.type.v0.1~a.b.c.d.v1",
                    "pattern": "gts.vendor.pkg.ns.type.v0~*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", True)
        ),
    ]


# Negative cases (3)
class TestCaseTestOp4WildcardMatch_Negative_1(HttpRunner):
    config = Config("OP#4 - Wildcard Match (neg 1)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("wildcard match (neg 1)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "candidate": (
                        "gts.x.test4.events.type.v1~abc.app._."
                        "custom_event.v1.3"
                    ),
                    "pattern": "gts.x.test4.events.type.v2~abc.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
        ),
    ]


class TestCaseTestOp4WildcardMatch_Negative_2(HttpRunner):
    config = Config("OP#4 - Wildcard Match (neg 2)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("wildcard match (neg 2)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "candidate": "gts.vendor.pkg.ns.type.v1.1~",
                    "pattern": "gts.vendor.pkg.ns.type.v0~*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
        ),
    ]


class TestCaseTestOp4WildcardMatch_Negative_3(HttpRunner):
    config = Config("OP#4 - Wildcard Match (neg 3)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("wildcard match (neg 3)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "candidate": (
                        "gts.x.test4.events.type.v1~abc.app._."
                        "custom_event.v1.2"
                    ),
                    "pattern": "gts.x.test4.events.type.v1~abc",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.match", False)
        ),
    ]


# Invalid patterns (3)
class TestCaseTestOp4WildcardInvalid_1(HttpRunner):
    config = Config("OP#4 - Wildcard Match (invalid 1)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("wildcard match invalid (1)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "candidate": "gts.x.test4.events.type.v1~abc.app._.custom_event.v1.2",
                    "pattern": "GTS.vendor.pkg.ns.type.v0.*",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_not_equal("body.error", "")
        ),
    ]


class TestCaseTestOp4WildcardInvalid_2(HttpRunner):
    config = Config("OP#4 - Wildcard Match (invalid 2)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("wildcard match invalid (2)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "candidate": "gts.vendor.pkg.ns.type.v0~",
                    "pattern": "gts.x.test4.events.type.v1*abc",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_not_equal("body.error", "")
        ),
    ]


class TestCaseTestOp4WildcardInvalid_3(HttpRunner):
    config = Config("OP#4 - Wildcard Match (invalid 3)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("wildcard match invalid (3)")
            .get("/match-id-pattern")
            .with_params(
                **{
                    "candidate": "gts.vendor.pkg.ns.type.v0~",
                    "pattern": "gts.x.test4.events.type",
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_not_equal("body.error", "")
        ),
    ]
