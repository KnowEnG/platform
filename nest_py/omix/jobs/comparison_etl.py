"""
routines for defining some know (hardcoded) comparisons
and uploading their definitions (but not analytics) to the api

tightly coupled to mmbdb_seed_job
"""

import nest_py.omix.data_types.cohort_comparisons as cohort_comparisons
import nest_py.core.data_types.tablelike_entry as tablelike_entry

def upload_comparison(client_registry, comparison_config, 
    baseline_cohort_tle, variant_cohort_tle, patient_cohort_tle,
    fst_results):
    print("uploading comparison: " + str(comparison_config['comparison_key']))

    comps_schema = cohort_comparisons.generate_schema()
    comps_client = client_registry[cohort_comparisons.COLLECTION_NAME]
    
    tle = tablelike_entry.TablelikeEntry(comps_schema)
    tle.set_value('display_name', comparison_config['display_name'])

    baseline_id = baseline_cohort_tle.get_nest_id().get_value()
    tle.set_value('baseline_cohort_id', baseline_id)

    variant_id = variant_cohort_tle.get_nest_id().get_value()
    tle.set_value('variant_cohort_id', variant_id)

    patient_id = patient_cohort_tle.get_nest_id().get_value()
    tle.set_value('patient_cohort_id', patient_id)

    _set_top_fst_scores(tle, fst_results)

    tle = comps_client.create_entry(tle)
    assert(not tle is None)
    return tle

def _set_top_fst_scores(comp_tle, fst_results):
    ranked_otu_ids = list()
    otu_scores = list()
    for blob in fst_results:
        otu_id = blob['otu_tle'].get_nest_id().get_value()
        ranked_otu_ids.append(otu_id)
        score = blob['display_score']
        otu_scores.append(score)

    comp_tle.set_value('top_fst_ranked_otu_ids', ranked_otu_ids)
    comp_tle.set_value('top_fst_ranked_otu_scores', otu_scores)
    return

