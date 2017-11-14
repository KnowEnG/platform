"""
analytics functions and data structures for turning a
an AttributeTree representing a taxonomy
with each taxa having a set of attributes representing
analytics of the otus below it
"""
import math
import numpy
import skbio.diversity.alpha
import random

from nest_py.omix.jobs.attribute_tree import AttributeTree
from nest_py.omix.jobs.sparse_array import SparseArray
import nest_py.omix.jobs.otu_analysis as otu_analysis
import nest_py.omix.jobs.cohort_tree_etl as cohort_tree_etl

import nest_py.omix.data_types.otus as otus
import nest_py.core.jobs.jobs_logger as logger
from nest_py.core.jobs.checkpoint import CheckpointTimer

def compute_all_for_cohorts(client_registry, cohort_tles, all_geno_samples, otu_defs,
    num_quantiles=8, num_bins=20, timer=CheckpointTimer("cohort_analysis")):
    """
    compute all analytics for each cohort in a list. they will share some
    scaling factors between all cohorts.

    """
    #deduce the structure of the tree, which we will copy each time
    taxonomy_empty_tree = otu_analysis.compute_taxonomy_tree(otu_defs)

    global_max_unique_otus = compute_global_max_unique_otus(cohort_tles,
        all_geno_samples, otu_defs, taxonomy_empty_tree)

    for cohort in cohort_tles:
        tree = taxonomy_empty_tree.copy()
        compute_cohort_metrics(cohort, all_geno_samples, otu_defs, tree, timer=timer)
        compute_cohort_aggregates(cohort, tree, 
            num_quantiles=num_quantiles,
            num_bins=num_bins,
            unique_otus_bin_max=global_max_unique_otus,
            timer=timer)

        cohort_tree_etl.upload_nodes(client_registry, cohort, tree, timer=timer)
    return 

def compute_global_max_unique_otus(cohort_tles, all_geno_samples, otu_defs, empty_tree):
    """
    TODO: this is very ineffient to do sum_gross_counts_per_sample and then 
    throw it out, but needed to free up the memory
    """
    global_max = 0.0
    for cohort_def in cohort_tles:
        cohort_name = cohort_def.get_value('display_name_short')
        log('finding max_unique_otus for ' + cohort_name)
        taxonomy_tree = empty_tree.copy()
        geno_sample_lst = subset_samples_by_cohort(all_geno_samples, cohort_def)
        sum_gross_counts_per_sample(taxonomy_tree, otu_defs, geno_sample_lst)
        compute_unique_otus_per_sample(taxonomy_tree)
        local_max_unique_otus = find_effective_max_unique_otus(taxonomy_tree)
        if local_max_unique_otus > global_max:
            global_max = local_max_unique_otus

    #we want to round this to the nearest 100
    #print('global max unique otus before rounding up: ' + str(global_max))
    global_max = (math.ceil(global_max / 100.0)) * 100.0
    #print('global max unique otus: ' + str(global_max))
    return global_max


def compute_cohort_metrics(cohort_def, all_geno_samples, otu_defs, taxonomy_tree,
    timer=CheckpointTimer('cohort_metrics')):
    """
    takes a cohort def (that includes the geno_sample ids in the cohort),
    and the master list of all geno_samples that were part of the tornado run.
    Also takes the otu defs and a copy of an AttributeTree that represents just
    the taxonomy.

    this computes all of the core metrics that we need at every node, at every sample
    """
    cohort_name = cohort_def.get_value('display_name_short')
    timer.checkpoint('begin cohort basic metrics: ' + cohort_name)
    geno_sample_lst = subset_samples_by_cohort(all_geno_samples, cohort_def)
    sum_gross_counts_per_sample(taxonomy_tree, otu_defs, geno_sample_lst)
    compute_abundance_frac_per_sample(taxonomy_tree)
    compute_unique_otus_per_sample(taxonomy_tree)
    compute_normalized_entropy_per_sample(taxonomy_tree)
    timer.checkpoint('end cohort basic metrics: ' + cohort_name)
    return


