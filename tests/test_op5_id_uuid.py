from .conftest import get_gts_base_url
from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseTestOp5IdToUuid_Type(HttpRunner):
    config = Config("OP#5 - ID to UUID (type)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    # Use UUID5 like:
    # import uuid
    # GTS_NS = uuid.uuid5(uuid.NAMESPACE_URL, "gts")
    # val = uuid.uuid5(GTS_NS, "gts.x.test5.events.type.v1~")
    # print(val)

    teststeps = [
        Step(
            RunRequest("uuid mapping (type)")
            .get("/uuid")
            .with_params(**{"gts_id": "gts.x.test5.events.type.v1~"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.id", "gts.x.test5.events.type.v1~")
            .assert_equal("body.uuid", "de567dcc-10ef-597d-8f82-3c999ed9b979")
        ),
        Step(
            RunRequest("uuid mapping deterministic (type)")
            .get("/uuid")
            .with_params(**{"gts_id": "gts.x.test5.events.type.v1.1~"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.uuid", "b9a18e35-890b-586c-81fa-a156b9a26e2b")
        ),
    ]


class TestCaseTestOp5IdToUuid_Instance(HttpRunner):
    config = Config("OP#5 - ID to UUID (instance)").base_url(get_gts_base_url())

    def test_start(self):
        super().test_start()

    teststeps = [
        Step(
            RunRequest("uuid mapping (instance)")
            .get("/uuid")
            .with_params(
                **{
                    "gts_id": (
                        "gts.x.test5.events.type.v1~abc.app._."
                        "custom_event.v1.2"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal(
                "body.id",
                "gts.x.test5.events.type.v1~abc.app._.custom_event.v1.2",
            )
            .assert_equal("body.uuid", "c7f8cca7-3af6-58af-b72b-3febfd93f1a8")
        ),
        Step(
            RunRequest("uuid mapping (combined anonymous instance)")
            .get("/uuid")
            .with_params(
                **{
                    "gts_id": (
                        "gts.x.core.events.type.v1~"
                        "x.commerce.orders.order_placed.v1.0~"
                        "7a1d2f34-5678-49ab-9012-abcdef123456"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal(
                "body.id",
                (
                    "gts.x.core.events.type.v1~"
                    "x.commerce.orders.order_placed.v1.0~"
                    "7a1d2f34-5678-49ab-9012-abcdef123456"
                ),
            )
            .assert_equal("body.uuid", "7a1d2f34-5678-49ab-9012-abcdef123456")
        ),
        Step(
            RunRequest("uuid mapping deterministic (instance)")
            .get("/uuid")
            .with_params(
                **{
                    "gts_id": (
                        "gts.x.test5.events.type.v1~abc.app._."
                        "custom_event.v1.2"
                    )
                }
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.uuid", "c7f8cca7-3af6-58af-b72b-3febfd93f1a8")
        ),
    ]
