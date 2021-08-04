from datahub.metadata.schema_classes import BooleanTypeClass, RecordTypeClass, SchemaFieldDataTypeClass
import pytest

from datahub.ingestion.extractor.protobuf_util import protobuf_schema_to_mce_fields

SCHEMA_WITH_SINGLE_MESSAGE_EMPTY_MESSAGE = """
syntax = "proto3";

message test {
}
"""

SCHEMA_WITH_SINGLE_MESSAGE_SINGLE_FIELD = """
syntax = "proto3";

message test {
    string field_1 = 1;
}
"""

SCHEMA_WITH_TWO_MESSAGES_ENUM = """
syntax = "proto3";

message test {
    string field_1 = 1;

    enum anEnum {
        first = 1;
        second = 2;
    }

    anEnum field_2 = 2;
}

message anotherMessage {
    int64 anInteger = 1;
}
"""

SCHEMA_NESTED = """
syntax = "proto3";

message test_1 {
    test_2 f1 = 1;
    message test_2 {
        test_3 f2 = 1;
        message test_3 {
            test_4 f3 = 1;
            message test_4 {
                message test_5 {}
                test_5 f4 = 1;
            }
        }
    }
}
"""

SCHEMA_REPEATED = """
syntax = "proto3";

message test_1 {
    repeated int64 aList = 1;
}
"""

SCHEMA_REPEATED_WITH_MESSAGE_NESTED_TYPE = """
syntax = "proto3";

message test_1 {
    repeated msg aList = 1;

    message msg {
        string name = 1;
    }
}
"""

SCHEMA_COMPLEX = """
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

def test_protobuf_schema_to_mce_fields_with_single_empty_message():
    schema = SCHEMA_WITH_SINGLE_MESSAGE_EMPTY_MESSAGE
    fields = protobuf_schema_to_mce_fields(schema)

    assert 1 == len(fields)
    assert 'test' == fields[0].fieldPath

def test_protobuf_schema_to_mce_fields_with_single_message_single_field():
    schema = SCHEMA_WITH_SINGLE_MESSAGE_SINGLE_FIELD
    fields = protobuf_schema_to_mce_fields(schema)

    # 1 message + 1 field
    assert 2 == len(fields)
    assert 'test' == fields[0].fieldPath
    assert 'test.field_1' == fields[1].fieldPath
    assert 'message' == fields[0].nativeDataType
    assert 'string' == fields[1].nativeDataType

def test_protobuf_schema_to_mce_fields_with_two_messages_enum():
    schema = SCHEMA_WITH_TWO_MESSAGES_ENUM
    fields = protobuf_schema_to_mce_fields(schema)

    assert 8 == len(fields)
    assert 'test' == fields[0].fieldPath
    assert 'test.field_1' == fields[1].fieldPath
    assert 'test.field_2' == fields[2].fieldPath
    assert 'test.anEnum' == fields[3].fieldPath
    assert 'test.anEnum.first' == fields[4].fieldPath
    assert 'test.anEnum.second' == fields[5].fieldPath
    assert 'anotherMessage' == fields[6].fieldPath
    assert 'anotherMessage.anInteger' == fields[7].fieldPath

def test_protobuf_schema_to_mce_fields_nested():
    schema = SCHEMA_NESTED
    fields = protobuf_schema_to_mce_fields(schema)

    assert 9 == len(fields)
    assert 'test_1' == fields[0].fieldPath

    assert 'test_1.f1' == fields[1].fieldPath
    assert 'test_2' == fields[1].nativeDataType

    assert 'test_1.test_2' == fields[2].fieldPath
    assert 'message' == fields[2].nativeDataType

    assert 'test_1.test_2.f2' == fields[3].fieldPath
    assert 'test_3' == fields[3].nativeDataType

    assert 'test_1.test_2.test_3' == fields[4].fieldPath
    assert 'message' == fields[4].nativeDataType

    assert 'test_1.test_2.test_3.f3' == fields[5].fieldPath
    assert 'test_4' == fields[5].nativeDataType

    assert 'test_1.test_2.test_3.test_4' == fields[6].fieldPath
    assert 'message' == fields[6].nativeDataType

    assert 'test_1.test_2.test_3.test_4.f4' == fields[7].fieldPath
    assert 'test_5' == fields[7].nativeDataType

    assert 'test_1.test_2.test_3.test_4.test_5' == fields[8].fieldPath
    assert 'message' == fields[8].nativeDataType

def test_protobuf_schema_to_mce_fields_repeated():
    schema = SCHEMA_REPEATED
    fields = protobuf_schema_to_mce_fields(schema)

    assert 2 == len(fields)
    assert 'repeated int64' == fields[1].nativeDataType
    assert 'int64' == fields[1].type.type.nestedType[0]

def test_protobuf_schema_to_mce_fields_repeated():
    schema = SCHEMA_REPEATED_WITH_MESSAGE_NESTED_TYPE
    fields = protobuf_schema_to_mce_fields(schema)

    assert 4 == len(fields)
    assert 'repeated msg' == fields[1].nativeDataType
    assert 'msg' == fields[1].type.type.nestedType[0]

def test_protobuf_schema_to_mce_fields_with_complex_schema():
    schema = SCHEMA_COMPLEX
    fields = protobuf_schema_to_mce_fields(schema)

    # 2 outer messages, 4 fields in the first message, 1 field in the second
    # message, 1 inner message, 1 oneof, 1 enum, 2 oneof fields, 2 enum fields
    assert 14 == len(fields)