def compute_cohort_aggregates(cohort_def, taxonomy_tree,
        num_quantiles=8, num_bins=20, unique_otus_bin_max=20000, 
        timer=CheckpointTimer('cohort_aggregates')):
    """
    takes a cohort def (that includes the geno_sample ids in the cohort),
    and the master list of all geno_samples that were part of the tornado run.
    Also takes the otu defs and a copy of an AttributeTree that represents just
    the taxonomy.
    runs all the analytics for every node on the tree using the cohort's samples
    as input data and associates the outputs to attributes of the taxonomy tree
    nodes
    this method provides aggregates (or things like histogram bins) for metrics
    that are already assumed to have been computed by compute_cohort_metrics
    """
    cohort_name = cohort_def.get_value('display_name_short')
    timer.checkpoint('begin cohort aggregates: ' + cohort_name)

    compute_quantiles(taxonomy_tree, 'abundance_frac_per_sample', 
        'abundance_frac_quantiles', num_quantiles)

    compute_medians(taxonomy_tree, 'abundance_frac_quantiles',
        'abundance_frac_median')

    compute_means(taxonomy_tree, 'abundance_frac_per_sample',
        'abundance_frac_mean')

    compute_zero_separated_histograms(taxonomy_tree, 'abundance_frac_per_sample',
        'abundance_frac_histo', 0.0, 1.0, num_bins)

    compute_quantiles(taxonomy_tree, 'num_unique_otus_per_sample', 
        'num_unique_otus_quantiles', num_quantiles)

    compute_medians(taxonomy_tree, 'num_unique_otus_quantiles',
        'num_unique_otus_median')

    compute_means(taxonomy_tree, 'num_unique_otus_per_sample',
        'num_unique_otus_mean')

    compute_means(taxonomy_tree, 'normalized_entropy_per_sample',
        'normalized_entropy_mean')

    compute_zero_separated_histograms(taxonomy_tree, 'normalized_entropy_per_sample',
        'normalized_entropy_histo', 0.0, 1.0, num_bins)

    compute_pdf_scatterplots(taxonomy_tree, 
        'abundance_frac_quantiles', 'abundance_frac_density_plot')

    compute_pdf_scatterplots(taxonomy_tree, 
        'num_unique_otus_quantiles', 'num_unique_otus_density_plot')

    compute_zero_separated_histograms(taxonomy_tree, 'num_unique_otus_per_sample',
        'num_unique_otus_histo', 0.0, unique_otus_bin_max, num_bins)

    timer.checkpoint('end cohort aggregates: ' + cohort_name)
    #pretty_print_jdata(taxonomy_tree.to_jdata())
    return taxonomy_tree

def subset_samples_by_cohort(all_geno_samples, cohort_def):
    """
    find all of the actual samples that belong to a cohort from a list, given
    the cohort_def that has sample_ids. TODO: very n-squared loop
    """
    geno_sample_ids = cohort_def.get_value('sample_ids')
    geno_sample_lst = list()
    for sample_id in geno_sample_ids:
        for tornado_sample_key in all_geno_samples:
            geno_smp = all_geno_samples[tornado_sample_key]
            if geno_smp.get_nest_id().get_value() == sample_id:
                geno_sample_lst.append(geno_smp)
    assert(len(geno_sample_lst) == len(geno_sample_ids))
    return geno_sample_lst


