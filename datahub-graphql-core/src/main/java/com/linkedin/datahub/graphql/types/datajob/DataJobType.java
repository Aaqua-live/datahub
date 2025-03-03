package com.linkedin.datahub.graphql.types.datajob;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.linkedin.common.urn.CorpuserUrn;
import com.linkedin.common.urn.DataJobUrn;
import com.linkedin.common.urn.Urn;
import com.linkedin.common.urn.UrnUtils;
import com.linkedin.data.template.StringArray;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.authorization.AuthorizationUtils;
import com.linkedin.datahub.graphql.authorization.ConjunctivePrivilegeGroup;
import com.linkedin.datahub.graphql.authorization.DisjunctivePrivilegeGroup;
import com.linkedin.datahub.graphql.exception.AuthorizationException;
import com.linkedin.datahub.graphql.generated.AutoCompleteResults;
import com.linkedin.datahub.graphql.generated.BrowsePath;
import com.linkedin.datahub.graphql.generated.BrowseResults;
import com.linkedin.datahub.graphql.generated.DataJob;
import com.linkedin.datahub.graphql.generated.DataJobUpdateInput;
import com.linkedin.datahub.graphql.generated.Entity;
import com.linkedin.datahub.graphql.generated.EntityType;
import com.linkedin.datahub.graphql.generated.FacetFilterInput;
import com.linkedin.datahub.graphql.generated.SearchResults;
import com.linkedin.datahub.graphql.resolvers.ResolverUtils;
import com.linkedin.datahub.graphql.types.BrowsableEntityType;
import com.linkedin.datahub.graphql.types.MutableType;
import com.linkedin.datahub.graphql.types.SearchableEntityType;
import com.linkedin.datahub.graphql.types.datajob.mappers.DataJobMapper;
import com.linkedin.datahub.graphql.types.datajob.mappers.DataJobUpdateInputMapper;
import com.linkedin.datahub.graphql.types.mappers.AutoCompleteResultsMapper;
import com.linkedin.datahub.graphql.types.mappers.BrowsePathsMapper;
import com.linkedin.datahub.graphql.types.mappers.BrowseResultMapper;
import com.linkedin.datahub.graphql.types.mappers.UrnSearchResultsMapper;
import com.linkedin.entity.EntityResponse;
import com.linkedin.entity.client.EntityClient;
import com.linkedin.metadata.Constants;
import com.linkedin.metadata.authorization.PoliciesConfig;
import com.linkedin.metadata.browse.BrowseResult;
import com.linkedin.metadata.query.AutoCompleteResult;
import com.linkedin.metadata.search.SearchResult;
import com.linkedin.mxe.MetadataChangeProposal;
import com.linkedin.r2.RemoteInvocationException;
import graphql.execution.DataFetcherResult;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import static com.linkedin.datahub.graphql.Constants.*;
import static com.linkedin.metadata.Constants.*;


