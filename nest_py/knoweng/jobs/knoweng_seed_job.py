import os
import nest_py.knoweng.jobs.networks as networks
import nest_py.knoweng.data_types.public_gene_sets as public_gene_sets
import nest_py.knoweng.data_types.species as species
import nest_py.knoweng.data_types.collections as collections
import nest_py.knoweng.data_types.analysis_networks as analysis_networks
import nest_py.core.data_types.tablelike_entry as tablelike_entry

from nest_py.core.jobs.checkpoint import CheckpointTimer
import nest_py.core.jobs.jobs_auth as jobs_auth
import nest_py.knoweng.jobs.db_utils as db_utils

def run(http_client, db_engine, data_dir, subsample, flavor_name):
    """
    http_client (NestHttpClient): an http client configured for a particular api server (NOT USED, db_utils reads direct from CONFIG)
    db_engine  (NOT USED, db_utils reads direct from CONFIG)
    data_dir (str): location to write data files
    subsample (bool): ignored
    flavor_name (str): ignored
    """

    # TODO fix this
    data_dir = '/'

    timer = CheckpointTimer('knoweng_seed')
    timer.checkpoint("knoweng_seed_job: Begin")
    exit_code = 0

    #will read from nest_config parameters shared with flask
    db_utils.init_crud_clients()

    network_base_dir = os.path.join(data_dir, 'networks')
    merged_networks = networks.get_merged_network_info(network_base_dir)
    all_species = networks.get_species(network_base_dir)
    collections = networks.get_collections(all_species, merged_networks)
    analysis_networks = networks.get_analysis_networks(all_species, merged_networks)
    
    timer.checkpoint("Loading public gene sets")
    load_public_gene_sets(merged_networks, network_base_dir)
    timer.checkpoint("Loading species")
    load_species(all_species)
    timer.checkpoint("Loading collections")
    load_collections(collections)
    timer.checkpoint("Loading analysis networks")
    load_analysis_networks(analysis_networks)
    timer.checkpoint("knoweng_seed_job: Done")
    
    return exit_code
    
def load_public_gene_sets(merged_networks, network_base_dir):
    pgs_schema = public_gene_sets.generate_schema()
    coll_name = public_gene_sets.COLLECTION_NAME
    public_gene_sets_client = db_utils.get_crud_client(coll_name)
    pgs_tles = list()
    for network in merged_networks:
        if network['node1_type'] == 'Property':
            # get set names
            set_id_to_set_name = networks.get_set_names_in_network(\
                network_base_dir, network['path_to_pnode_map'])
            # TODO url or something
            # open path_to_edge and collect set ids and their gene counts
            for set_id, gene_count in networks.get_gene_counts_in_network(\
                network_base_dir, network['path_to_edge']).items():

                tle = tablelike_entry.TablelikeEntry(pgs_schema)
                
                tle.set_value('set_id', set_id)
                # TODO remove default in next line once networks are ready
                set_name = set_id_to_set_name.get(set_id, set_id).replace('_', ' ')
                tle.set_value('set_name', set_name)
                tle.set_value('species_id', network['species_id'])
                tle.set_value('gene_count', gene_count)
                tle.set_value('collection', network['pretty_name'])
                tle.set_value('edge_type_name', network['edge_type_name'])
                supercollection = network['supercollection'].replace('_', ' ')
                tle.set_value('supercollection', supercollection)
                tle.set_value('url', 'TODO url')

                #tle = public_gene_sets_client.create_entry(tle)
                pgs_tles.append(tle)
    num_created = public_gene_sets_client.bulk_create_entries_async(pgs_tles, batch_size=5000)
    assert(num_created == len(pgs_tles))
    return

def load_species(all_species):
    species_schema = species.generate_schema()
    species_client = db_utils.get_crud_client(species_schema.get_name())
    for sc in all_species:
        tle = tablelike_entry.TablelikeEntry(species_schema)
        tle.set_value('species_number', sc['id'])
        tle.set_value('short_latin_name', sc['short_latin_name'])
        tle.set_value('name', sc['familiar_name'])
        tle.set_value('display_order', sc['display_order'])
        tle.set_value('group_name', sc['group_name'])
        tle.set_value('selected_by_default', bool(sc['selected_by_default']))
        tle = species_client.create_entry(tle)
        assert(not tle is None)
        
def load_collections(all_collections):
    collections_schema = collections.generate_schema()
    collections_client = db_utils.get_crud_client(collections_schema.get_name())
    for collection in all_collections:
        tle = tablelike_entry.TablelikeEntry(collections_schema)
        tle.set_value('super_collection', collection['super_collection'])
        tle.set_value('species_number', collection['species_number'])
        tle.set_value('edge_type_name', collection['edge_type_name'])
        tle.set_value('super_collection_display_index', collection['super_collection_display_index'])
        tle.set_value('collection', collection['collection'])
        tle.set_value('collection_selected_by_default', bool(collection['collection_selected_by_default']))
        tle = collections_client.create_entry(tle)
        assert(not tle is None)
        
def load_analysis_networks(all_analysis_networks):
    an_schema = analysis_networks.generate_schema()
    analysis_networks_client = db_utils.get_crud_client(an_schema.get_name())
    for network in all_analysis_networks:
        tle = tablelike_entry.TablelikeEntry(an_schema)
        tle.set_value('species_number', network['species_number'])
        tle.set_value('analysis_network_name', network['analysis_network_name'])
        tle.set_value('edge_type_name', network['edge_type_name'])
        tle.set_value('selected_by_default', bool(network['selected_by_default']))
        tle = analysis_networks_client.create_entry(tle)
        assert(not tle is None)
        