def sum_gross_counts_per_sample(tree_root, otu_defs, geno_sample_defs):
    """
    for every (sample,otu) pair, retrieve the count from the sample
    and the taxonomy from the otu_def. add the count to every node
    in the taxonomy path at the entry for that sample in 
    the 'gross_count_per_sample' tree attribute
    """
    num_samples = len(geno_sample_defs)
    num_otus = len(otu_defs)
    tree_root.init_common_sparse_array_attribute('gross_count_per_sample', 
        num_samples, not_set_value=0.0)
    taxa_levels = list(otus.TAXONOMY_LEVELS)
    taxa_levels.append('otu_name')
    sample_idx = -1

    for geno_sample_def in geno_sample_defs:
        sample_idx = sample_idx + 1
        counts_ary = geno_sample_def.get_value('otu_counts')

        for otu_def in otu_defs:
            otu_idx = otu_def.get_value('index_within_tornado_run')
            otu_count = counts_ary.get_value(otu_idx)
            if otu_count == 0.0:
                continue
            
            taxa_level = 'root'
            taxa_node_name = 'root'
            current_node = tree_root
            root_counts = current_node.get_attribute('gross_count_per_sample')
            root_sample_count = root_counts.get_value(sample_idx)
            root_sample_count = root_sample_count + otu_count
            root_counts.set_value(sample_idx, root_sample_count)

            for taxa_level in taxa_levels:
                taxa_node_name = otu_def.get_value(taxa_level)
                current_node = current_node.find_child('node_name', taxa_node_name)
                node_counts = current_node.get_attribute('gross_count_per_sample')
                node_sample_count = node_counts.get_value(sample_idx)
                node_sample_count = node_sample_count + otu_count
                node_counts.set_value(sample_idx, node_sample_count)
    return 

def compute_abundance_frac_per_sample(tree_root):
    """
    tree must have the 'gross_count_per_sample' attribute already populated
    throughout the tree
    """
    root_gross_counts = tree_root.get_attribute('gross_count_per_sample')
    num_samples = len(root_gross_counts)
    tree_root.init_common_sparse_array_attribute('abundance_frac_per_sample', 
        num_samples, not_set_value=0.0)

    _rec_compute_abundance_frac_per_sample(tree_root, root_gross_counts)
    return

def _rec_compute_abundance_frac_per_sample(current_node, root_gross_counts):
    """ inner recursive loop for traversing tree and computing relative 
    abundance fractions
    """
    num_samples = len(root_gross_counts)
    node_gross_counts = current_node.get_attribute('gross_count_per_sample')
    node_abundance_fracs = current_node.get_attribute('abundance_frac_per_sample')
    for i in range(num_samples):
        root_count = root_gross_counts.get_value(i)
        node_count = node_gross_counts.get_value(i)
        if node_count > 0.0:
            abundance_frac = float(node_count) / float(root_count)
            node_abundance_fracs.set_value(i, abundance_frac)
    for child_tree in current_node.get_children():
        _rec_compute_abundance_frac_per_sample(child_tree, root_gross_counts)
    return

def generate_random_normalized_entropy_per_sample(tree):
    att_name = 'normalized_entropy_per_sample'
    gross_counts = tree.get_attribute('gross_count_per_sample')
    num_samples = len(gross_counts)
    normalized_entropies = SparseArray(num_samples, not_set_value=0.0)
    for i in range(num_samples):
        ent = random.uniform(0.0, 3.0)
        normalized_entropies.set_value(i, ent)
    tree.set_attribute(att_name, normalized_entropies)

    for child_tree in tree.get_children():
        generate_random_normalized_entropy_per_sample(child_tree)
    return