public class DataJobType implements SearchableEntityType<DataJob, String>, BrowsableEntityType<DataJob, String>,
                                    MutableType<DataJobUpdateInput, DataJob> {

    private static final Set<String> ASPECTS_TO_RESOLVE = ImmutableSet.of(
        DATA_JOB_KEY_ASPECT_NAME,
        DATA_JOB_INFO_ASPECT_NAME,
        DATA_JOB_INPUT_OUTPUT_ASPECT_NAME,
        EDITABLE_DATA_JOB_PROPERTIES_ASPECT_NAME,
        OWNERSHIP_ASPECT_NAME,
        INSTITUTIONAL_MEMORY_ASPECT_NAME,
        GLOBAL_TAGS_ASPECT_NAME,
        GLOSSARY_TERMS_ASPECT_NAME,
        STATUS_ASPECT_NAME,
        DOMAINS_ASPECT_NAME,
        DEPRECATION_ASPECT_NAME
    );
    private static final Set<String> FACET_FIELDS = ImmutableSet.of("flow");
    private final EntityClient _entityClient;

    public DataJobType(final EntityClient entityClient) {
        _entityClient = entityClient;
    }

    @Override
    public EntityType type() {
        return EntityType.DATA_JOB;
    }

    @Override
    public Function<Entity, String> getKeyProvider() {
        return Entity::getUrn;
    }

    @Override
    public Class<DataJob> objectClass() {
        return DataJob.class;
    }

    @Override
    public Class<DataJobUpdateInput> inputClass() {
        return DataJobUpdateInput.class;
    }

    @Override
    public List<DataFetcherResult<DataJob>> batchLoad(final List<String> urnStrs, @Nonnull final QueryContext context)
        throws Exception {
        final List<Urn> urns = urnStrs.stream()
            .map(UrnUtils::getUrn)
            .collect(Collectors.toList());
        try {
            final Map<Urn, EntityResponse> dataJobMap = _entityClient.batchGetV2(
                Constants.DATA_JOB_ENTITY_NAME,
                new HashSet<>(urns),
                ASPECTS_TO_RESOLVE,
                context.getAuthentication());

            final List<EntityResponse> gmsResults = new ArrayList<>();
            for (Urn urn : urns) {
                gmsResults.add(dataJobMap.getOrDefault(urn, null));
            }
            return gmsResults.stream()
                .map(gmsDataJob -> gmsDataJob == null ? null : DataFetcherResult.<DataJob>newResult()
                    .data(DataJobMapper.map(gmsDataJob))
                    .build())
                .collect(Collectors.toList());
        } catch (Exception e) {
            throw new RuntimeException("Failed to batch load Data Jobs", e);
        }
    }

    @Override
    public SearchResults search(@Nonnull String query,
                                @Nullable List<FacetFilterInput> filters,
                                int start,
                                int count,
                                @Nonnull final QueryContext context) throws Exception {
        final Map<String, String> facetFilters = ResolverUtils.buildFacetFilters(filters, FACET_FIELDS);
        final SearchResult searchResult = _entityClient.search(
            "dataJob", query, facetFilters, start, count, context.getAuthentication());
        return UrnSearchResultsMapper.map(searchResult);
    }

    @Override
    public AutoCompleteResults autoComplete(@Nonnull String query,
                                            @Nullable String field,
                                            @Nullable List<FacetFilterInput> filters,
                                            int limit,
                                            @Nonnull final QueryContext context) throws Exception {
        final Map<String, String> facetFilters = ResolverUtils.buildFacetFilters(filters, FACET_FIELDS);
        final AutoCompleteResult result = _entityClient.autoComplete("dataJob", query, facetFilters, limit, context.getAuthentication());
        return AutoCompleteResultsMapper.map(result);
    }

    @Override
    public BrowseResults browse(@Nonnull List<String> path, @Nullable List<FacetFilterInput> filters, int start,
        int count, @Nonnull QueryContext context) throws Exception {
                final Map<String, String> facetFilters = ResolverUtils.buildFacetFilters(filters, FACET_FIELDS);
        final String pathStr = path.size() > 0 ? BROWSE_PATH_DELIMITER + String.join(BROWSE_PATH_DELIMITER, path) : "";
        final BrowseResult result = _entityClient.browse(
            "dataJob",
                pathStr,
                facetFilters,
                start,
                count,
            context.getAuthentication());
        return BrowseResultMapper.map(result);
    }

    @Override
    public List<BrowsePath> browsePaths(@Nonnull String urn, @Nonnull QueryContext context) throws Exception {
        final StringArray result = _entityClient.getBrowsePaths(DataJobUrn.createFromString(urn), context.getAuthentication());
        return BrowsePathsMapper.map(result);
    }

    @Override
    public DataJob update(@Nonnull String urn, @Nonnull DataJobUpdateInput input, @Nonnull QueryContext context) throws Exception {
        if (isAuthorized(urn, input, context)) {
            final CorpuserUrn actor = CorpuserUrn.createFromString(context.getAuthentication().getActor().toUrnStr());
            final Collection<MetadataChangeProposal> proposals = DataJobUpdateInputMapper.map(input, actor);
            proposals.forEach(proposal -> proposal.setEntityUrn(UrnUtils.getUrn(urn)));

            try {
                _entityClient.batchIngestProposals(proposals, context.getAuthentication());
            } catch (RemoteInvocationException e) {
                throw new RuntimeException(String.format("Failed to write entity with urn %s", urn), e);
            }

            return load(urn, context).getData();
        }
        throw new AuthorizationException("Unauthorized to perform this action. Please contact your DataHub administrator.");
    }

    private boolean isAuthorized(@Nonnull String urn, @Nonnull DataJobUpdateInput update, @Nonnull QueryContext context) {
        // Decide whether the current principal should be allowed to update the Dataset.
        final DisjunctivePrivilegeGroup orPrivilegeGroups = getAuthorizedPrivileges(update);
        return AuthorizationUtils.isAuthorized(
            context.getAuthorizer(),
            context.getAuthentication().getActor().toUrnStr(),
            PoliciesConfig.DATA_JOB_PRIVILEGES.getResourceType(),
            urn,
            orPrivilegeGroups);
    }

    private DisjunctivePrivilegeGroup getAuthorizedPrivileges(final DataJobUpdateInput updateInput) {

        final ConjunctivePrivilegeGroup allPrivilegesGroup = new ConjunctivePrivilegeGroup(ImmutableList.of(
            PoliciesConfig.EDIT_ENTITY_PRIVILEGE.getType()
        ));

        List<String> specificPrivileges = new ArrayList<>();
        if (updateInput.getOwnership() != null) {
            specificPrivileges.add(PoliciesConfig.EDIT_ENTITY_OWNERS_PRIVILEGE.getType());
        }
        if (updateInput.getEditableProperties() != null) {
            specificPrivileges.add(PoliciesConfig.EDIT_ENTITY_DOCS_PRIVILEGE.getType());
        }
        if (updateInput.getGlobalTags() != null) {
            specificPrivileges.add(PoliciesConfig.EDIT_ENTITY_TAGS_PRIVILEGE.getType());
        }
        final ConjunctivePrivilegeGroup specificPrivilegeGroup = new ConjunctivePrivilegeGroup(specificPrivileges);

        // If you either have all entity privileges, or have the specific privileges required, you are authorized.
        return new DisjunctivePrivilegeGroup(ImmutableList.of(
            allPrivilegesGroup,
            specificPrivilegeGroup
        ));
    }
}
