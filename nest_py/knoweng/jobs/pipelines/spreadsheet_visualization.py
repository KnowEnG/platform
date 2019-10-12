"""
This module defines a class for running knoweng's spreadsheet visualization jobs.

IMPORTANT NOTE: On screen, features correspond to rows and samples correspond to
columns. In dataframes in this file, however, features correspond to columns and
samples correspond to rows, because pandas columns share a data type.

TODO: Change portions of client code to "attribute" or "feature" and "sample"
(or something along those lines)--but perhaps wait on all of that until
unifying this code with the Omix data model.

"""

import logging
import os
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np
import pandas as pd
from scipy import stats

from lifelines.statistics import multivariate_logrank_test

from nest_py.knoweng.jobs.db_utils import get_file_record, \
    get_ssviz_spreadsheets_by_ids, get_ssviz_spreadsheets_by_file_ids, \
    get_ssviz_feature_data, create_ssviz_spreadsheet_and_feature_data, \
    create_ssviz_jobs_spreadsheets_entries, \
    create_ssviz_feature_variances_entry, \
    get_ssviz_spreadsheets_with_correlations, \
    create_ssviz_feature_correlations_entry

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

# the minimum allowable fraction of overlapping sample ids between spreadsheets
MIN_WORST_SCORE = 0.5

# the maximum allowable number of distinct values for a categoric feature
# a non-numeric feature with more distinct values will be treated as free text
# and assigned the type "other"
# when changing this number, make sure there are enough colors in
# HeatmapPane.categoricalPalette
MAX_UNIQUE_CATEGORICAL_VALUES = 15

