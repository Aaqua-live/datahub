import logging

from kafka import KafkaAdminClient

import datahub.emitter.mce_builder as builder
from datahub.configuration.common import ConfigModel
from datahub.configuration.kafka import KafkaConsumerConnectionConfig
from datahub.ingestion.api.common import PipelineContext
from datahub.ingestion.transformer.dataset_transformer import DatasetTransformer
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    DatasetSnapshotClass,
    MetadataChangeEventClass,
)
from pydantic.class_validators import validator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AddKafkaConsumersConfig(ConfigModel):
    connection: KafkaConsumerConnectionConfig = KafkaConsumerConnectionConfig()
    replace_existing: bool = False

    @validator("connection", pre=True)
    def validate_consumer_config(cls, conn):
        assert "consumer_config" in conn, "consumer_config is missing in connection"
        assert (
            "security.protocol" in conn["consumer_config"]
        ), "security.protocol is missing in consumer_config"
        assert (
            "sasl.mechanism" in conn["consumer_config"]
        ), "sasl.mechanism is missing in consumer_config"
        if conn["consumer_config"]["sasl.mechanism"] == "PLAIN":
            assert (
                "sasl.username" in conn["consumer_config"]
            ), "sasl.username is missing in consumer_config"
            assert (
                "sasl.password" in conn["consumer_config"]
            ), "sasl.password is missing in consumer_config"
        return conn


class AddKafkaConsumersTransformer(DatasetTransformer):
    """
    Transformer that can be used to set kafka consumer information
    in properties
    """

    ctx: PipelineContext
    config: AddKafkaConsumersConfig

    def __init__(self, config: AddKafkaConsumersConfig, ctx: PipelineContext):
        self.ctx = ctx
        self.config = config
        self.admin_client = KafkaAdminClient(
            **AddKafkaConsumersTransformer.convert_to_kafka_python(self.config.connection.dict())
        )
        logger.info("Finished creating Admin Client")
        self.consumer_topics = dict()
        self.fetch_consumer_info()

    @classmethod
    def create(
        cls, config_dict: dict, ctx: PipelineContext
    ) -> "AddKafkaConsumersTransformer":
        config = AddKafkaConsumersConfig.parse_obj(config_dict)
        return cls(config, ctx)

    @staticmethod
    def convert_to_kafka_python(conn) -> dict:
        kafka_python_conn = dict()
        kafka_python_conn["bootstrap_servers"] = conn["bootstrap"]
        kafka_python_conn["security_protocol"] = conn["consumer_config"][
            "security.protocol"
        ]
        kafka_python_conn["sasl_mechanism"] = conn["consumer_config"]["sasl.mechanism"]
        if conn["consumer_config"]["sasl.mechanism"] == "PLAIN":
            kafka_python_conn["sasl_plain_username"] = conn["consumer_config"][
                "sasl.username"
            ]
            kafka_python_conn["sasl_plain_password"] = conn["consumer_config"][
                "sasl.password"
            ]
        return kafka_python_conn

    def fetch_consumer_info(self) -> None:
        consumer_groups = self.admin_client.list_consumer_groups()
        consumer_group_ids = [item[0] for item in consumer_groups if item[0] != ""]
        details = self.admin_client.describe_consumer_groups(consumer_group_ids)
        for detail in details:
            for member in detail.members:
                for subscription in member.member_metadata.subscription:
                    if subscription not in self.consumer_topics:
                        self.consumer_topics[subscription] = set()
                    self.consumer_topics[subscription].add(detail.group)

    def transform_one(self, mce: MetadataChangeEventClass) -> MetadataChangeEventClass:
        if not isinstance(mce.proposedSnapshot, DatasetSnapshotClass):
            return mce

        topic = (
            mce.proposedSnapshot.urn.replace("urn:li:dataset:(", "")
            .replace(")", "")
            .split(",")[1]
        )
        if topic not in self.consumer_topics:
            logger.info(f"No consumer Info found for {topic}")
            return mce

        properties = builder.get_or_add_aspect(
            mce,
            DatasetPropertiesClass(
                customProperties={},
            ),
        )

        if self.config.replace_existing:
            properties.customProperties = {}

        properties.customProperties["consumers"] = ", ".join(
            sorted(list(self.consumer_topics[topic]))
        )
        return mce
