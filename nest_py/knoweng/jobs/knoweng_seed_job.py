from bz2 import BZ2File
import os
from shutil import copyfileobj
from urllib import urlretrieve
import zipfile

import nest_py.knoweng.jobs.networks as networks
import nest_py.knoweng.data_types.public_gene_sets as public_gene_sets
import nest_py.knoweng.data_types.species as species
import nest_py.knoweng.data_types.collections as collections
import nest_py.knoweng.data_types.analysis_networks as analysis_networks
import nest_py.core.data_types.tablelike_entry as tablelike_entry

from nest_py.core.jobs.checkpoint import CheckpointTimer
import nest_py.knoweng.jobs.db_utils as db_utils

URL_FOR_DEMO_DATA_AND_READMES = \
    'https://github.com/KnowEnG/quickstart-demos/archive/' + \
    '251b70e50ae51d2a43113097c925a5227065a27e.zip'

def run(http_client, db_engine, data_dir, subsample, flavor_name):
    """
    http_client (NestHttpClient): an http client configured for a particular api
        server (NOT USED, db_utils reads direct from CONFIG)
    db_engine  (NOT USED, db_utils reads direct from CONFIG)
    data_dir (str): location to write data files
    subsample (bool): ignored
    flavor_name (str): ignored
    """
    timer = CheckpointTimer('knoweng_seed')
    timer.checkpoint("knoweng_seed_job: Begin")
    exit_code = 0

    #will read from nest_config parameters shared with flask
    db_utils.init_crud_clients()

    network_base_dir = '/networks' # TODO centralize config
    merged_networks = networks.get_merged_network_info(network_base_dir)
    all_species = networks.get_species(network_base_dir)
    all_collections = networks.get_collections(all_species, merged_networks)
    all_analysis_networks = networks.get_analysis_networks(all_species, merged_networks)

    timer.checkpoint("Loading public gene sets")
    load_public_gene_sets(merged_networks, network_base_dir)
    timer.checkpoint("Loading species")
    load_species(all_species)
    timer.checkpoint("Loading collections")
    load_collections(all_collections)
    timer.checkpoint("Loading analysis networks")
    load_analysis_networks(all_analysis_networks)
    timer.checkpoint("Loading demo data and readmes")
    load_demo_data_and_readmes(data_dir)
    timer.checkpoint("knoweng_seed_job: Done")

    return exit_code

def load_public_gene_sets(merged_networks, network_base_dir):
    pgs_schema = public_gene_sets.generate_schema()
    coll_name = public_gene_sets.COLLECTION_NAME
    public_gene_sets_client = db_utils.get_crud_client(coll_name)
    pgs_tles = list()
    
    # Get count of all table entries
    all_entries = public_gene_sets_client.simple_filter_query({})
    all_entries_count = len(all_entries)
    if all_entries_count > 0:
        print('Found ' + str(all_entries_count) + ' entries in public_gene_sets.. skipping import')
        return
    
    for network in merged_networks:
        if network['node1_type'] == 'Property':
            # get set names
            set_id_to_set_name = networks.get_set_names_in_network(\
                network_base_dir, network['path_to_pnode_map'])
            # TODO url or something
            # open path_to_edge and collect set ids and their gene counts
            for set_id, gene_count in networks.get_gene_counts_in_network(\
                network_base_dir, network['path_to_edge']).items():
                    
                # TODO remove default in next line once networks are ready
                set_name = set_id_to_set_name.get(set_id, set_id).replace('_', ' ')
                supercollection = network['supercollection'].replace('_', ' ')
                    
                # Check if this already exists (if so, skip)
                existings = public_gene_sets_client.simple_filter_query({
                    'set_id': set_id,
                    'set_name': set_name,
                    'species_id': network['species_id'],
                    'collection': network['pretty_name'],
                    'gene_count': gene_count,
                    'edge_type_name': network['edge_type_name'],
                    'supercollection': supercollection
                })
                if len(existings) > 0:
                    #print('public gene set ' + str(set_id) + ' already exists... skipping')
                    continue

                tle = tablelike_entry.TablelikeEntry(pgs_schema)

                tle.set_value('set_id', set_id)
                tle.set_value('set_name', set_name)
                tle.set_value('species_id', network['species_id'])
                tle.set_value('gene_count', gene_count)
                tle.set_value('collection', network['pretty_name'])
                tle.set_value('edge_type_name', network['edge_type_name'])
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
        # Check if this already exists (if so, skip)
        existings = species_client.simple_filter_query({
            'species_number': sc['id'],
            'short_latin_name': sc['short_latin_name'],
            'name': sc['familiar_name'],
            'group_name': sc['group_name']
        })
        if len(existings) > 0:
            print('species ' + str(sc['id']) + ' already exists... skipping')
            continue
        
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
        existings = collections_client.simple_filter_query({
            'collection': collection['collection'],
            'super_collection': collection['super_collection'],
            'species_number': collection['species_number'],
            'edge_type_name': collection['edge_type_name']
        })
        if len(existings) > 0:
            print('collection ' + str(collection['collection']) + ' already exists... skipping')
            continue
        
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
        species_number = network['species_number']
        analysis_network_name = network['analysis_network_name']
        edge_type_name = network['edge_type_name']
        selected_by_default = bool(network['selected_by_default'])
        
        # Check if this already exists (if so, skip)
        existings = analysis_networks_client.simple_filter_query({
            'species_number': species_number,
            'analysis_network_name': analysis_network_name,
            'edge_type_name': edge_type_name
        })
        if len(existings) > 0:
            print('analysis network ' + str(analysis_network_name) + ' already exists... skipping')
            continue
        
        tle = tablelike_entry.TablelikeEntry(an_schema)
        tle.set_value('species_number', species_number)
        tle.set_value('analysis_network_name', analysis_network_name)
        tle.set_value('edge_type_name', edge_type_name)
        tle.set_value('selected_by_default', selected_by_default)
        tle = analysis_networks_client.create_entry(tle)
        assert(not tle is None)