class SpreadsheetVisualizationJob(object):

    """Local job that handles spreadsheet visualization."""
    def __init__(self, user_id, job_id, project_id, userfiles_dir,\
        job_dir_relative_path, job_name, spreadsheet_nest_ids):
        """Initializes self.

        Args:
            user_id (NestId): The user id associated with the job.
            job_id (NestId): The job id associated with the job.
            project_id (NestId): The project id associated with the job.
            userfiles_dir (str): The base directory containing all files for
                all users.
            job_dir_relative_path (str): The relative path from userfiles_dir
                to the directory containing the job's files, which must already
                exist.
            job_name (str): The job name.
            spreadsheet_nest_ids: The data files in the job

        Returns:
            None: None.

        """
        self.user_id = user_id
        self.job_id = job_id
        self.project_id = project_id
        self.userfiles_dir = userfiles_dir
        self.job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)
        self.job_name = job_name
        self.spreadsheet_nest_ids = spreadsheet_nest_ids
        self.started = False
        self.error_message = None

        # self.spreadsheets is array of dicts
        # each dict has keys file_id, filename, is_file_samples_as_rows,
        # sample_names, feature_names, feature_types, df, is_new_to_db,
        # variances (if eligible for primary heatmap), and
        # ssviz_spreadsheet_id
        # it'll be populated as self.spreadsheet_nest_ids are processed
        self.spreadsheets = []

    def start(self):
        """Processes all spreadsheet data to populate database tables.

        Returns:
            None: None.

        """
        self.process_data()
        if not self.is_failed():
            self.prepare_zip_file()
        self.started = True

    def is_started(self):
        """Returns True if the job has been started, else returns False. Note
        this will continue to return True even after the job has finished.

        Returns:
            boolean: True if the job has been started, else False.

        """
        return self.started

    def get_command(self):
        pass

    def is_ready(self):
        """Always returns True."""
        return True

    def is_failed(self):
        """Returns True if this job reported an error."""
        return self.get_error_message() is not None

    def get_error_message(self):
        """Returns the error messages reported by the pipeline, if any."""
        return self.error_message

    def is_done(self):
        """Returns true iff all of the database records have been created."""
        return self.started

    def on_done(self):
        """Does nothing."""
        pass

    def process_data(self):
        """Processes all data, populating DB."""
        # partially populate self.spreadsheets--file_id, df
        self.load_spreadsheets()
        # continue populating self.spreadsheets--is_file_samples_as_rows,
        # sample_names, feature_names, feature_types; note this can also
        # transpose the data frames
        if not self.is_failed():
            self.validate_spreadsheet_files()
        # count missing values per feature and per sample
        if not self.is_failed():
            self.count_missing_values()
        # TODO start a DB transaction--need to limit its scope to this job only
        # check/populate ssviz_spreadsheets table, along with
        # ssviz_spreadsheet_id and is_new_to_db in self.spreadsheets
        if not self.is_failed():
            self.record_spreadsheets()
        # check/populate ssviz_feature_variances
        if not self.is_failed():
            self.calculate_and_record_variances()
        # check/populate ssviz_feature_correlations
        if not self.is_failed():
            self.calculate_and_record_correlations()
        # TODO commit DB transaction

    def load_spreadsheets(self):
        """Reads files into dataframes and partially populates self.spreadsheets
        with file_id and df values.

        """
        for ssf_id in self.spreadsheet_nest_ids:
            ssf_dto = get_file_record(self.user_id, ssf_id)
            ssf_path = ssf_dto.get_file_path(self.userfiles_dir)

            input_df = SpreadsheetVisualizationJob._load_spreadsheet(ssf_path)

            self.spreadsheets.append({\
                "file_id": ssf_id,
                "filename": ssf_dto.filename,
                "df": input_df})

    @staticmethod
    def _load_spreadsheet(ssf_path):
        """Reads one file into a dataframe, attempting some data cleanup along
        the way. Broken out into a static method for ease of testing.

        Args:
            ssf_path (str): The path to the spreadsheet.

        Returns:
            pandas.DataFrame: A dataframe containing the spreadsheet data.

        """
        # A few comments on reading the spreadsheet:
        # 1. The spreadsheet might use row numbers as labels # TODO handle
        # 2. The spreadsheet might use "NA"-like strings as labels
        # 3. There might be duplicates among the row labels and/or column
        #    labels. Note we set mangle_dupe_cols to False. We don't want
        #    to mangle yet, because we don't know at this point which
        #    dimension corresponds to samples and which corresponds to
        #    features. Once we figure out the correct orientation, we'll
        #    drop duplicate samples (because we won't know how to join
        #    them properly across speadsheets--unless we have only one
        #    spreadsheet), and we'll name-mangle duplicate features (because
        #    there's no joining to do, and while mangled names could confuse
        #    the user, the UI provides enough clues to disambiguate if the
        #    user is tracing back to the original file).
        #    see `_clean_duplicate_features_and_samples()`
        input_df = pd.read_csv(\
            ssf_path, sep='\t', index_col=0, header=0,
            mangle_dupe_cols=False, error_bad_lines=False,
            warn_bad_lines=True)

        # check for column labels treated as NaN
        nan_column_labels = pd.isnull(input_df.columns)
        if True in nan_column_labels:
            # replace the column labels
            with open(ssf_path) as infile:
                line = infile.readline().rstrip()
                headers = line.split("\t")
                # user's file might or might not have had label on first column
                start_index = len(headers) - len(nan_column_labels)
                input_df.columns = headers[start_index:]

        # check for row labels treated as NaN
        nan_row_labels = pd.isnull(input_df.index)
        if True in nan_row_labels:
            # replace the row labels
            # don't re-parse every row, every column
            # (still room for improvement here)
            row_index = -1 # first row of file is headers
            with open(ssf_path) as infile:
                for line in infile:
                    if row_index >= 0 and nan_row_labels[row_index]:
                        row_label = line.split("\t")[0]
                        input_df.index.values[row_index] = row_label
                    row_index += 1

        return input_df

    @staticmethod
    def _test_label_intersections(labels_to_match, files_metadata):
        """Determines the overlap between `labels_to_match` and the rows and
        columns for each of the elements in `files_metadata`.

        Args:
            labels_to_match (list(str)): The sample ids to match.
            files_metadata (list(dict)): A list of dictionaries as populated by
                the `validate_spreadsheet_files` method. Each dictionary should
                contain keys 'column_names' and 'row_names'.

        Returns:
            list(dict): A list of dictionaries, one per element in
                `files_metadata`. Each dictionary will contain keys
                'column_score' and 'row_score'.

        """
        return_val = []
        ref_set = set(labels_to_match)
        for metadata in files_metadata:
            # calculate fraction of labels shared between `labels_to_match` and
            # the rows and columns for this file
            # TODO could factor out row/col commonalities
            row_max = max(len(metadata['row_names']), len(ref_set))
            column_max = max(len(metadata['column_names']), len(ref_set))
            row_intersection = len(set(metadata['row_names']) & ref_set)
            column_intersection = len(set(metadata['column_names']) & ref_set)
            row_score = row_intersection / (1.0 * row_max) if \
                row_max > 0 else 0
            column_score = column_intersection / (1.0 * column_max) if \
                column_max > 0  else 0
            return_val.append({\
                'row_score': row_score, 'column_score': column_score})
        return return_val

    @staticmethod
    def _get_feature_types_and_cleaned_df(input_df, drop_duplicate_samples):
        """Determines the feature type for each feature in `input_df`.

        Args:
            input_df (pandas.DataFrame): The data frame.
            drop_duplicate_samples (boolean): Whether to drop duplicate samples;
                use True if there are multiple spreadsheets in the job, else
                use False if there's only one spreadsheet in the job.

        Returns:
            list(str): A list of strings, one per feature in `input_df`. Each
            string will be either "numeric", "categoric", or "other".
            pd.DataFrame: The cleaned dataframe.

        """
        # TODO case to consider: numerically-coded categoric data. Raises
        # other questions, too. For example, consider a somatic mutation
        # df in which all values are 0, 1, or NaN. If we consider it
        # categoric, what rules should we relax to allow it as a
        # primary heatmap?

        # short-term handling of numerically-coded categoric:
        # goal: if feature.nunique <= MAX_UNIQUE_CATEGORICAL_VALUES, treat
        #   as categoric unless the whole sheet is numeric
        # solution:
        # - attempt to convert all features to numeric
        # - if all features in sheet are numeric AND sheet has more than
        #     one feature, stop
        # - else attempt to convert each feature to categoric
        # (this is what we'll do below)

        # TODO: medium-term handling of numerically-coded categoric:
        # - if feature.nunique <= MAX_UNIQUE_CATEGORICAL_VALUES, treat as
        #     categoric
        # - if sheet.nunique (that is, pooling all values from all rows),
        #     <= MAX_UNIQUE_CATEGORICAL_VALUES, the sheet is main-heatmap
        #     eligible (need agreement on variance analog)

        feature_types = []
        clean_df = SpreadsheetVisualizationJob.\
            _clean_duplicate_features_and_samples(\
                input_df.copy(), drop_duplicate_samples)

        # short-term step 1: attempt to convert all features to numeric
        for feature_name in clean_df:
            clean_df[feature_name] = pd.to_numeric(\
                clean_df[feature_name], errors='ignore')
            # at this point, just distinguish other and numeric
            feature_type = "other"
            if np.issubdtype(clean_df[feature_name].dtype, np.number):
                feature_type = "numeric"
            feature_types.append(feature_type)

        # short-term step 2: if all features in sheet are numeric and sheet has
        # more than one feature, stop
        unique_types = list(set(feature_types))
        if len(feature_types) > 1 and unique_types == ['numeric']:
            pass
        # short-term step 3: else attempt to convert each feature to categoric
        else:
            for feature_idx, feature_name in enumerate(clean_df):
                feature = clean_df[feature_name]
                nunique = feature.nunique()
                # if all values are NaN, treat as other to prevent problems
                # calculating correlations, where we discard missing values
                # pandas discards NaN when reporting unique features, too, so
                # we're looking for the case of nunique == 0
                if nunique == 0:
                    feature_types[feature_idx] = "other"
                elif nunique <= MAX_UNIQUE_CATEGORICAL_VALUES:
                    feature_types[feature_idx] = "categoric"
                    # TODO: consider consequences of this:
                    # clean_df[feature_name] = \
                    #     clean_df[feature_name].astype('category')
        return feature_types, clean_df

    @staticmethod
    def _clean_duplicate_features_and_samples(input_df, drop_duplicate_samples):
        """Examines dataframes for duplicate sample names and duplicate feature
        names. Handles them like so:
            - We'll name-mangle duplicate feature names, because the UI needs
              unique feature names per file. The user will have enough info on
              screen to de-mangle the names w.r.t. the original spreadsheet.
            - If there's only one spreadsheet, we'll name-mangle duplicate
              sample names, because some of the processing in this module
              requires unique sample names per dataframe. The user will have
              enough info on screen to de-mangle the names w.r.t. the original
              spreadsheet.
            - If there are multiple spreadsheets, we'll drop duplicate sample
              names, because we won't know how to join them properly across
              spreadsheets.

        Args:
            input_df (pandas.DataFrame): The data frame.
            drop_duplicate_samples (boolean): Whether to drop duplicate samples;
                use True if there are multiple spreadsheets in the job, else
                use False if there's only one spreadsheet in the job.

        Returns:
            pd.DataFrame: The cleaned dataframe.

        """
        # this method assumes the DF is oriented such that columns correspond
        # to features; note callers might still be in the process of determining
        # the proper orientation, and that's ok
        original_feature_names = input_df.columns.tolist()
        original_sample_names = input_df.index.tolist()
        # name-mangle any duplicate feature names
        fname_counts = {}
        for idx, fname in enumerate(original_feature_names):
            if fname in fname_counts:
                fname_counts[fname] += 1
                new_name = fname + "." + str(fname_counts[fname])
                input_df.columns.values[idx] = new_name
            else:
                fname_counts[fname] = 0
        # name-mangle or drop any duplicate sample names
        sname_counts = {}
        duplicate_samples = [] # tracking in case we need to drop
        for idx, sname in enumerate(original_sample_names):
            if sname in sname_counts:
                sname_counts[sname] += 1
                new_name = sname + "." + str(sname_counts[sname])
                input_df.index.values[idx] = new_name
                duplicate_samples.append(new_name)
            else:
                sname_counts[sname] = 0
        if drop_duplicate_samples:
            input_df.drop(labels=duplicate_samples, axis=0, inplace=True)
        return input_df

    def validate_spreadsheet_files(self):
        """Validates spreadsheets and continues populating self.spreadsheets:
        is_file_samples_as_rows, sample_names, feature_names, feature_types.
        Note this can also transpose the data frames.

        """
        # if we have more than one spreadsheet, we need to determine a common
        # set of sample identifiers and detect/correct spreadsheet orientations.
        # remember, we want samples to correspond to columns on screen, but in
        # the dataframes here, we need samples to be row indices.
        # TODO move this code so other pipelines can use it, too
        if len(self.spreadsheets) > 1:
            all_file_meta_data = [\
                {
                    "row_names": ss_dict["df"].index.tolist(),
                    "column_names": ss_dict["df"].columns.tolist()
                } for ss_dict in self.spreadsheets]
            # we'll consider two cases:
            # 1. first spreadsheet has samples as columns
            # 2. first spreadsheet has samples as rows
            first_md = all_file_meta_data[0]
            other_mds = all_file_meta_data[1:]
            # determine sample id overlap scores for the two cases
            scores_if_first_has_samples_as_columns = \
                SpreadsheetVisualizationJob._test_label_intersections(\
                    first_md['column_names'], other_mds)
            scores_if_first_has_samples_as_rows = \
                SpreadsheetVisualizationJob._test_label_intersections(\
                    first_md['row_names'], other_mds)
            # find the worst score associated with the two cases
            # worst score is the lowest over all the spreadsheets
            # we still take the max per spreadsheet, because we allow ourselves
            # to transpose any spreadsheet in other_mds
            worst_score_if_first_has_samples_as_columns = min([\
                max(score_dict['column_score'], score_dict['row_score']) for\
                score_dict in scores_if_first_has_samples_as_columns])
            worst_score_if_first_has_samples_as_rows = min([\
                max(score_dict['column_score'], score_dict['row_score']) for\
                score_dict in scores_if_first_has_samples_as_rows])
            if worst_score_if_first_has_samples_as_columns < MIN_WORST_SCORE \
                and worst_score_if_first_has_samples_as_rows < MIN_WORST_SCORE:
                # TODO make error message more specific (Xiaoxia's was better)
                # gets a little complicated now, because it could be that the
                # first spreadsheet is the offender
                self.error_message = 'Invalid data: Spreadsheets must have ' + \
                    'common sample identifiers.'
                return
            # determine orientation of first spreadsheet
            elif worst_score_if_first_has_samples_as_columns < MIN_WORST_SCORE:
                # the only viable solution is that first spreadsheet has samples
                # as rows
                first_md['is_file_samples_as_rows'] = True
            elif worst_score_if_first_has_samples_as_rows < MIN_WORST_SCORE:
                # the only viable solution is that first spreadsheet has samples
                # as columns
                first_md['is_file_samples_as_rows'] = False
            elif worst_score_if_first_has_samples_as_columns >= \
                    worst_score_if_first_has_samples_as_rows:
                # the first file could work either way, but the score is better
                # or equal if we treat the columns as samples
                first_md['is_file_samples_as_rows'] = False
            else:
                # the first file could work either way, but the score is better
                # if we treat the rows as samples
                first_md['is_file_samples_as_rows'] = True
            # determine transposition of other spreadsheets accordingly
            working_scores = scores_if_first_has_samples_as_rows \
                if first_md['is_file_samples_as_rows'] else \
                scores_if_first_has_samples_as_columns
            for i, working_score in enumerate(working_scores):
                # note i is index into working_scores, but because
                # working_scores omits the first spreadsheet, the corresponding
                # index into all_file_meta_data is i+1
                file_meta_data = all_file_meta_data[i+1]
                file_meta_data['is_file_samples_as_rows'] = \
                    working_score['row_score'] > working_score['column_score']
            # perform transposes and populate additional fields of
            # self.spreadsheets
            for i, file_meta_data in enumerate(all_file_meta_data):
                ss_dict = self.spreadsheets[i]
                if file_meta_data['is_file_samples_as_rows']:
                    pass
                else:
                    ss_dict['df'] = ss_dict['df'].T
                ss_dict['is_file_samples_as_rows'] = \
                    file_meta_data['is_file_samples_as_rows']
                ss_dict['feature_types'], ss_dict['df'] = \
                    SpreadsheetVisualizationJob.\
                        _get_feature_types_and_cleaned_df(ss_dict['df'], True)
                # set sample_names and feature_names from cleaned df, which
                # might have found duplicate sample names and/or duplicate
                # feature names
                ss_dict['sample_names'] = ss_dict['df'].index.tolist()
                ss_dict['feature_names'] = ss_dict['df'].columns.tolist()
        else:
            ss_dict = self.spreadsheets[0]
            # see which orientation gives us better feature types
            feature_types_if_samples_as_rows, df_if_samples_as_rows = \
                SpreadsheetVisualizationJob._get_feature_types_and_cleaned_df(\
                    ss_dict['df'], False)
            feature_types_if_samples_as_columns, df_if_samples_as_columns = \
                SpreadsheetVisualizationJob._get_feature_types_and_cleaned_df(\
                    ss_dict['df'].T, False)
            # simple heuristic for comparison: use whichever gives us higher
            # percentage of features with type "numeric" (TODO: better rule)
            better_with_samples_as_rows = False # default preserves orientation
            if feature_types_if_samples_as_rows and \
                feature_types_if_samples_as_rows:
                numeric_count_if_samples_as_rows = len([1 for ft in \
                    feature_types_if_samples_as_rows if ft == 'numeric'])
                numeric_count_if_samples_as_columns = len([1 for ft in \
                    feature_types_if_samples_as_columns if ft == 'numeric'])
                numeric_pct_if_samples_as_rows = \
                    numeric_count_if_samples_as_rows /\
                        float(len(feature_types_if_samples_as_rows))
                numeric_pct_if_samples_as_columns = \
                    numeric_count_if_samples_as_columns /\
                        float(len(feature_types_if_samples_as_columns))
                if numeric_pct_if_samples_as_rows > \
                    numeric_pct_if_samples_as_columns:
                    better_with_samples_as_rows = True
            if better_with_samples_as_rows:
                ss_dict['is_file_samples_as_rows'] = True
                ss_dict['feature_types'] = feature_types_if_samples_as_rows
                ss_dict['df'] = df_if_samples_as_rows
            else:
                ss_dict['is_file_samples_as_rows'] = False
                ss_dict['feature_types'] = feature_types_if_samples_as_columns
                ss_dict['df'] = df_if_samples_as_columns
            ss_dict['feature_names'] = ss_dict["df"].columns.tolist()
            ss_dict['sample_names'] = ss_dict["df"].index.tolist()

    def count_missing_values(self):
        """Counts missing values per feature and per sample, per spreadsheet,
        updating self.spreadsheets.

        """
        for ss_dict in self.spreadsheets:
            df_nulls = ss_dict["df"].isnull()
            ss_dict['sample_nan_counts'] = df_nulls.sum(axis=1).tolist()
            ss_dict['feature_nan_counts'] = df_nulls.sum(axis=0).tolist()

    def record_spreadsheets(self):
        """
        Ensures that ssviz_spreadsheets contains a record for each spreadsheet
        and that ssviz_feature_data contains a record for each feature in each
        spreadsheet. Associates each spreadsheet with the job in
        ssviz_jobs_spreadsheets. Sets ssviz_spreadsheet_id and is_new_to_db in
        self.spreadsheets.
        """
        ssviz_spreadsheets_for_file_ids = get_ssviz_spreadsheets_by_file_ids(\
            self.user_id,
            [ss_dict['file_id'] for ss_dict in self.spreadsheets])
        for ss_dict in self.spreadsheets:
            matches = [tle for tle in ssviz_spreadsheets_for_file_ids if \
                tle.get_value('file_id') == ss_dict['file_id'] and \
                tle.get_value('is_file_samples_as_rows') == \
                ss_dict['is_file_samples_as_rows']]
            if len(matches) > 0:
                ss_dict['ssviz_spreadsheet_id'] = matches[0].get_nest_id()
                ss_dict['is_new_to_db'] = False
                if len(matches) > 1:
                    # this can happen when multiple ssv jobs run on the same
                    # file at the same time. it's not ideal but it doesn't
                    # break anything, either
                    # TODO prevent this case
                    LOGGER.warning("Found " + str(len(matches)) + \
                        " records for file_id " + str(ss_dict['file_id']) + \
                        " and " + "is_file_samples_as_rows " + \
                        str(ss_dict['is_file_samples_as_rows']))
            else:
                ssviz_spreadsheet_id = create_ssviz_spreadsheet_and_feature_data(\
                    self.user_id, ss_dict['file_id'],
                    ss_dict['is_file_samples_as_rows'], ss_dict['sample_names'],
                    ss_dict['feature_names'], ss_dict['feature_types'],
                    ss_dict['feature_nan_counts'], ss_dict['sample_nan_counts'],
                    ss_dict['df'])
                ss_dict['ssviz_spreadsheet_id'] = ssviz_spreadsheet_id
                ss_dict['is_new_to_db'] = True
        if not self.is_failed():
            create_ssviz_jobs_spreadsheets_entries(self.user_id, self.job_id,\
                [ss_dict['ssviz_spreadsheet_id'] for ss_dict in \
                self.spreadsheets])

    def calculate_and_record_variances(self):
        """
        Ensures that any spreadsheets consisting entirely of numeric data have
        records in ssviz_feature_variances.
        """
        for ss_dict in self.spreadsheets:
            unique_types = list(set(ss_dict['feature_types']))
            if unique_types == ['numeric']:
                # note we'll calculate the variances even if the spreadsheet is
                # not new to the db--we'll write them to the download zip
                ss_dict['variances'] = [np.nanvar(ss_dict['df'][feature_name]) \
                    for feature_name in ss_dict['df']]
                if ss_dict['is_new_to_db']:
                    create_ssviz_feature_variances_entry(self.user_id,\
                        ss_dict['ssviz_spreadsheet_id'], ss_dict['variances'])

    def calculate_and_record_correlations(self):
        """
        Ensures that all possible groupings have correlation records in
        ssviz_feature_correlations.
        """
        candidate_correlations = get_ssviz_spreadsheets_with_correlations(\
            self.user_id, [ss_dict['ssviz_spreadsheet_id'] for ss_dict \
            in self.spreadsheets])
        for grouping_ss_dict in self.spreadsheets:
            grouping_feature_types = grouping_ss_dict['feature_types']
            # skip this grouping spreadsheet if it doesn't contain any
            # categoric features
            if 'categoric' not in grouping_feature_types:
                continue
            for comp_ss_dict in self.spreadsheets:
                # skip calculation if we've previously processed this combo
                if [cc_tle for cc_tle in candidate_correlations if \
                    cc_tle.get_value('ssviz_spreadsheet_id') == \
                    comp_ss_dict['ssviz_spreadsheet_id'] and \
                    cc_tle.get_value('g_spreadsheet_id') == \
                    grouping_ss_dict['ssviz_spreadsheet_id']]:
                    continue
                for g_feature_idx, g_feature_type in \
                    enumerate(grouping_feature_types):
                    if g_feature_type == 'categoric':
                        # grab the grouping feature so we can group the
                        # comparison df accordingly
                        g_feature = \
                            grouping_ss_dict['df'].iloc[:, g_feature_idx]
                        # pd.crosstab below won't work if series share name
                        # https://github.com/pandas-dev/pandas/issues/6319
                        # so rename g_feature
                        # changing g_feature doesn't affect the df from which it
                        # came, btw
                        g_feature.name = "NEST_INTERNAL_RENAME_FOR_CROSSTAB"
                        # g_feature_groups will be a dictionary in which
                        # category values are keys and sample name arrays are
                        # values
                        # note missing values are not considered a group here,
                        # and that's how we want it
                        g_feature_groups = \
                            g_feature.groupby(by=g_feature).groups
                        # break comp_ss dataframe into groups
                        # doing this once at the dataframe level, instead of
                        # inside the loop at the feature level, to reduce time
                        # comp_df_groups will be a dictionary in which category
                        # values are keys and sub-dataframes (one for the set of
                        # sample names associated with each category value) are
                        # the values
                        comp_df = comp_ss_dict['df']
                        comp_df_groups = {}
                        comp_df_sample_names_set = set(comp_df.index.tolist())
                        for cat_value, sample_names \
                                in g_feature_groups.iteritems():
                            common_sample_names = [sn for sn in sample_names \
                                if sn in comp_df_sample_names_set]
                            if common_sample_names:
                                # pull sample_names, not common_sample_names
                                # that'll give us NaN rows for any samples not
                                # found in comp_df
                                # see TODO note in else branch about later
                                # versions of pandas
                                comp_df_groups[cat_value] = \
                                    comp_df.loc[sample_names]
                            else:
                                # pandas will raise an error if we call .loc
                                # without any matches, so we'll manually
                                # create a df with NaN entries, consistent with
                                # .loc's behavior for partial matches
                                # TODO more recent versions of pandas might
                                # raise errors if there are ANY unmatched
                                # indices
                                comp_df_groups[cat_value] = pd.DataFrame([], \
                                    index=sample_names, \
                                    columns=comp_df.columns.tolist())
                        comp_feature_types = comp_ss_dict['feature_types']
                        pvals = []
                        for c_feature_idx, c_feature_type in \
                            enumerate(comp_feature_types):
                            pval = None
                            if c_feature_type == 'numeric':
                                groups_values = [[x for x in \
                                    sub_df.iloc[:, c_feature_idx].values \
                                    if not np.isnan(x)] \
                                    for cat_value, sub_df in \
                                    comp_df_groups.iteritems()]
                                fval, pval = stats.f_oneway(*groups_values)
                                # if pval is nan, treat it as no association
                                # (happens, e.g., if there's no variance in
                                # comparison feature)
                                # for now, don't have to worry about case where
                                # comparison feature IS the grouping feature,
                                # because we're only supporting categoric
                                # grouping features, and this branch only
                                # concerns numeric comparison features
                                # TODO: reconsider this case and similar case
                                # for categoric branch below when supporting
                                # numerically-coded categoric features
                                if np.isnan(pval):
                                    pval = 1.0
                            elif c_feature_type == 'categoric':
                                try:
                                    cont_table = pd.crosstab(g_feature, \
                                        comp_df.iloc[:, c_feature_idx])
                                    chi, pval, dof, expected = \
                                        stats.chi2_contingency(cont_table)
                                except KeyError:
                                    # see https://github.com/pandas-dev/pandas/issues/10291
                                    # TODO remove after updating to pandas 0.18.0
                                    # see KNOW-841
                                    pval = 1.0
                            else:
                                pval = 1.0
                            pvals.append(pval)
                        create_ssviz_feature_correlations_entry(self.user_id, \
                            comp_ss_dict['ssviz_spreadsheet_id'], \
                            grouping_ss_dict['ssviz_spreadsheet_id'], \
                            g_feature_idx, pvals)

    def prepare_zip_file(self):
        """Creates a zip file on disk for later download by the user.

        Args:
            None.

        Returns:
            None.

        """
        # need the following:
        # 1. readme
        # 2. spreadsheets, transposed if necessary
        # 3. variances for spreadsheets
        # 4. correlations for spreadsheets TODO
        zip_path = os.path.join(\
            self.job_dir_path, 'download.zip')
        with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zipout:

            zipout.write(\
                '/pipeline_readmes/README-SSV.md', 'README-SSV.md')

            for ss_dict in self.spreadsheets:
                name, extension = os.path.splitext(ss_dict['filename'])

                # we'll write the spreadsheets to match the on-screen
                # orientation; i.e., samples will correspond to columns

                # if the original file had samples corresponding to rows, the
                # output file will be the transpose of the original file--note
                # that in the filename
                if ss_dict['is_file_samples_as_rows']:
                    # flag transposition in filename
                    name += '_transposed'
                fullname = name + extension

                # the output file is always the transpose of our dataframe,
                # because the on-screen orientation is always the transpose of
                # the pandas orientation
                zipout.writestr(\
                    fullname,
                    ss_dict['df'].T.to_csv(path_or_buf=None, sep="\t"))

                if 'variances' in ss_dict:
                    var_series = pd.Series(\
                        data=ss_dict['variances'],
                        index=ss_dict['feature_names'],
                        name="variance")
                    zipout.writestr(\
                        fullname + '.variances.txt',
                        var_series.to_csv(path=None, sep="\t", header=True))

