from datahub.ingestion.api.registry import Registry
from datahub.ingestion.api.transform import Transformer
from datahub.ingestion.transformer.add_dataset_browse_path import (
    AddDatasetBrowsePathTransformer,
)
from datahub.ingestion.transformer.add_dataset_ownership import (
    AddDatasetOwnership,
    PatternAddDatasetOwnership,
    SimpleAddDatasetOwnership,
)
from datahub.ingestion.transformer.add_dataset_tags import (
    AddDatasetTags,
    SimpleAddDatasetTags,
)
from datahub.ingestion.transformer.mark_dataset_status import MarkDatasetStatus
from datahub.ingestion.transformer.remove_dataset_ownership import (
    SimpleRemoveDatasetOwnership,
)
from datahub.ingestion.transformer.enrich_kafka_transformer import (
    AddKafkaConsumersTransformer,
    # AddDomainTagsTransformer,
)

transform_registry = Registry[Transformer]()

transform_registry.register(
    "simple_remove_dataset_ownership", SimpleRemoveDatasetOwnership
)
transform_registry.register("mark_dataset_status", MarkDatasetStatus)
transform_registry.register("set_dataset_browse_path", AddDatasetBrowsePathTransformer)

transform_registry.register("add_dataset_ownership", AddDatasetOwnership)
transform_registry.register("simple_add_dataset_ownership", SimpleAddDatasetOwnership)
transform_registry.register("pattern_add_dataset_ownership", PatternAddDatasetOwnership)

transform_registry.register("add_dataset_tags", AddDatasetTags)
transform_registry.register("simple_add_dataset_tags", SimpleAddDatasetTags)

transform_registry.register("add_kafka_consumers", AddKafkaConsumersTransformer)
# transform_registry.register("add_domain_tags", AddDomainTagsTransformer)