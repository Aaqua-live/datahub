from unittest.mock import patch

import pydantic
import pytest

import datahub.emitter.mce_builder as builder
import datahub.metadata.schema_classes as models
from datahub.ingestion.api.common import PipelineContext, RecordEnvelope
from datahub.ingestion.transformer.enrich_kafka_transformer import (
    AddKafkaConsumersConfig,
    AddKafkaConsumersTransformer,
)


def make_kafka_dataset(topic_name):
    return models.MetadataChangeEventClass(
        proposedSnapshot=models.DatasetSnapshotClass(
            urn=f"urn:li:dataset:(urn:li:dataPlatform:kafka,{topic_name},PROD)",
            aspects=[
                models.StatusClass(removed=False),
            ],
        ),
    )


@patch(
    "datahub.ingestion.transformer.enrich_kafka_transformer.KafkaAdminClient.list_consumer_groups"
)
@patch(
    "datahub.ingestion.transformer.enrich_kafka_transformer.KafkaAdminClient.describe_consumer_groups"
)
@patch("datahub.ingestion.transformer.enrich_kafka_transformer.KafkaAdminClient")
def test_enrich_kafka_transformer_with_valid_consumers(
    patch_client,
    patch_client_describe_consumer_groups,
    patch_client_list_consumer_groups,
    mock_time,
    get_kafka_connection_props,
    mock_list_consumer_groups,
    mock_describe_consumer_groups_1_consumer,
    mock_describe_consumer_groups_2_consumer,
):
    input = make_kafka_dataset("test-topic-1")
    patch_client.return_value = patch_client
    patch_client_list_consumer_groups.return_value = mock_list_consumer_groups
    patch_client_describe_consumer_groups.return_value = (
        mock_describe_consumer_groups_1_consumer
    )

    transformer = AddKafkaConsumersTransformer.create(
        get_kafka_connection_props,
        PipelineContext(run_id="test"),
    )

    output = list(transformer.transform([RecordEnvelope(input, metadata={})]))
    assert len(output) == 1

    # check if properties were added
    properties_aspect = builder.get_aspect_if_available(
        output[0].record, models.DatasetPropertiesClass
    )
    assert "consumers" in properties_aspect.customProperties
    assert properties_aspect.customProperties["consumers"] == "consumer_group_2"

    patch_client_describe_consumer_groups.return_value = (
        mock_describe_consumer_groups_2_consumer
    )

    transformer = AddKafkaConsumersTransformer.create(
        get_kafka_connection_props,
        PipelineContext(run_id="test"),
    )
    output = list(transformer.transform([RecordEnvelope(input, metadata={})]))
    assert len(output) == 1

    # check if multiple consumers were added
    properties_aspect = builder.get_aspect_if_available(
        output[0].record, models.DatasetPropertiesClass
    )
    assert "consumers" in properties_aspect.customProperties
    assert len(properties_aspect.customProperties["consumers"].split(",")) == 2
    assert (
        properties_aspect.customProperties["consumers"]
        == "consumer_group_2, consumer_group_3"
    )


@patch(
    "datahub.ingestion.transformer.enrich_kafka_transformer.KafkaAdminClient.list_consumer_groups"
)
@patch("datahub.ingestion.transformer.enrich_kafka_transformer.KafkaAdminClient")
def test_enrich_kafka_transformer_with_no_consumers(
    patch_client,
    patch_client_list_consumer_groups,
    mock_time,
    get_kafka_connection_props,
):
    input = make_kafka_dataset("test-topic-3")
    patch_client.return_value = patch_client
    patch_client_list_consumer_groups.return_value = []
    transformer = AddKafkaConsumersTransformer.create(
        get_kafka_connection_props,
        PipelineContext(run_id="test"),
    )

    output = list(transformer.transform([RecordEnvelope(input, metadata={})]))
    assert len(output) == 1

    # check if properties exist
    properties_aspect = builder.get_aspect_if_available(
        output[0].record, models.DatasetPropertiesClass
    )
    assert properties_aspect is None


def test_convert_to_kafka_python():
    conn = {
        "bootstrap": "localhost:9092",
        "consumer_config": {
            "security.protocol": "SASL_SSL",
            "sasl.mechanism": "PLAIN",
            "sasl.username": "username",
            "sasl.password": "password",
        },
    }
    result = AddKafkaConsumersTransformer.convert_to_kafka_python(conn)
    assert "bootstrap_servers" in result
    assert result["bootstrap_servers"] is "localhost:9092"
    assert "security_protocol" in result
    assert result["security_protocol"] is "SASL_SSL"
    assert "sasl_mechanism" in result
    assert result["sasl_mechanism"] is "PLAIN"
    assert "sasl_plain_username" in result
    assert result["sasl_plain_username"] is "username"
    assert "sasl_plain_password" in result
    assert result["sasl_plain_password"] is "password"


def test_invalid_config_raises_error():
    config_dict = {
        "connection": {
            "bootstrap": "localhost:9092",
            "consumer_config": {
                "security.protocol": "SASL_SSL",
                "sasl.mechanism": "PLAIN",
                "sasl.username": "username",
                "sasl.password": "password",
            },
        }
    }
    invalid_conn = {"conn": {}}
    with pytest.raises(pydantic.ValidationError, match="extra fields not permitted"):
        AddKafkaConsumersConfig.parse_obj(invalid_conn)
    invalid_conn_missing_consumer_config = {
        "connection": {
            "bootstrap": "localhost:9092",
        }
    }
    with pytest.raises(pydantic.ValidationError, match="consumer_config is missing in connection"):
        AddKafkaConsumersConfig.parse_obj(invalid_conn_missing_consumer_config)
    
    invalid_conn_empty_consumer_config = {
        "connection": {
            "bootstrap": "localhost:9092",
            "consumer_config": {},
        }
    }

    with pytest.raises(pydantic.ValidationError, match="security.protocol is missing in consumer_config"):
        AddKafkaConsumersConfig.parse_obj(invalid_conn_empty_consumer_config)