def get_spreadsheet_visualization_runners(\
    user_id, job_id, project_id, userfiles_dir, project_dir, \
    spreadsheet_nest_ids):
    """Returns a list of ChronosJob instances required to run a GP job.

    Args:
        user_id (NestId): The user id associated with the job.
        job_id (NestId): The job id associated with the job.
        project_id (NestId): The project id associated with the job.
        userfiles_dir (str): The base directory containing all files for
            all users.
        project_dir (str): The name of the directory containing the files
            associated with the current project.
        spreadsheet_nest_ids: The data files in this job.

    Returns:
        list: A list of job instances required to run an SSV job.

    """
    job_name = "nest-ssv-" + job_id.to_slug().lower()
    job_dir_relative_path = os.path.join(project_dir, job_name)
    os.mkdir(os.path.join(userfiles_dir, job_dir_relative_path))

    return [
        SpreadsheetVisualizationJob(user_id, job_id, project_id, userfiles_dir,\
            job_dir_relative_path, job_name, spreadsheet_nest_ids)
    ]

def calculate_survival_pval(user_id, grouping_spreadsheet_id, \
    grouping_feature_idx, duration_spreadsheet_id, duration_feature_idx, \
    event_spreadsheet_id, event_feature_idx, event_val):
    """Returns the log-rank test p-value for a survival analysis.

    Args:
        user_id (NestId): The user id associated with the original SSV job.
        grouping_spreadsheet_id (int): The id of the spreadsheet containing the
            grouping feature.
        grouping_feature_idx (int): The feature index of the grouping feature
            within its spreadsheet.
        duration_spreadsheet_id (int): The id of the spreadsheet containing the
            duration feature.
        duration_feature_idx (int): The feature index of the duration feature
            within its spreadsheet.
        event_spreadsheet_id (int): The id of the spreadsheet containing the
            event feature.
        event_feature_idx (int): The feature index of the event feature within
            its spreadsheet.
        event_val (str): The value within the event feature that encodes an
            observed event. Note this is always passed as a string, even if the
            feature is stored as numeric values.

    Returns:
        float: The p-value.

    """

    # get the sample names for the three features
    ss_tles = get_ssviz_spreadsheets_by_ids(user_id, [\
        grouping_spreadsheet_id, duration_spreadsheet_id, event_spreadsheet_id])
    grouping_sample_names = [tle.get_value('sample_names') for tle in ss_tles \
        if tle.get_nest_id().get_value() == grouping_spreadsheet_id][0]
    duration_sample_names = [tle.get_value('sample_names') for tle in ss_tles \
        if tle.get_nest_id().get_value() == duration_spreadsheet_id][0]
    event_sample_names = [tle.get_value('sample_names') for tle in ss_tles \
        if tle.get_nest_id().get_value() == event_spreadsheet_id][0]

    # get the values for the three features
    # TODO consolidate calls? assuming not worth the trouble now
    grouping_feature = get_ssviz_feature_data(user_id, \
        grouping_spreadsheet_id, [grouping_feature_idx])[0].get_value('values')
    duration_feature = get_ssviz_feature_data(user_id, \
        duration_spreadsheet_id, [duration_feature_idx])[0].get_value('values')
    event_feature = get_ssviz_feature_data(user_id, \
        event_spreadsheet_id, [event_feature_idx])[0].get_value('values')

    # missing values will be None in original data (numeric or categoric)

    # prepare to convert event feature to boolean based on event_value, which is
    # always a string
    val_converter = lambda val: 1 if val == event_val else 0
    # because event_val is always passed as a string and we need to recognize,
    # e.g., 1.0 == 1, also try converting to a float (could eliminate this if
    # we either passed or looked up the event feature type)
    try:
        event_val_as_float = float(event_val)
        val_converter = lambda val: 1 if (\
            val == event_val or val == event_val_as_float) else 0
    except ValueError:
        pass
    # do the conversion
    boolean_event_feature = [val_converter(v) if v is not None else None \
        for v in event_feature]

    # assemble the features with their names into pd.Series
    grouping_series = pd.Series(data=grouping_feature,\
        index=grouping_sample_names, name='grouping')
    duration_series = pd.Series(data=duration_feature,\
        index=duration_sample_names, name='duration')
    event_series = pd.Series(data=boolean_event_feature,\
        index=event_sample_names, name='event')

    # assemble the series into a dataframe
    combined_data = pd.concat([grouping_series, duration_series, event_series],\
        axis=1)

    # retain only the samples that have a duration and a group
    combined_data.dropna(subset=['duration', 'grouping'], inplace=True)

    # fill missing values in event (0, for censored)
    combined_data['event'].fillna(value=0, inplace=True)

    test_stats = multivariate_logrank_test(combined_data['duration'].values, \
        combined_data['grouping'].values, combined_data['event'].values)
    return float(test_stats.p_value)
