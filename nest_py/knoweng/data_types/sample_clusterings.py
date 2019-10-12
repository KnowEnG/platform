
from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'sample_clusterings'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('job_id')
    schema.add_categoric_list_attribute('consensus_matrix_labels')
    schema.add_jsonb_attribute('consensus_matrix_values')
    schema.add_foreignid_attribute('consensus_matrix_file_id')
    schema.add_foreignid_attribute('init_col_grp_file_id')
    schema.add_int_attribute('init_col_grp_feature_idx')
    schema.add_foreignid_attribute('init_col_srt_file_id')
    schema.add_int_attribute('init_col_srt_feature_idx')
    # don't strictly need silhouette scores stored this way--they're simply the
    # global average and per-cluster averages of the sample-level silhouette
    # scores--but this does simplify life a bit on the client side
    # TODO reconsider down the road
    schema.add_numeric_attribute('global_silhouette_score')
    schema.add_numeric_list_attribute('cluster_silhouette_scores')
    return schema
