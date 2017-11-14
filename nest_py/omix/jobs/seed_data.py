VALID_SEED_FLAVORS = ['mayo_mar16', 'klumpp']
DEFAULT_SEED_FLAVOR = 'mayo_mar16'

class SeedFlavorData(object):
    """
    abstract class that defines the data (otus, patient data) and
    configs (cohorts and comparisons) for the mmbdb seed job

    This is likely to change rapidly as new data sets and
    functionality are added. It's also a long way from being
    a durable interface as lots of quirks in the mayo data are
    expected to be there.

    See sublcasses (klump, mayo_mar16) for examples of how to implement.
    """

    def __init__(self):
        return

    def get_biom_table(self):
        """
        The biom table (http://biom_format.org) contains the
        otu observations per sample. The meta data is expected
        to contain the taxonomy data per OTU/observation, 
        and often has some minimal metadata per sample that
        may be used by get_tornado_sample_keys 
        """
        raise Exception('Abstract class. Not implemented')
        return None

    def get_cohort_configs(self):
        """
        a list of cohort configs:

        a cohort_config is a dict with the following fields:
            'display_name_short',
            'display_name_long',
            'query'

        note that 'display_name_short' is used a 'cohort_key'
        throughout the codebase as a unique key for every cohort
        """
        raise Exception('Abstract class. Not implemented')
        return None

    def get_comparison_configs(self):
        """
        a list of comparison configs.

        a comparison config is a dict with these fields:
            'comparison_key'
            'display_name'
            'baseline_cohort_key'
            'variant_cohort_key'
            'patient_cohort_key'

        Note that the XXXX_cohort_key fields all take a value that
        is a 'display_name_short' in get_cohort_configs
        """
        raise Exception('Abstract class. Not implemented')
        return None

    def get_fst_results_cache_url(self, comparison_key):
        """
        given a comparison_key for one of the comparison_configs
        returned by get_comparison_configs(), this returns 
        a URL on box of the FeatureSelectionTool output, or None
        if one doesn't exist. (If this returns None, the seed
        job will run the FST analysis, which can take hours
        on a large data set)

        """
        raise Exception('Abstract class. Not implemented')
        return None
    
    def get_tornado_sample_keys(self, cohort_key):
        """
        Given a cohort_key (display_name_short), returns a list
        of strings that are the 'id's of the samples in the
        biom_table. 

        This step will eventually be replaced by a query that
        can be saved in the cohort_config itself (there is already
        a 'query' field in cohort_configs, but that is just for
        documentation purposes, the actual query must be manually
        implemented in python code here, for every cohort)
        """
        raise Exception('Abstract class. Not implemented')
        return None
 
