import logging
import os
import time

import pytest

from tests.test_helpers.docker_helpers import docker_compose_runner  # noqa: F401
from kafka.structs import (
    MemberInformation,
    GroupInformation,
)
from kafka.coordinator.protocol import (
    ConsumerProtocolMemberMetadata,
    ConsumerProtocolMemberAssignment,
)

# Enable debug logging.
logging.getLogger().setLevel(logging.DEBUG)
os.putenv("DATAHUB_DEBUG", "1")


@pytest.fixture
def mock_time(monkeypatch):
    def fake_time():
        return 1615443388.0975091

    monkeypatch.setattr(time, "time", fake_time)

    yield

@pytest.fixture
def get_kafka_connection_props():
    return {
        "connection": {
            "bootstrap": "kafka.cloud:9092",
            "consumer_config": {
                "security.protocol": "SASL_SSL",
                "sasl.mechanism": "PLAIN",
                "sasl.username": "sasl_username",
                "sasl.password": "sasl_password",
            },
        }
    }


@pytest.fixture
def mock_list_consumer_groups():
    return [
        ("", ""),
        ("consumer_group_1", "consumer"),
        ("consumer_group_2", "consumer"),
        ("consumer_group_3", "consumer"),
    ]


@pytest.fixture
def mock_describe_consumer_groups_1_consumer():
    return [
        GroupInformation._make(
            [0, "consumer_group_1", "Empty", "consumer", "", [], None]
        ),
        GroupInformation._make(
            [
                0,
                "consumer_group_2",
                "Empty",
                "consumer",
                "",
                [
                    MemberInformation._make(
                        [
                            "consumer_group_member_2",
                            "test_client",
                            "/0.0.0.0",
                            ConsumerProtocolMemberMetadata(0, ["test-topic-1"], None),
                            ConsumerProtocolMemberAssignment(
                                0, [("test-topic", [0, 1, 2, 3, 4, 5])], None
                            ),
                        ]
                    )
                ],
                None,
            ]
        ),
        GroupInformation._make(
            [0, "consumer_group_3", "Empty", "consumer", "", [], None]
        ),
    ]


@pytest.fixture
def mock_describe_consumer_groups_2_consumer():
    return [
        GroupInformation._make(
            [0, "consumer_group_1", "Empty", "consumer", "", [], None]
        ),
        GroupInformation._make(
            [
                0,
                "consumer_group_2",
                "Empty",
                "consumer",
                "",
                [
                    MemberInformation._make(
                        [
                            "consumer_group_member_2",
                            "test_client",
                            "/0.0.0.0",
                            ConsumerProtocolMemberMetadata(0, ["test-topic-1"], None),
                            ConsumerProtocolMemberAssignment(
                                0, [("test-topic", [0, 1, 2, 3, 4, 5])], None
                            ),
                        ]
                    )
                ],
                None,
            ]
        ),
        GroupInformation._make(
            [
                0,
                "consumer_group_3",
                "Empty",
                "consumer",
                "",
                [
                    MemberInformation._make(
                        [
                            "consumer_group_member_3",
                            "test_client",
                            "/0.0.0.0",
                            ConsumerProtocolMemberMetadata(0, ["test-topic-1"], None),
                            ConsumerProtocolMemberAssignment(
                                0, [("test-topic", [0, 1, 2, 3, 4, 5])], None
                            ),
                        ]
                    )
                ],
                None,
            ]
        ),
    ]


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden-files",
        action="store_true",
        default=False,
    )
