import logging
from os import name
from typing import Any, List, Optional, Union
from avro.schema import Schema

import protoparser_ng as protoparser

from datahub.metadata.com.linkedin.pegasus2avro.schema import (
    ArrayTypeClass,
    BooleanTypeClass,
    BytesTypeClass,
    EnumTypeClass,
    MapTypeClass,
    NumberTypeClass,
    RecordTypeClass,
    SchemaField,
    SchemaFieldDataType,
    StringTypeClass,
    UnionTypeClass,
)
from protoparser_ng.parser import Field, Message, Oneof, Enum

logger = logging.getLogger(__name__)

_field_type_mapping = {
    "bool": BooleanTypeClass,
    "int32": NumberTypeClass,
    "int64": NumberTypeClass,
    "uint32": NumberTypeClass,
    "uint64": NumberTypeClass,
    "sint32": NumberTypeClass,
    "sint64": NumberTypeClass,
    "fixed32": NumberTypeClass,
    "fixed64": NumberTypeClass,
    "sfixed32": NumberTypeClass,
    "sfixed64": NumberTypeClass,
    "float": NumberTypeClass,
    "double": NumberTypeClass,
    "bytes": BytesTypeClass,
    "string": StringTypeClass,
    "message": RecordTypeClass,
    "map": MapTypeClass,
    "enum": EnumTypeClass,
    "repeated": ArrayTypeClass,
    "oneof": UnionTypeClass,
}

def _protobuf_fields_to_mce_fields(protobuf_fields: List[Field], parent: str) -> List[SchemaField]:
    """Convert protobuf fields into MCE fields"""
    mce_fields: List[SchemaField] = []

    # Add fields defined in a message
    for f in protobuf_fields:
        if f.type == 'repeated':
            field_type = SchemaFieldDataType(type=ArrayTypeClass(nestedType=[f.key_type]))
        else:
            field_type = SchemaFieldDataType(type=_field_type_mapping[f.type]()) if f.type in _field_type_mapping else SchemaFieldDataType(type=RecordTypeClass())

        field = SchemaField(
            fieldPath = f'{parent}.{f.name}',
            nativeDataType = f'{f.type} {f.key_type}' if f.type == 'repeated' else f.type,
            type = field_type
        )
        mce_fields.append(field)

    return mce_fields

def _oneofs_to_mce_fields(oneof: Oneof, parent: str = None) -> List[SchemaField]:
    """Converts protobuf oneofs into MCE unions"""
    fields: List[SchemaField] = []
    current_path = f'{parent}.{oneof.name}' if parent is not None else oneof.name

    # Add the oneof itself
    fields.append(SchemaField(
        fieldPath=current_path,
        nativeDataType='oneof',
        type=SchemaFieldDataType(type=UnionTypeClass())
    ))

    # Add fields defined in the oneof
    fields += _protobuf_fields_to_mce_fields(oneof.fields, current_path)

    return fields

def _enums_to_mce_fields(pbenum: Enum, parent: str = None) -> List[SchemaField]:
    """Converts protobuf enums into MCE enums"""
    fields: List[SchemaField] = []
    current_path = f'{parent}.{pbenum.name}' if parent is not None else pbenum.name

    # Add the enum itself
    fields.append(SchemaField(
        fieldPath=current_path,
        nativeDataType='enum',
        type=SchemaFieldDataType(type=EnumTypeClass())
    ))

    # Add fields defined in an enum
    fields += _protobuf_fields_to_mce_fields(pbenum.fields, current_path)

    return fields

def _message_to_mce_fields(message: Message, parent: str = None) -> List[SchemaField]:
    """Converts protobuf messages into MCE records"""
    fields: List[SchemaField] = []
    current_path = f'{parent}.{message.name}' if parent is not None else message.name

    # Add the message itself
    fields.append(SchemaField(
        fieldPath=current_path,
        nativeDataType='message',
        type = SchemaFieldDataType(type=RecordTypeClass()),
    ))

    # Add fields defined in a message
    fields += _protobuf_fields_to_mce_fields(message.fields, current_path)

    # Add the oneofs defined in a message
    for k, v in message.oneofs.items():
        fields += _oneofs_to_mce_fields(v, current_path)

    # Add the oneofs defined in a message
    for k, v in message.enums.items():
        fields += _enums_to_mce_fields(v, current_path)

    # Add messages defined (nested) in a message
    for k, v in message.messages.items():
        fields += _message_to_mce_fields(v, current_path)

    return fields

def protobuf_schema_to_mce_fields(protobuf_schema_string: str) -> List[SchemaField]:
    """Converts a protobuf schema into a schema compatible with MCE"""

    proto_file = protoparser.parse(protobuf_schema_string)

    fields: List[SchemaField] = []
    for k, v in proto_file.messages.items():
        if type(v) is Message:
            fields += _message_to_mce_fields(v)

    return fields