def compute_normalized_entropy_per_sample(tree):
    """
    this method sets the local value for the attribute
    'normalized_entropy_per_sample' but then also returns
    the set of all non-zero gross counts in the subtree so
    that it's parent can compute it's evenness

    the normalized_entropy is computed for every sample, 
    using all non-zero otu counts in the entire subtree below
    """
    att_name = 'normalized_entropy_per_sample'
    gross_counts = tree.get_attribute('gross_count_per_sample')
    num_samples = len(gross_counts)

    #list of lists. [sample_idx][nonzero_gross_count_x]
    nonzero_counts_per_sample = list()
    for i in range(num_samples):
        nonzero_counts_per_sample.append(list())

    if tree.is_leaf():
        for i in range(num_samples):
            otu_count = gross_counts.get_value(i)
            if otu_count > 0.0:
                nonzero_counts_per_sample[i].append(int(otu_count))
    else: 
        for child_tree in tree.get_children():
            child_matrix = compute_normalized_entropy_per_sample(child_tree)
            for i in range(num_samples):
                child_nonzero_counts_of_sample = child_matrix[i]
                current_nonzero_sample_counts = nonzero_counts_per_sample[i]
                #these are lists getting concatenated
                nonzero_counts_of_sample = (current_nonzero_sample_counts + 
                    child_nonzero_counts_of_sample)
                nonzero_counts_per_sample[i] = nonzero_counts_of_sample

    #this is a sparse array b/c that's what the histograms take, 
    #it's probably not actually sparse
    normalized_entropies = SparseArray(num_samples, not_set_value=0.0)
    for i in range(num_samples):
        nonzero_otu_counts =  nonzero_counts_per_sample[i]
        norm_entropy = _calc_normalized_entropy(nonzero_otu_counts)
        normalized_entropies.set_value(i, norm_entropy)
        #if tree.get_attribute('node_level') == 'phylum':
        #    log('nonzero counts list: ' + str(nonzero_otu_counts))
        #    log('norm entropy: ' + str(norm_entropy))

    tree.set_attribute(att_name, normalized_entropies)
    return nonzero_counts_per_sample

def _calc_normalized_entropy(list_of_numbers):
    """
    computes the normalized shannon's entropy of a group of numbers
    representing otu counts (that are nonzero)
    """
    num_otus = len(list_of_numbers)
    if  num_otus <= 1:
        norm_entropy = 0.0
    else:
        nary = numpy.array(list_of_numbers, dtype=numpy.int)
        entropy = skbio.diversity.alpha.shannon(nary, base=2)
        norm_entropy = entropy / float(num_otus)
    return norm_entropy

def compute_quantiles(tree, source_att_name, quantile_att_name, num_quantiles):
    """
    traverses a tree computing the quantiles of the data stored in one attribute
    (source_att_name) and creates a new attribute (quantile_att_name) where
    the value is a list of quantile levels.
    """
    #make a copy of the source values in a numpy ary and sort them
    source_vals = tree.get_attribute(source_att_name)
    quantiles = _quantiles_of_sparse_ary(source_vals, num_quantiles)
    tree.set_attribute(quantile_att_name, quantiles)
    for child_tree in tree.get_children():
        compute_quantiles(child_tree, source_att_name, quantile_att_name, 
            num_quantiles)
    return
   
def _quantiles_of_sparse_ary(sparse_ary, num_quantiles): 
    num_vals = len(sparse_ary)

    if num_vals == 0:
        #if there are no values in the sparse array, it's maybe
        #would be correct to raise an exception, but for now
        #return all zeros
        quantiles = [0] * (num_quantiles + 1)
        return quantiles

    source_npary = sparse_ary.to_npary()
    source_npary.sort()
    quantiles = list()
    #if 4 quantiles were requested, we return the values at
    #min, 25%, 50%, 75%, max
    mn = source_npary[0]
    mx = source_npary[num_vals - 1]
    quantiles.append(round(mn, 3))
    perc_boundaries = list()
    for i in range(1, num_quantiles):
        f = (float(i) * 100.0) / float(num_quantiles)
        perc_boundaries.append(f)
    #print('array fed to numpy: ' + str(source_npary))
    #print("perc boundaries: " + str(perc_boundaries))
    percentiles = numpy.percentile(source_npary, perc_boundaries)
    for p in percentiles:
        round_edge = round(p, 3)
        quantiles.append(round_edge)
    quantiles.append(round(mx, 10))

    if quantiles[len(quantiles) - 1] == 0.0 and mx > 0.0:
        print('rounded max quant down to zero: ' + str(mx))

    return quantiles

