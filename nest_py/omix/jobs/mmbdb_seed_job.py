from nest_py.core.jobs.jobs_logger import log
from nest_py.core.jobs.checkpoint import CheckpointTimer
import nest_py.ops.container_users as container_users
import nest_py.core.jobs.jobs_auth as jobs_auth
import nest_py.core.db.nest_db as nest_db

import nest_py.omix.jobs.biom_etl as biom_etl
import nest_py.omix.jobs.fst_etl as fst_etl
import nest_py.omix.jobs.cohort_etl as cohort_etl
import nest_py.omix.jobs.comparison_etl as comparison_etl
import nest_py.omix.jobs.comparison_tree_etl as comparison_tree_etl

import nest_py.omix.jobs.otu_analysis as otu_analysis
import nest_py.omix.jobs.cohort_analysis as cohort_analysis
import nest_py.omix.jobs.comparison_analysis as comparison_analysis
import nest_py.omix.jobs.client_registry as client_registry

import nest_py.omix.jobs.seed_data as mmbdb_seed_data
from nest_py.omix.jobs.klumpp_ic1_data import KlumppIC1SeedData
from nest_py.omix.jobs.klumpp_ic2_data import LizzieSeedData
from nest_py.omix.jobs.klumpp_ic2_data import WenbinFecalSeedData
from nest_py.omix.jobs.klumpp_ic2_data import WenbinCecumSeedData
from nest_py.omix.jobs.klumpp_ic2_data import WenbinCombinedSeedData
from nest_py.omix.jobs.mayo_mar16_data import MayoMar16SeedData
from nest_py.omix.jobs.mayo_microbiome_report_sample_data import \
    MayoMicrobiomeReportSampleSeedData


#num quantiles used for relative abundance,richness, and evenness.
#this also determines how many points will be in density_plot coordinates
#which are derived from the quantiles
NUM_QUANTILES = 4 #only use even numbers or the 'median' values will be wrong

#used by all histograms
NUM_BINS = 20

#if true, populates the cohort_phylo_tree_nodes and comparison_phylo_tree_nodes
#with analytics output for all defined chorts and comparisons. if false,
#stops after the definitions are uploaded, which included FST analysis
DO_TREE_ANALYTICS = True

#True to use DB clients, False to use API clients
DB_VS_API = True

