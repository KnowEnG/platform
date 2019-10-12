import os

import pandas as pd
import pytest

from nest_py.knoweng.jobs.pipelines.spreadsheet_visualization import \
    SpreadsheetVisualizationJob

def test_load_spreadsheet():
    """
    Tests the data-cleaning features of
    SpreadsheetVisualizationJob._load_spreadsheet().
    """
    test_data_dir_path = os.path.dirname(os.path.realpath(__file__))

    # first block: file header has no initial tab

    # case 0: "NA" is label of first sample
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_00.tsv"))
    assert input_df.columns.tolist() == ['NA', 'sample2', 'sample3']
    assert input_df.index.tolist() == ['featureA', 'featureB', 'featureC']

    # case 1: "NA" is label of second sample
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_01.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'NA', 'sample3']
    assert input_df.index.tolist() == ['featureA', 'featureB', 'featureC']

    # case 2: "NA" is label of third sample
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_02.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'sample2', 'NA']
    assert input_df.index.tolist() == ['featureA', 'featureB', 'featureC']

    # case 3: "NA" is label of first feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_03.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'sample2', 'sample3']
    assert input_df.index.tolist() == ['NA', 'featureB', 'featureC']

    # case 4: "NA" is label of second feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_04.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'sample2', 'sample3']
    assert input_df.index.tolist() == ['featureA', 'NA', 'featureC']

    # case 5: "NA" is label of third feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_05.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'sample2', 'sample3']
    assert input_df.index.tolist() == ['featureA', 'featureB', 'NA']

    # case 6: "NA" is label of first sample and first feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_06.tsv"))
    assert input_df.columns.tolist() == ['NA', 'sample2', 'sample3']
    assert input_df.index.tolist() == ['NA', 'featureB', 'featureC']

    # case 7: "NA" is label of second sample and second feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_07.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'NA', 'sample3']
    assert input_df.index.tolist() == ['featureA', 'NA', 'featureC']

    # case 8: "NA" is label of third sample and third feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_08.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'sample2', 'NA']
    assert input_df.index.tolist() == ['featureA', 'featureB', 'NA']

    # second block: file header has initial tab

    # case 9: "NA" is label of first sample
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_09.tsv"))
    assert input_df.columns.tolist() == ['NA', 'sample2', 'sample3']
    assert input_df.index.tolist() == ['featureA', 'featureB', 'featureC']

    # case 10: "NA" is label of second sample
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_10.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'NA', 'sample3']
    assert input_df.index.tolist() == ['featureA', 'featureB', 'featureC']

    # case 11: "NA" is label of third sample
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_11.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'sample2', 'NA']
    assert input_df.index.tolist() == ['featureA', 'featureB', 'featureC']

    # case 12: "NA" is label of first feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_12.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'sample2', 'sample3']
    assert input_df.index.tolist() == ['NA', 'featureB', 'featureC']

    # case 13: "NA" is label of second feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_13.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'sample2', 'sample3']
    assert input_df.index.tolist() == ['featureA', 'NA', 'featureC']

    # case 14: "NA" is label of third feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_14.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'sample2', 'sample3']
    assert input_df.index.tolist() == ['featureA', 'featureB', 'NA']

    # case 15: "NA" is label of first sample and first feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_15.tsv"))
    assert input_df.columns.tolist() == ['NA', 'sample2', 'sample3']
    assert input_df.index.tolist() == ['NA', 'featureB', 'featureC']

    # case 16: "NA" is label of second sample and second feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_16.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'NA', 'sample3']
    assert input_df.index.tolist() == ['featureA', 'NA', 'featureC']

    # case 17: "NA" is label of third sample and third feature
    input_df = SpreadsheetVisualizationJob._load_spreadsheet(\
        os.path.join(test_data_dir_path, "ssv_na_label_17.tsv"))
    assert input_df.columns.tolist() == ['sample1', 'sample2', 'NA']
    assert input_df.index.tolist() == ['featureA', 'featureB', 'NA']