def compute_medians(tree, quantiles_att_name, median_att_name):
    """
    given a name of an attribute that contains quantiles (as a list)
    for all nodes in a tree, walks the tree and creates a new
    attribute at every node called median_att_name with the
    middle quantile level.
    """
    quant_levels = tree.get_attribute(quantiles_att_name)
    num_quants = len(quant_levels) - 1
    if num_quants % 2 == 1:
        raise Exception('finding medians only works with an even number of quantiles')
    #if there are 4 quantiles, the quant_levels are [min, 25%, 50%, 75%, max] and
    # we want the 50% for the median, or idx 2, which is num_quants / 2
    median_idx = num_quants / 2
    median = quant_levels[median_idx]
    round_median = round(median, 4)
    tree.set_attribute(median_att_name, round_median)
    for child_tree in tree.get_children():
        compute_medians(child_tree, quantiles_att_name, median_att_name)
    return

def compute_means(tree, numbers_att_name, mean_att_name):
    """
    given the name of an attribute that contains a sparse array
    of numbers, walks the tree and creates a new attribute at
    every node call mean_att_name, with a value that is the
    average (float)
    """
    numbers_ary = tree.get_attribute(numbers_att_name)
    count = len(numbers_ary)
    sum_x = 0.0
    for i in range(count):
        xi = numbers_ary.get_value(i)
        sum_x += xi
    mean = sum_x / (float(count))
    round_mean = round(mean, 4)
    tree.set_attribute(mean_att_name, round_mean)
    for child_tree in tree.get_children():
        compute_means(child_tree, numbers_att_name, mean_att_name)
    return

def compute_unique_otus_per_sample(tree):
    for child_tree in tree.get_children():
        compute_unique_otus_per_sample(child_tree)

    gross_counts = tree.get_attribute('gross_count_per_sample')
    num_samples = len(gross_counts)
    uniques_per_sample = SparseArray(num_samples, not_set_value=0)
    if tree.is_leaf():
        for i in range(num_samples):
            if gross_counts.get_value(i) > 0.0:
                num_uniques = 1
            else:
                num_uniques = 0
            uniques_per_sample.set_value(i, num_uniques)
    else:
        for i in range(num_samples):
            num_unique_otus = 0
            for child_tree in tree.get_children():
                child_num_uniques = child_tree.get_attribute('num_unique_otus_per_sample')
                child_num_unique = child_num_uniques.get_value(i)
                num_unique_otus = num_unique_otus + child_num_unique
            uniques_per_sample.set_value(i, num_unique_otus)
    tree.set_attribute('num_unique_otus_per_sample', uniques_per_sample)
    return

def find_effective_max_unique_otus(tree):
    """
    the effective maximum number of unique otus is the max seen
    at the phyla level
    """
    node_level = tree.get_attribute('node_level')

    #if above phylum in the tree, find the max of the children
    if node_level in ['root', 'kingdom']:
        child_maxes = list()
        for child_tree in tree.get_children():
            child_max = find_effective_max_unique_otus(child_tree)
            child_maxes.append(child_max)
        eff_max = max(child_maxes)
    elif node_level == 'phylum':
        uniques_per_sample = tree.get_attribute('num_unique_otus_per_sample')
        eff_max = uniques_per_sample.get_max()
    else:
        raise Exception("Can only find effective max given a tree at phyla or above")
    return eff_max

