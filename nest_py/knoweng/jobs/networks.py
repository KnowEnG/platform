"""
This module gathers available Knowledge Network data.
"""

# note: not using pandas so this can run under jython
from collections import Counter
import csv
import os

DEFAULT_SPECIES_FAMILIAR_NAME = 'Human'

def get_species(network_base_dir):
    """Returns information on the available species.

    Args:
        network_base_dir (str): The path to the network base directory.

    Returns:
        list: One element per species, where an element is a dict with keys
            'id', 'latin_name', and 'familiar_name'.
    """
    return_val = []
    species_file = os.path.join(network_base_dir, 'species_desc.txt')
    with open(species_file, 'rb') as csvfile:
        for row in csv.reader(csvfile, delimiter='\t'):
            return_val.append({
                'id': row[0],
                'short_latin_name': row[1],
                'latin_name': row[2],
                'familiar_name': row[3],
                'display_order': row[4],
                'group_name': row[5],
                "selected_by_default": (row[3] == DEFAULT_SPECIES_FAMILIAR_NAME)
            })
    return return_val

def get_collections(all_species, all_networks):
    """Returns flat super collections and their corresponding collections in a given sorting order

    """
    # keeping kegg even though it's not part of our usual KN anymore
    # for all I know, it'll be available in specially licensed versions
    default_pg_names = ['gene_ontology', 'kegg_pathway', 'pfam_prot']
    sc_display_orders = {
        'Ontologies': 1,
        'Pathways': 2,
        'Tissue Expression': 3,
        'Regulation': 4,
        'Disease/Drug': 5,
        'Protein Domains': 6
    }
    return_val = []
    for species in sorted(all_species, key=lambda k: k['familiar_name']):
        for network in sorted(all_networks, key=lambda k: k['supercollection'] + k['pretty_name']):
            if network['node1_type'] == 'Property' and network['species_id'] == species['id']:
                super_collection_name = network['supercollection'].replace('_', ' ')
                return_val.append({
                    'species_number': species['id'],
                    'collection': network['pretty_name'],
                    'edge_type_name': network['edge_type_name'],
                    'collection_selected_by_default': (network['edge_type_name'] in default_pg_names),
                    'super_collection': super_collection_name,
                    'super_collection_display_index': sc_display_orders[super_collection_name]
                })
    return return_val

def get_analysis_networks(all_species, all_networks):
    """Returns interaction networks for analysis if user chooses to use knowledge network when configing pipeline to execute

    """
    return_val = []
    gg_default_name = 'STRING_experimental'
    for species in sorted(all_species, key=lambda k: k['familiar_name']):
        for network in sorted(all_networks, key=lambda k: k['pretty_name']):
            if network['node1_type'] == 'Gene' and network['species_id'] == species['id']:
                return_val.append({
                    'species_number': species['id'],
                    'analysis_network_name': network['pretty_name'],
                    'edge_type_name': network['edge_type_name'],
                    'selected_by_default': (network['edge_type_name'] == gg_default_name)
                })
    return return_val

def get_immediate_subdirectories(a_dir):
    """Given a directory path, returns names of the immediate subdirectories.
    Args:
        a_dir (str): The path to the directory of interest.

    Returns:
        list: One element per subdirectory of a_dir, where an element is a
            string containing the subdirectory's name (not its path).
    """
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def get_network_directories(network_base_dir):
    """Returns information on the available network directories.

    Args:
        network_base_dir (str): The path to the network base directory.

    Returns:
        list: One element per network directory, where an element is a dict with
            keys 'node1_type', 'species_id', and 'edge_type_name', 'path_to_dir',
            'path_to_edge', 'path_to_metadata', 'path_to_node_map', and
            'path_to_pnode_map'.
    """
    return_val = []
    # filesystem layout:
    # <network_base_dir>/<Node1_type>/<species_id>/<edge_type_name>
    for node_type in get_immediate_subdirectories(network_base_dir):
        node_type_dir = os.path.join(network_base_dir, node_type)
        for species_id in get_immediate_subdirectories(node_type_dir):
            species_dir = os.path.join(node_type_dir, species_id)
            for edge_type_name in get_immediate_subdirectories(species_dir):
                # edge_type_dir not currently used
                # edge_type_dir = os.path.join(species_dir, edge_type_name)
                # note base_path does not include network_base_dir
                base_path = os.path.join(node_type, species_id, edge_type_name,\
                    species_id + '.' + edge_type_name)
                return_val.append({
                    'node1_type': node_type,
                    'species_id': species_id,
                    'edge_type_name': edge_type_name,
                    'path_to_dir': base_path,
                    'path_to_edge': base_path + '.edge',
                    'path_to_metadata': base_path + '.metadata',
                    'path_to_node_map': base_path + '.node_map',
                    'path_to_pnode_map': base_path + '.pnode_map'
                })
    return return_val

