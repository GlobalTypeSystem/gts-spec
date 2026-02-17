from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


# Helper function to register test entities
def register_test_entities():
    return [
        Step(
            RunRequest("register entity 1")
            .post("/entities")
            .with_json({
                "id": "gts.x.test10.query.event.v1.0~a.b.c.d.v1",
                "type": "gts.x.test10.query.event.v1.0~",
                "eventId": "evt-001",
                "status": "active",
                "category": "order"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register entity 2")
            .post("/entities")
            .with_json({
                "id": "gts.x.test10.query.event.v1.1~a.b.c.d.v2",
                "type": "gts.x.test10.query.event.v1.1~",
                "eventId": "evt-002",
                "status": "inactive",
                "category": "payment"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register entity 3")
            .post("/entities")
            .with_json({
                "id": "gts.x.test10.query.event.v2.2~a.b.c.d.v1~a.b.c.d.v2",
                "type": "gts.x.test10.query.event.v2.2~a.b.c.d.v1~",
                "eventId": "evt-003",
                "status": "active",
                "category": "email"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register entity 4")
            .post("/entities")
            .with_json({
                "id": "gts.x.test10.other_namespace.notification.v1.0~a.b.c.d.v1",
                "type": "gts.x.test10.other_namespace.notification.v1.0~",
                "eventId": "evt-003",
                "status": "some",
                "category": "email"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register entity 5")
            .post("/entities")
            .with_json({
                "id": "gts.x.test10_2.commerce.order.v2.0~a.b.c.d.v1",
                "type": "gts.x.test10_2.commerce.order.v2.0~",
                "eventId": "evt-004",
                "status": "active",
                "category": "order"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


# 1. Exact match

class TestCaseTestOp10Query_ExactMatch(HttpRunner):
    """OP#10 - Query Execution: Exact ID match"""
    config = Config("OP#10 - Query (exact match)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query for exact match
        Step(
            RunRequest("query exact match")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10.query.event.v1.0~a.b.c.d.v1"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 1)
        ),
    ]


# 2. Invalid query

class TestCaseTestOp10Query_InvalidQuery1(HttpRunner):
    """OP#10 - Query Execution: Invalid query 1 (partial GTS ID w/o wildcard)"""
    config = Config("OP#10 - Query (invalid query 1)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query for specific version
        Step(
            RunRequest("query specific version")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10.query"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_contains("body.error", "Invalid query")
        ),
    ]


class TestCaseTestOp10Query_InvalidQuery2(HttpRunner):
    """OP#10 - Query Execution: Invalid query 2 (missing namespace)"""
    config = Config("OP#10 - Query (invalid query 2)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query for specific version
        Step(
            RunRequest("query specific version")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10..query.v1"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_contains("body.error", "Invalid query")
        ),
    ]


class TestCaseTestOp10Query_InvalidQuery3(HttpRunner):
    """OP#10 - Query Execution: Invalid query 3 (incomplete version)"""
    config = Config("OP#10 - Query (invalid query 3)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query for specific version
        Step(
            RunRequest("query specific version")
            .get("/query")
            .with_params(**{"expr": "gtsa.x.test10._.query.v"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_contains("body.error", "Invalid query")
        ),
    ]


class TestCaseTestOp10Query_InvalidQuery4(HttpRunner):
    """OP#10 - Query Execution: Invalid query 4 (no version)"""
    config = Config("OP#10 - Query (invalid query 4)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query for specific version
        Step(
            RunRequest("query specific version")
            .get("/query")
            .with_params(**{"expr": "gtsa.x.test10._.query.v1~a.b.c.d"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_contains("body.error", "Invalid query")
        ),
    ]


# 3. Wildcard match

class TestCaseTestOp10Query_WildcardPackage(HttpRunner):
    """OP#10 - Query Execution: Wildcard vendor match"""
    config = Config("OP#10 - Query (wildcard vendor)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with wildcard for all x vendor entities
        Step(
            RunRequest("query wildcard vendor")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10.*", "limit": 50})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 4)
            .assert_equal("body.limit", 50)
        ),
    ]


class TestCaseTestOp10Query_WildcardPackageWithLimit(HttpRunner):
    """OP#10 - Query Execution: Wildcard vendor match"""
    config = Config("OP#10 - Query (wildcard vendor)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with wildcard for all x vendor entities
        Step(
            RunRequest("query wildcard vendor")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10.*", "limit": 2})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 2)
            .assert_equal("body.limit", 2)
        ),
    ]


class TestCaseTestOp10Query_WildcardNamespace(HttpRunner):
    """OP#10 - Query Execution: Wildcard namespace match"""
    config = Config("OP#10 - Query (wildcard namespace)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with wildcard for specific package
        Step(
            RunRequest("query wildcard package")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10.query.*"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 3)
        ),
    ]


class TestCaseTestOp10Query_WildcardType(HttpRunner):
    """OP#10 - Query Execution: Wildcard type match"""
    config = Config("OP#10 - Query (wildcard type)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with wildcard for specific type pattern
        Step(
            RunRequest("query wildcard type")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10.query.event.*"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 3)
        ),
    ]


class TestCaseTestOp10Query_WildcardMajorVersion(HttpRunner):
    """OP#10 - Query Execution: Wildcard major version match"""
    config = Config("OP#10 - Query (wildcard major version)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with wildcard for specific type pattern
        Step(
            RunRequest("query wildcard type")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10.query.event.v2.*"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 1)
        ),
    ]


class TestCaseTestOp10Query_WildcardMinorVersion(HttpRunner):
    """OP#10 - Query Execution: Wildcard minor version match"""
    config = Config("OP#10 - Query (wildcard minor version)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with wildcard for specific type pattern
        Step(
            RunRequest("query wildcard type")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10.query.event.v1.1~*"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 1)
        ),
    ]


# 4. Wildcard and filter by attribute

class TestCaseTestOp10Query_WildcardAndFilterByAttribute(HttpRunner):
    """OP#10 - Query Execution: Wildcard and filter by attribute"""
    config = Config("OP#10 - Query (wildcard and filter by attribute)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with attribute filter
        Step(
            RunRequest("query with status filter")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10.*[status=active]"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 2)
        ),
    ]


class TestCaseTestOp10Query_MultipleFilters(HttpRunner):
    """OP#10 - Query Execution: Multiple attribute filters"""
    config = Config("OP#10 - Query (multiple filters)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with multiple filters
        Step(
            RunRequest("query with multiple filters")
            .get("/query")
            .with_params(
                **{"expr": 'gts.x.test10.*[status=active, category=order]'}
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 1)
        ),
    ]


class TestCaseTestOp10Query_MultipleFiltersWithQuotes(HttpRunner):
    """OP#10 - Query Execution: Multiple attribute filters with quotes"""
    config = Config("OP#10 - Query (multiple filters with quotes)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with multiple filters
        Step(
            RunRequest("query with multiple filters")
            .get("/query")
            .with_params(
                **{"expr": 'gts.x.test10.*[status="active", category="order"]'}
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 1)
        ),
    ]

class TestCaseTestOp10Query_MultipleFiltersWithWildcard(HttpRunner):
    """OP#10 - Query Execution: Multiple attribute filters with wildcard value"""
    config = Config("OP#10 - Query (multiple filters with wildcard)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with multiple filters including wildcard value
        Step(
            RunRequest("query with multiple filters and wildcard")
            .get("/query")
            .with_params(
                **{"expr": 'gts.x.test10.*[status=active, category=*]'}
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 2)
        ),
    ]


# 5. Invalid query

class TestCaseTestOp10Query_InvalidFilterByAttribute(HttpRunner):
    """OP#10 - Query Execution: Filter by attribute with invalid syntax"""
    config = Config("OP#10 - Query (filter by attribute with invalid syntax)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with attribute filter
        Step(
            RunRequest("query with status filter")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10.*~[status=active]"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_startswith("body.error", "Invalid query")
        ),
    ]


# 6. No matches

class TestCaseTestOp10Query_NoMatches(HttpRunner):
    """OP#10 - Query Execution: No matches"""
    config = Config("OP#10 - Query (no matches)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query that matches nothing
        Step(
            RunRequest("query with no matches")
            .get("/query")
            .with_params(**{"expr": "gts.nonexistent.*"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 0)
        ),
    ]


class TestCaseTestOp10Query_FilterNoMatches(HttpRunner):
    """OP#10 - Query Execution: Filter with no matches"""
    config = Config("OP#10 - Query (filter no matches)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_test_entities() + [
        # Query with filter that matches nothing
        Step(
            RunRequest("query filter with no matches")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10.*[status=nonexisting, category=order]"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 0)
        ),
    ]


# 7. Wildcard Use Cases - Base and Derived Type Matching

# Helper function to register test entities for wildcard use cases
def register_wildcard_usecase_entities():
    """Register entities for testing the 4 wildcard use cases.
    These represent schema definitions themselves:
    - gts.x.test10_llm.chat.message.v1.0~ (base schema)
    - gts.x.test10_llm.chat.message.v1.0~x.test10_llm.system_message.v1.0~ (derived)
    - gts.x.test10_llm.chat.message.v1.1~ (base schema)
    - gts.x.test10_llm.chat.message.v1.1~x.test10_llm.user_message.v1.1~ (derived)
    """
    return [
        Step(
            RunRequest("register base schema v1.0")
            .post("/entities")
            .with_json({
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "$$id": "gts://gts.x.test10_llm.chat.message.v1.0~",
                "type": "object",
                "description": "Base chat message v1.0"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema from v1.0")
            .post("/entities")
            .with_json({
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "$$id": (
                    "gts://gts.x.test10_llm.chat.message.v1.0~"
                    "x.test10_llm._.system_message.v1.0~"
                ),
                "type": "object",
                "description": "System message derived from v1.0",
                "allOf": [
                    {
                        "$$ref": "gts://gts.x.test10_llm.chat.message.v1.0~"
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register base schema v1.1")
            .post("/entities")
            .with_json({
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "$$id": "gts://gts.x.test10_llm.chat.message.v1.1~",
                "type": "object",
                "description": "Base chat message v1.1"
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunRequest("register derived schema from v1.1")
            .post("/entities")
            .with_json({
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "$$id": (
                    "gts://gts.x.test10_llm.chat.message.v1.1~"
                    "x.test10_llm._.user_message.v1.1~"
                ),
                "type": "object",
                "description": "User message derived from v1.1",
                "allOf": [
                    {
                        "$$ref": "gts://gts.x.test10_llm.chat.message.v1.1~"
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


class TestCaseTestOp10Query_UseCase1_DerivedFromV10(HttpRunner):
    """OP#10 - Use Case 1: Find all derived types from v1.0 base schema
    Pattern: gts.x.test10_llm.chat.message.v1.0~*
    Expected: Only gts.x.test10_llm.chat.message.v1.0~x.test10.system_message.v1.0~
    """
    config = Config("OP#10 - Use Case 1 (derived from v1.0)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_wildcard_usecase_entities() + [
        Step(
            RunRequest("query derived types from v1.0")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10_llm.chat.message.v1.0~*"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 1)
        ),
    ]


class TestCaseTestOp10Query_UseCase2_AllVersions(HttpRunner):
    """OP#10 - Use Case 2: Find all base schemas and derived schemas
    Pattern: gts.x.test10_llm.chat.message.*
    Expected: All 4 identifiers (both base schemas and derived types)
    """
    config = Config("OP#10 - Use Case 2 (all versions)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = register_wildcard_usecase_entities() + [
        Step(
            RunRequest("query all versions and derived types")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10_llm.chat.message.*"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 4)
        ),
    ]


class TestCaseTestOp10Query_UseCase3_DerivedFromV1AnyMinor(HttpRunner):
    """OP#10 - Use Case 3: Find all derived types from v1 (any minor)
    Pattern: gts.x.test10_llm.chat.message.v1~*
    Expected: Two derived entities from v1.0 and v1.1
    """
    config = Config(
        "OP#10 - Use Case 3 (derived from v1 any minor)"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = register_wildcard_usecase_entities() + [
        Step(
            RunRequest("query derived types from v1 any minor")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10_llm.chat.message.v1~*"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 2)
        ),
    ]


class TestCaseTestOp10Query_UseCase4_AllV1BaseAndDerived(HttpRunner):
    """OP#10 - Use Case 4: Find all base and derived from v1 (any minor)
    Pattern: gts.x.test10_llm.chat.message.v1.*
    Expected: All 4 identifiers (matches both v1.0~ and v1.1~)
    """
    config = Config(
        "OP#10 - Use Case 4 (all v1 base and derived)"
    ).base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = register_wildcard_usecase_entities() + [
        Step(
            RunRequest("query all v1 base and derived types")
            .get("/query")
            .with_params(**{"expr": "gts.x.test10_llm.chat.message.v1.*"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_length_equal("body.results", 4)
        ),
    ]


if __name__ == "__main__":
    TestCaseTestOp10Query_ExactMatch().test_start()
