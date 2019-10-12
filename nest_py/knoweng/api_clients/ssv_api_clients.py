from nest_py.core.api_clients.tablelike_api_client_maker import TablelikeApiClientMaker
import nest_py.knoweng.data_types.ssviz_jobs_spreadsheets as ssviz_jobs_spreadsheets
import nest_py.knoweng.data_types.ssviz_feature_correlations as ssviz_feature_correlations
import nest_py.knoweng.data_types.ssviz_feature_data as ssviz_feature_data
import nest_py.knoweng.data_types.ssviz_feature_variances as ssviz_feature_variances
import nest_py.knoweng.data_types.ssviz_spreadsheets as ssviz_spreadsheets

# SSV endpoints don't allow PATCH or POST
class SsvizGenericClientMaker(TablelikeApiClientMaker):

    def run_smoke_scripts(self, http_client, result_acc):
        result_acc.add_report_line(\
            'BEGIN smoke for ' + self.get_collection_name())
        crud_client = self.get_crud_client(http_client)
        filter_results = crud_client.simple_filter_query({}, max_results=1)
        # expecting 0 or 1 results
        # more than 1 would be a surprise; an exception (caught by smoke test
        # internals) is probably the more likely failure mode
        if len(filter_results) > 1:
            result_acc.set_success(False)
            result_acc.add_report_line(\
                "Got " + str(len(filter_results)) + "results.")
        result_acc.add_report_line(\
            'END smoke for ' + self.get_collection_name())

class SsvizJobsSpreadsheetsClientMaker(SsvizGenericClientMaker):

    def __init__(self):
        schema = ssviz_jobs_spreadsheets.generate_schema()
        super(SsvizJobsSpreadsheetsClientMaker, self).__init__(schema)

class SsvizRowCorrelationsClientMaker(SsvizGenericClientMaker):

    def __init__(self):
        schema = ssviz_feature_correlations.generate_schema()
        super(SsvizRowCorrelationsClientMaker, self).__init__(schema)

class SsvizRowDataClientMaker(SsvizGenericClientMaker):

    def __init__(self):
        schema = ssviz_feature_data.generate_schema()
        super(SsvizRowDataClientMaker, self).__init__(schema)

class SsvizRowVariancesClientMaker(SsvizGenericClientMaker):

    def __init__(self):
        schema = ssviz_feature_variances.generate_schema()
        super(SsvizRowVariancesClientMaker, self).__init__(schema)

class SsvizSpreadsheetsClientMaker(SsvizGenericClientMaker):

    def __init__(self):
        schema = ssviz_spreadsheets.generate_schema()
        super(SsvizSpreadsheetsClientMaker, self).__init__(schema)
