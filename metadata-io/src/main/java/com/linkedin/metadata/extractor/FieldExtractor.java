package com.linkedin.metadata.extractor;

import com.linkedin.data.schema.PathSpec;
import com.linkedin.data.template.RecordTemplate;
import com.linkedin.metadata.dao.utils.RecordUtils;
import com.linkedin.metadata.models.AspectSpec;
import com.linkedin.metadata.models.EntitySpec;
import com.linkedin.metadata.models.FieldSpec;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;


/**
 * Extracts fields from a RecordTemplate based on the appropriate {@link FieldSpec}.
 */
public class FieldExtractor {

  private static final String ARRAY_WILDCARD = "*";

  private FieldExtractor() {
  }

  private static long getNumArrayWildcards(PathSpec pathSpec) {
    return pathSpec.getPathComponents().stream().filter(ARRAY_WILDCARD::equals).count();
  }

  // Extract the value of each field in the field specs from the input record
  public static <T extends FieldSpec> Map<T, List<Object>> extractFields(RecordTemplate record, List<T> fieldSpecs) {
    final Map<T, List<Object>> extractedFields = new HashMap<>();
    for (T fieldSpec : fieldSpecs) {
      Optional<Object> value = RecordUtils.getFieldValue(record, fieldSpec.getPath());
      if (!value.isPresent()) {
        extractedFields.put(fieldSpec, Collections.emptyList());
      } else {
        long numArrayWildcards = getNumArrayWildcards(fieldSpec.getPath());
        // Not an array field
        if (numArrayWildcards == 0) {
          extractedFields.put(fieldSpec, Collections.singletonList(value.get()));
        } else {
          List<Object> valueList = (List<Object>) value.get();
          // If the field is a nested list of values, flatten it
          for (int i = 0; i < numArrayWildcards - 1; i++) {
            valueList = valueList.stream().flatMap(v -> ((List<Object>) v).stream()).collect(Collectors.toList());
          }
          extractedFields.put(fieldSpec, valueList);
        }
      }
    }
    return extractedFields;
  }

  public static <T extends FieldSpec> Map<T, List<Object>> extractFieldsFromSnapshot(RecordTemplate snapshot,
      EntitySpec entitySpec, Function<AspectSpec, List<T>> getFieldSpecsFunc) {
    final Map<String, RecordTemplate> aspects = AspectExtractor.extractAspectRecords(snapshot);
    final Map<T, List<Object>> extractedFields = new HashMap<>();
    aspects.keySet()
        .stream()
        .map(aspectName -> FieldExtractor.extractFields(aspects.get(aspectName),
            getFieldSpecsFunc.apply(entitySpec.getAspectSpec(aspectName))))
        .forEach(extractedFields::putAll);
    return extractedFields;
  }
}