def compute_zero_separated_histograms(tree, numbers_att, output_att_prefix, 
    bucket_min_val, bucket_max_val, num_bins):
    """

    """
    raw_values = tree.get_attribute(numbers_att)
    non_zero_values = raw_values.extract_specified_values()
    num_raw_vals = len(raw_values)
    num_nonzero_vals = len(non_zero_values)
    num_zero_vals = num_raw_vals - num_nonzero_vals

    num_zeros_name = output_att_prefix + '_num_zeros'
    tree.set_attribute(num_zeros_name, num_zero_vals)
    
    nonzero_nary = numpy.array(non_zero_values)
    hist_vals, bin_edges = numpy.histogram(nonzero_nary,
        bins=num_bins,
        range=(bucket_min_val, bucket_max_val), 
        density=False)

    for i in range(len(bin_edges)):
        round_edge = round(bin_edges[i], 2)
        bin_edges[i] = round_edge
    bin_start_x_name = output_att_prefix + '_bin_start_x'
    bin_starts = list(bin_edges[:-1])
    tree.set_attribute(bin_start_x_name, bin_starts)

    bin_end_x_name = output_att_prefix + '_bin_end_x'
    bin_ends = list(bin_edges[1:])
    tree.set_attribute(bin_end_x_name, bin_ends)

    bin_height_name = output_att_prefix + '_bin_height_y'
    bin_heights = list(hist_vals)
    tree.set_attribute(bin_height_name, bin_heights)

    for child_tree in tree.get_children():
        compute_zero_separated_histograms(child_tree, numbers_att,
            output_att_prefix, bucket_min_val, bucket_max_val, num_bins)

    return tree

def compute_pdf_scatterplots(tree, quantiles_att, axes_att_prefix):
    """
    given the name of an attribute that is a quantiles list, compute
    two new lists for x and y axis values to use in a probability density
    plot. TODO: this should be moved into the frontend, but we're not ready
    for this type of calculation there yet

    axes_att_prefix (string): two new attributes will be created that
        are lists of numbers, 
            <axes_att_prefix>_x : [x1, x2, x3...]
            <axes_att_prefix>_y: [y1, y2, y3...]

    where the pdf plot can then be drawn by connecting the points [(x1,y1), (x2,y2), ...]
    
    all pdf's are on the same relative scale, meaning that if you multiply any 'y' value
    by the number of samples in that cohort, the values will then be on the same absolute
    scale. 
    """
    quantiles = tree.get_attribute(quantiles_att)
    x_vals, y_vals = _pdf_scatterplots_of_quantiles(quantiles)
    x_att_name = axes_att_prefix + '_x'
    y_att_name = axes_att_prefix + '_y'
    tree.set_attribute(x_att_name, x_vals)
    tree.set_attribute(y_att_name, y_vals)
    for child_tree in tree.get_children():
        compute_pdf_scatterplots(child_tree, quantiles_att, axes_att_prefix)
    return

