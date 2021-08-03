import pytest

from datahub.ingestion.extractor.protobuf_util import protobuf_schema_to_mce_fields

SCHEMA_WITH_SINGLE_MESSAGE_AND_SEVERAL_PRIMITIVE_TYPED_FIELDS = """
syntax = "proto3";
message test {
    string string_field_1  = 1;
    bool   boolean_field_1 = 2;
    int64  int64_field_1   = 3;

    emptyMessage emptyMsg = 4;

    // an empty message
    message emptyMessage {};

    oneof payload {
        string pl_1 = 1;
        int64  pl_2 = 2;
    }

    enum anEnum {
        idle = 0;
        spinning = 1;
    }
}

message outside {
    int64 an_int_64_field = 1;
}
"""

def test_protobuf_schema_to_mce_fields_with_single_message():
    schema = SCHEMA_WITH_SINGLE_MESSAGE_AND_SEVERAL_PRIMITIVE_TYPED_FIELDS
    fields = protobuf_schema_to_mce_fields(schema)

    # 2 outer messages, 4 fields, 1 inner message
    assert 14 == len(fields)