def load_demo_data_and_readmes(data_dir):
    # download the zip to data_dir
    zip_path = os.path.join(data_dir, 'demos_readmes.zip')
    urlretrieve(URL_FOR_DEMO_DATA_AND_READMES, zip_path)
    # next two dir names do double-duty: they're the names of the directories
    # in the zip and the names we'll use for the subdirectories on disk
    # TODO centralize config
    demo_data_dir_name = 'demo_files'
    readmes_dir_name = 'pipeline_readmes'
    # this next one is for the name of a directory in the zip only; we'll use
    # the demo_data_dir_name on disk
    publication_data_dir_name = 'publication_data'
    # create the directories on disk
    demo_data_dir_path = os.path.join(data_dir, demo_data_dir_name)
    readmes_dir_path = os.path.join(data_dir, readmes_dir_name)
    for path in [demo_data_dir_path, readmes_dir_path]:
        _ensure_directory(path)
    with zipfile.ZipFile(zip_path, 'r') as inzip:
        for filepath in inzip.namelist():
            dirname = os.path.dirname(filepath)
            filename = os.path.basename(filepath)
            outpath = None
            if filename:
                if dirname.endswith(demo_data_dir_name):
                    outpath = os.path.join(demo_data_dir_path, filename)
                elif dirname.endswith(readmes_dir_name):
                    outpath = os.path.join(readmes_dir_path, filename)
                else:
                    # check for publication_data
                    pd_index = dirname.find(publication_data_dir_name)
                    if pd_index >= 0:
                        dir_pieces = dirname[pd_index:].split('/')
                        dirpath = os.path.join(demo_data_dir_path, *dir_pieces)
                        _ensure_directory(dirpath)
                        outpath = os.path.join(dirpath, filename)
                    else:
                        # whatever this item is, we don't need it
                        pass
            else:
                # this is a directory
                pass
            if outpath is not None:
                with inzip.open(filepath) as fsrc, open(outpath, 'wb') as fdst:
                    copyfileobj(fsrc, fdst)
            if outpath is not None and outpath.endswith('.bz2'):
                bzpath = outpath[:-4]
                with BZ2File(outpath, 'rb') as fsrc, open(bzpath, 'wb') as fdst:
                    for block in iter(lambda: fsrc.read(100 * 1024), b''):
                        fdst.write(block)
                os.remove(outpath)
    os.remove(zip_path)

def _ensure_directory(path):
    if not os.path.isdir(path):
        print "Creating " + path
        os.makedirs(path)
    else:
        print "Found " + path
