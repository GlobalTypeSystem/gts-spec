from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseTestOp7SchemaGraph_ValidChain(HttpRunner):
    """OP#7 - Relationship Resolution: Build schema graph for valid chain"""
    config = Config("OP#7 - Schema Graph (valid chain)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register base event schema
        Step(
            RunRequest("register base event schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test7.events.type.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id", "type", "tenantId", "occurredAt"],
                "properties": {
                    "type": {"type": "string"},
                    "id": {"type": "string", "format": "uuid"},
                    "tenantId": {"type": "string", "format": "uuid"},
                    "occurredAt": {"type": "string", "format": "date-time"},
                    "payload": {"type": "object"}
                },
                "additionalProperties": False
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register derived event schema
        Step(
            RunRequest("register derived event schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test7.events.type.v1~"
                    "x.test7.graph.event.v1.0~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test7.events.type.v1~"},
                    {
                        "type": "object",
                        "required": ["type", "payload"],
                        "properties": {
                            "type": {
                                "const": (
                                    "gts.x.test7.events.type.v1~"
                                    "x.test7.graph.event.v1.0~"
                                )
                            },
                            "payload": {
                                "type": "object",
                                "required": ["testField"],
                                "properties": {
                                    "testField": {"type": "string"}
                                }
                            }
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Build schema graph
        Step(
            RunRequest("build schema graph")
            .get("/resolve-relationships")
            .with_params(
                **{
                    "gts_id": (
                        "gts.x.test7.events.type.v1~x.test7.graph.event.v1.0~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


class TestCaseTestOp7SchemaGraph_BrokenReference(HttpRunner):
    """OP#7 - Relationship Resolution: Detect broken reference"""
    config = Config("OP#7 - Schema Graph (broken reference)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register schema with broken reference
        Step(
            RunRequest("register schema with broken reference")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test7.broken.schema.v1.0~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.nonexistent.base.type.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Build schema graph - should detect broken reference
        Step(
            RunRequest("build schema graph with broken reference")
            .get("/resolve-relationships")
            .with_params(**{"gts_id": "gts.x.test7.broken.schema.v1.0~"})
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


class TestCaseTestOp7SchemaGraph_RefPlainGtsPrefix(HttpRunner):
    """OP#7 - Reject $ref that starts with 'gts.' instead of 'gts://'"""

    config = Config("OP#7 - Schema Graph ($$ref plain gts prefix)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with plain gts. $ref should fail")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.test7.invalid_ref.plain_prefix.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": "gts.x.test7.invalid_ref.plain_prefix.v1~"
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseTestOp7SchemaGraph_RefWildcardGts(HttpRunner):
    """OP#7 - Reject $ref using wildcards after gts://"""

    config = Config("OP#7 - Schema Graph ($$ref wildcard gts://)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with wildcard gts:// $ref should fail")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.test7.invalid_ref.wildcard.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": "gts://gts.x.test7.events.*.v1~"
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseTestOp7SchemaGraph_LocalRefAllowed(HttpRunner):
    """OP#7 - Relationship Resolution: Allow local JSON Schema $ref"""
    config = Config("OP#7 - Schema Graph (local $$ref allowed)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with local $ref should succeed")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.test7.local_ref.allowed.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "$$defs": {
                    "Base": {
                        "type": "object",
                        "properties": {"id": {"type": "string"}},
                        "required": ["id"],
                        "additionalProperties": False
                    }
                },
                "allOf": [
                    {"$$ref": "#/$$defs/Base"}
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


class TestCaseTestOp7SchemaGraph_RefNotGtsUri(HttpRunner):
    """OP#7 - Reject non-GTS external $ref"""
    config = Config("OP#7 - Schema Graph ($$ref not gts://...)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with non-GTS $ref should fail")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.test7.invalid_ref.not_gts_uri.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": "https://example.com/schemas/base.json"
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseTestOp7SchemaGraph_RefMalformedGts(HttpRunner):
    """OP#7 - Reject malformed GTS $ref"""
    config = Config("OP#7 - Schema Graph (malformed GTS in $$ref)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("register schema with malformed GTS $ref should fail")
            .post("/entities")
            .with_params(**{"validate": "true"})
            .with_json({
                "$$id": "gts://gts.x.test7.invalid_ref.malformed_gts.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        # invalid segment token: hyphen is not allowed
                        "$$ref": "gts://gts.x.bad-seg.ns.type.v1~"
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 422)
        ),
    ]


class TestCaseTestOp7SchemaGraph_ComplexChain(HttpRunner):
    """OP#7 - Relationship Resolution: Multi-level inheritance chain"""
    config = Config("OP#7 - Schema Graph (complex chain)").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register base schema
        Step(
            RunRequest("register base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.test7.base.type.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register level 1 derived schema
        Step(
            RunRequest("register level 1 derived schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test7.base.type.v1~"
                    "x.test7.derived1.type.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.test7.base.type.v1~"},
                    {
                        "type": "object",
                        "required": ["field1"],
                        "properties": {
                            "field1": {"type": "string"}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register level 2 derived schema
        Step(
            RunRequest("register level 2 derived schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.test7.base.type.v1~"
                    "x.test7.derived1.type.v1~"
                    "x.test7.derived2.type.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.test7.base.type.v1~"
                            "x.test7.derived1.type.v1~"
                        )
                    },
                    {
                        "type": "object",
                        "required": ["field2"],
                        "properties": {
                            "field2": {"type": "string"}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Build schema graph for complex chain
        Step(
            RunRequest("build schema graph for complex chain")
            .get("/resolve-relationships")
            .with_params(
                **{
                    "gts_id": (
                        "gts.x.test7.base.type.v1~"
                        "x.test7.derived1.type.v1~"
                        "x.test7.derived2.type.v1~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


class TestCaseTestOp7Relationship_DeepInheritanceChain(HttpRunner):
    """Test resolution of deep inheritance chains (5 levels)"""
    config = Config("OP#7 Extended - Deep Inheritance Chain").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register base schema (level 1)
        Step(
            RunRequest("register base schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.base.entity.root.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register level 2
        Step(
            RunRequest("register level 2 schema")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.base.entity.root.v1~x.l2._.type.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.base.entity.root.v1~"},
                    {
                        "properties": {
                            "level": {"type": "integer", "const": 2}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register level 3
        Step(
            RunRequest("register level 3 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.base.entity.root.v1~"
                    "x.l2._.type.v1~"
                    "x.l3._.type.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.base.entity.root.v1~"
                            "x.l2._.type.v1~"
                        )
                    },
                    {
                        "properties": {
                            "level": {"type": "integer", "const": 3}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register level 4
        Step(
            RunRequest("register level 4 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.base.entity.root.v1~"
                    "x.l2._.type.v1~"
                    "x.l3._.type.v1~"
                    "x.l4._.type.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.base.entity.root.v1~"
                            "x.l2._.type.v1~"
                            "x.l3._.type.v1~"
                        )
                    },
                    {
                        "properties": {
                            "level": {"type": "integer", "const": 4}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register level 5
        Step(
            RunRequest("register level 5 schema")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.base.entity.root.v1~"
                    "x.l2._.type.v1~"
                    "x.l3._.type.v1~"
                    "x.l4._.type.v1~"
                    "x.l5._.type.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.base.entity.root.v1~"
                            "x.l2._.type.v1~"
                            "x.l3._.type.v1~"
                            "x.l4._.type.v1~"
                        )
                    },
                    {
                        "properties": {
                            "level": {"type": "integer", "const": 5}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Resolve the deep chain
        Step(
            RunRequest("resolve deep inheritance chain")
            .get("/resolve-relationships")
            .with_params(
                **{
                    "gts_id": (
                        "gts.x.base.entity.root.v1~"
                        "x.l2._.type.v1~"
                        "x.l3._.type.v1~"
                        "x.l4._.type.v1~"
                        "x.l5._.type.v1~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


class TestCaseTestOp7Relationship_CrossPackageReferences(HttpRunner):
    """Test relationship resolution across different packages"""
    config = Config("OP#7 Extended - Cross-Package References").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register base in package A
        Step(
            RunRequest("register base in package A")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.package_a.core.base.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["baseId"],
                "properties": {
                    "baseId": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register derived in package B referencing package A
        Step(
            RunRequest("register derived in package B")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.package_a.core.base.v1~"
                    "x.package_b._.derived.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.package_a.core.base.v1~"},
                    {
                        "properties": {
                            "derivedField": {"type": "string"}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Register further derived in package C
        Step(
            RunRequest("register derived in package C")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.package_a.core.base.v1~"
                    "x.package_b._.derived.v1~"
                    "x.package_c._.extended.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.package_a.core.base.v1~"
                            "x.package_b._.derived.v1~"
                        )
                    },
                    {
                        "properties": {
                            "extendedField": {"type": "string"}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Resolve cross-package relationships
        Step(
            RunRequest("resolve cross-package relationships")
            .get("/resolve-relationships")
            .with_params(
                **{
                    "gts_id": (
                        "gts.x.package_a.core.base.v1~"
                        "x.package_b._.derived.v1~"
                        "x.package_c._.extended.v1~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


class TestCaseTestOp7Relationship_MultiVendorChain(HttpRunner):
    """Test relationship resolution across multiple vendors"""
    config = Config("OP#7 Extended - Multi-Vendor Chain").base_url(
        get_gts_base_url()
    )

    def test_start(self):
        super().test_start()

    teststeps = [
        # Register base by vendor X
        Step(
            RunRequest("register base by vendor X")
            .post("/entities")
            .with_json({
                "$$id": "gts://gts.x.platform.events.base.v1~",
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["eventId", "timestamp"],
                "properties": {
                    "eventId": {"type": "string"},
                    "timestamp": {"type": "string"}
                }
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Vendor ABC extends X's base
        Step(
            RunRequest("vendor ABC extends base")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.platform.events.base.v1~"
                    "abc.app._.custom_event.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {"$$ref": "gts://gts.x.platform.events.base.v1~"},
                    {
                        "properties": {
                            "vendorData": {"type": "object"}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Vendor XYZ extends ABC's type
        Step(
            RunRequest("vendor XYZ extends ABC type")
            .post("/entities")
            .with_json({
                "$$id": (
                    "gts://gts.x.platform.events.base.v1~"
                    "abc.app._.custom_event.v1~"
                    "xyz.plugin._.specialized.v1~"
                ),
                "$$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "allOf": [
                    {
                        "$$ref": (
                            "gts://gts.x.platform.events.base.v1~"
                            "abc.app._.custom_event.v1~"
                        )
                    },
                    {
                        "properties": {
                            "specializedField": {"type": "string"}
                        }
                    }
                ]
            })
            .validate()
            .assert_equal("status_code", 200)
        ),
        # Resolve multi-vendor chain
        Step(
            RunRequest("resolve multi-vendor chain")
            .get("/resolve-relationships")
            .with_params(
                **{
                    "gts_id": (
                        "gts.x.platform.events.base.v1~"
                        "abc.app._.custom_event.v1~"
                        "xyz.plugin._.specialized.v1~"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]


if __name__ == "__main__":
    TestCaseTestOp7SchemaGraph_ValidChain().test_start()