def get_edge_types(network_base_dir):
    """Returns information on the available edge types.

    Args:
        network_base_dir (str): The path to the network base directory.

    Returns:
        list: One element per edge type, where an element is a dict with keys
            'edge_type_name', 'node1_type', 'supercollection', and
            'pretty_name'.
    """
    return_val = []
    edge_types_file = os.path.join(network_base_dir, 'edge_type.txt')
    with open(edge_types_file, 'rb') as csvfile:
        for row in csv.DictReader(csvfile, delimiter='\t'):
            return_val.append({
                'edge_type_name': row['et_name'],
                'node1_type': row['n1_type'],
                'supercollection': row['supercollection'],
                'pretty_name': row['pretty_name']
            })
    return return_val

def get_merged_network_info(network_base_dir):
    """Returns the merged results of get_network_directories and get_edge_types.

    Args:
        network_base_dir (str): The path to the network base directory.

    Returns:
        list: One element per network/edge type, where an element is a dict with
            keys 'edge_type_name', 'species_id', node1_type', 'supercollection',
            and 'pretty_name'.
    """
    # note edge_types.txt may describe a superset of the networks actually
    # found on disk. we only return information about the networks on disk.
    # we start with the directories and need to add the supercollection and
    # pretty_name
    directories = get_network_directories(network_base_dir)
    types = get_edge_types(network_base_dir)
    name_to_edge_type = \
        {edge_type['edge_type_name']: edge_type for edge_type in types}
    for directory in directories:
        edge_type = name_to_edge_type[directory['edge_type_name']]
        directory['supercollection'] = edge_type['supercollection']
        directory['pretty_name'] = edge_type['pretty_name']
    return directories

def get_set_names_in_network(network_base_dir, path_to_pnode_map):
    """Returns a dict from gene set ids to their associated gene set names for a
    given network.

    Args:
        network_base_dir (str): The path to the network base directory.
        path_to_pnode_map (str): The path from network_base_dir to the network's
            pnode_map file.

    Returns:
        dict: A dictionary in which the keys are gene set ids and each key maps
            to the gene set name associated with the gene set id.
    """
    pnode_map_file = os.path.join(network_base_dir, path_to_pnode_map)
    return_val = {}
    with open(pnode_map_file, 'rb') as csvfile:
        for row in csv.reader(csvfile, delimiter='\t'):
            return_val[row[0]] = row[4]
    return return_val

def get_gene_counts_in_network(network_base_dir, path_to_edge):
    """Returns the gene set ids and their associated gene counts for a given
    network.

    Args:
        network_base_dir (str): The path to the network base directory.
        path_to_edge (str): The path from network_base_dir to the network's edge
            file.

    Returns:
        Counter: A collections.Counter object in which the keys are the gene set
            ids and the values are the number of genes in the gene set.
    """
    edge_file = os.path.join(network_base_dir, path_to_edge)
    counter = Counter()
    with open(edge_file, 'rb') as csvfile:
        for row in csv.reader(csvfile, delimiter='\t'):
            counter.update([row[0]])
    return counter