def _pdf_scatterplots_of_quantiles(quantiles):

    if quantiles[0] == quantiles[-1]:
        #special case where all values are the same. nothing
        #sensible we can really do for a density plot
        x_points = [quantiles[0]]
        y_points = [1.0]
        return (x_points, y_points)

    num_levels = len(quantiles)
    num_quants = num_levels - 1
    #The midpoint of
    #each bucket will get a point in our scatterplot
    buckets = list() #each bucket will be a dict
    last_bucket_endpoint = quantiles[0]
    quant_level_idx = 1 #skip the min at quantiles[0]
    #log('quantiles : ' + str(quantiles))
    #log('num_levels : ' + str(num_levels))
    while quant_level_idx < num_levels:
        bucket = dict()
        bucket['start_point'] = last_bucket_endpoint
        bucket['num_units'] = 1
        bucket['end_point']= quantiles[quant_level_idx]
        last_bucket_endpoint = bucket['end_point']
        buckets.append(bucket)
        quant_level_idx += 1

    #log("init buckets")
    #log(str(buckets))

    #any buckets with the same start/end point need to be
    #merged into a neighbor 'bucket'. give the next bucket it's
    #num_units
    last_keeper_bucket = None
    for i in range(len(buckets)):
        bucket = buckets[i]
        if bucket['start_point'] == bucket['end_point']:
            if i < len(buckets) - 1:
                #normally merge with the next bucket
                neighbor_bucket = buckets[i+1]
            else:
                neighbor_bucket = last_keeper_bucket
            try:
                neighbor_bucket['num_units'] += bucket['num_units']
                last_keeper_bucket = neighbor_bucket
            except Exception as e:
                print("quantiles were: " + str(quantiles))
                print("buckets right now: " + str(buckets))
                print("i = " + str(i))
                raise e
            buckets[i] = None
        else:
            last_keeper_bucket = bucket

    #toss out any we just set to None b/c they got merged
    buckets = filter(None, buckets)

    #log("merged buckets")
    #log(str(buckets))
    for bucket in buckets:
        width = bucket['end_point'] - bucket['start_point']
        frac_of_pop = float(bucket['num_units']) / float(num_quants)
        unit_density = frac_of_pop / float(width)
        bucket['midpoint_height'] = unit_density
        midpoint = bucket['start_point'] + (0.5 * width)
        bucket['midpoint_x'] = midpoint
    
    x_points = list()
    y_points = list()

    #we ground the pdf at 0.0 at the min and max
    x_points.append(round(quantiles[0], 3))
    y_points.append(0.0)

    for bucket in buckets:
        x_points.append(round(bucket['midpoint_x'], 3))
        y_points.append(round(bucket['midpoint_height'], 3))

    #max
    x_points.append(round(quantiles[-1], 3))
    y_points.append(0.0)

    coords = (x_points, y_points)
    return coords

def log_empty_phyla_stats(cohort_tree):
    """
    looks at the phyla level abundance quantiles
    to determine how many phyla have few or very few
    samples (only the last quantile) that contain
    otus in that phyla. logs these numbers, they
    aren't part of the api
    """
    phyla_trees = _extract_phyla_subtrees(cohort_tree)
    totally_empty_count = 0
    only_one_quantile_count = 0
    not_empty_count = 0
    not_empty_names = list()
    kinda_empty_names = list()
    totally_empty_names = list()
    num_quants = 0
    for phyla_tree in phyla_trees:
        quants = phyla_tree.get_attribute('abundance_frac_quantiles')
        num_quants = len(quants) - 1
        last_quant_idx = len(quants) - 1
        next_to_last_quant_idx = last_quant_idx - 1
        phylum_name = phyla_tree.get_attribute('node_name')
        if quants[last_quant_idx] == 0.0:
            totally_empty_count += 1
            totally_empty_names.append(phylum_name)
        elif quants[next_to_last_quant_idx] == 0.0:
            only_one_quantile_count += 1
            kinda_empty_names.append(phylum_name)
        else:
            not_empty_count += 1
            not_empty_names.append(phylum_name)

    not_empty_names.sort()
    totally_empty_names.sort()
    kinda_empty_names.sort()
    #assume num_quants is the same for all of them
    quant_frac = float(num_quants - 1) / float(num_quants)
    one_quant_empty_str = str(int(quant_frac * 100.0)) + '%'
    msg = 'Not empty: ' + str(not_empty_count)
    msg += ', ' + one_quant_empty_str + ' empty: ' + str(only_one_quantile_count)
    msg += ', totally empty: ' + str(totally_empty_count)
    log(msg)
    log('Not     empty phyla: ' + str(not_empty_names))
    log('97%     empty phyla: ' + str(kinda_empty_names))
    log('Totally empty phyla: ' + str(totally_empty_names))
    return

def _extract_phyla_subtrees(tree):
    phyla_subtrees = list()
    node_level = tree.get_attribute('node_level')
    if  node_level == 'phylum':
        phyla_subtrees.append(tree)
    else:
        for child_tree in tree.get_children():
            phyla_subtrees = phyla_subtrees + _extract_phyla_subtrees(child_tree)
    return phyla_subtrees
    

def log(msg):
    print(msg)