def run(http_client, db_engine, data_dir, subsample, data_flavor_key):
    """
    db_engine, sqla_md (sqlalchemy.Engine): a postgres hook to the
        db we will use. Tables must already exist in the db.
    data_dir (string): location to write data files
    subsample (bool) if true, only load a 100 samples from the biom_table
        and process. results will not be valid but all api endpoints will
        be populated with data
    """
    timer = CheckpointTimer('mmbdb_seed')
    timer.checkpoint("mmbdb_seed_job: Begin")
    exit_code = 0

    host_user = container_users.make_host_user_container_user()
    seed_data = get_data_flavor(data_flavor_key, data_dir, host_user, subsample)
    ###############
    ##Connect CRUD clients
    ################
    nest_username = seed_data.get_username()
    nest_userpass = seed_data.get_userpass()
    if DB_VS_API:
        sqla_md = nest_db.get_global_sqlalchemy_metadata()
        clients = client_registry.make_db_client_registry(db_engine, sqla_md)
        for client in clients.values():
            jobs_auth.set_db_user(client, nest_username)
    else:
        jobs_auth.login_jobs_user(http_client, nest_username, nest_userpass)
        clients = client_registry.make_api_client_registry(http_client)

    ###################
    ##Download Raw Data
    ###################

    timer.checkpoint("Downloading biom data if necessary")
    biom_table = seed_data.get_biom_table()
    timer.checkpoint("Download complete.")
    timer.checkpoint("Downloaded/Loaded All Patient Metadata")

    ####################
    ##Upload Primitive Data
    ####################

    timer.checkpoint('uploading tornado_run: Begin')
    tornado_cfg = seed_data.get_tornado_config()
    tornado_run_tle = biom_etl.upload_tornado_run(clients, biom_table, tornado_cfg)
    tornado_run_id = tornado_run_tle.get_nest_id()
    timer.checkpoint('uploading tornado_run: End')

    timer.checkpoint('uploading otu_defs: Begin')
    otu_defs = biom_etl.upload_otu_defs(clients, biom_table, tornado_run_id)
    timer.checkpoint('uploading otu_defs: End')

    timer.checkpoint('uploading geno_samples: Begin')
    geno_samples = biom_etl.upload_geno_samples(clients, biom_table, \
        tornado_run_id, otu_defs)
    timer.checkpoint('uploading geno_samples: End')

    ####################
    #Define Cohorts
    ####################
    all_cohort_tles = dict()

    cohort_configs = seed_data.get_cohort_configs()

    for cohort_config in cohort_configs:
        cohort_key = cohort_config['display_name_short']
        timer.checkpoint('uploading cohort: ' + str(cohort_key))
        tornado_sample_keys = seed_data.get_tornado_sample_keys(
            cohort_key)
        sample_ids = cohort_etl.tornado_sample_keys_to_nest_ids(
            tornado_sample_keys, geno_samples)
        cohort_tle = cohort_etl.upload_cohort(clients, \
            cohort_config, sample_ids, tornado_run_id)
        all_cohort_tles[cohort_key] = cohort_tle


    ####################
    ##Define Comparisons
    ####################
    all_comparisons = list()

    comparison_configs = seed_data.get_comparison_configs()

    for comparison_config in comparison_configs:
        comparison_key = comparison_config['comparison_key']
        baseline_key = comparison_config['baseline_cohort_key']
        baseline_cohort_tle = all_cohort_tles[baseline_key]
        variant_key = comparison_config['variant_cohort_key']
        variant_cohort_tle = all_cohort_tles[variant_key]
        patient_key = comparison_config['patient_cohort_key']
        patient_cohort_tle = all_cohort_tles[patient_key]

        timer.checkpoint('fst begin for: ' + comparison_key)
        fst_results = fst_etl.get_fst_of_comparison(
            comparison_key,
            seed_data,
            baseline_cohort_tle,
            variant_cohort_tle,
            otu_defs,
            geno_samples,
            data_dir,
            host_user)

        timer.checkpoint('api upload begin: ' + comparison_key)
        comparison_tle = comparison_etl.upload_comparison(
            clients,
            comparison_config,
            baseline_cohort_tle,
            variant_cohort_tle,
            patient_cohort_tle,
            fst_results)
        timer.checkpoint('api upload done')

        all_comparisons.append(comparison_tle)

    if DO_TREE_ANALYTICS:

        ###############
        ###Cohort Node Analytics
        ###############
        #this also does the upload asap to reduce memory footprint
        cohort_analysis.compute_all_for_cohorts(clients, \
            all_cohort_tles.values(), \
            geno_samples, otu_defs, num_quantiles=NUM_QUANTILES, \
            num_bins=NUM_BINS, timer=timer)

        ###############
        ###Comparison Node Analytics
        ###############
        taxonomy_empty_tree = otu_analysis.compute_taxonomy_tree(otu_defs)
        for comp in all_comparisons:
            tree = taxonomy_empty_tree.copy()
            log('begin analytics for comparison: ' + comp.get_value('display_name'))
            timer.checkpoint('computing comparison analytics:begin')
            comparison_analysis.compute_all(comp, otu_defs, tree)
            timer.checkpoint('computing comparison analytics:end')

            timer.checkpoint('uploading comparison analytics nodes:begin')
            comparison_tree_etl.upload_nodes(clients, comp, tree)
            timer.checkpoint('uploading comparison analytics nodes:end')

    timer.checkpoint("mmbdb_seed_job: Done")
    return exit_code

def get_data_flavor(data_flavor_key, data_dir, file_owner, subsample):
    if data_flavor_key in mmbdb_seed_data.VALID_SEED_FLAVORS:
        if data_flavor_key == 'mayo_mar16':
            seed_data = MayoMar16SeedData(
                data_dir, file_owner, subsample=subsample)
            seed_data.get_patient_data() #prefetch
        if data_flavor_key == 'mayo_microbiome_report':
            seed_data = MayoMicrobiomeReportSampleSeedData(data_dir, file_owner)
        elif data_flavor_key == 'klumpp_ic1':
            seed_data = KlumppIC1SeedData(data_dir, file_owner)
        elif data_flavor_key == 'klumpp_ic2_lizzie':
            seed_data = LizzieSeedData(data_dir, file_owner)
        elif data_flavor_key == 'klumpp_ic2_wenbin_fecal':
            seed_data = WenbinFecalSeedData(data_dir, file_owner)
        elif data_flavor_key == 'klumpp_ic2_wenbin_cecum':
            seed_data = WenbinCecumSeedData(data_dir, file_owner)
        elif data_flavor_key == 'klumpp_ic2_wenbin_combined':
            seed_data = WenbinCombinedSeedData(data_dir, file_owner)
        else:
            raise Exception('this shouldnt happen')
    else:
        raise Exception("Not a valid data flavor: " + str(data_flavor_key))
    print("Using seed data flavor: " + data_flavor_key)

    #warm up caches
    seed_data.get_biom_table()
    seed_data.get_comparison_configs()
    cohorts = seed_data.get_cohort_configs()
    for cfg in cohorts:
        seed_data.get_tornado_sample_keys(cfg['display_name_short'])
    comps = seed_data.get_comparison_configs()
    for cfg in comps:
        seed_data.get_fst_results_cache_url(cfg['comparison_key'])
    return seed_data
