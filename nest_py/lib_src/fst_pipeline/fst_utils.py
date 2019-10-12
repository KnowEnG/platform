"""
                   University of Illinois/NCSA
                       Open Source License

        Copyright(C) 2014-2015, The Board of Trustees of the
            University of Illinois.  All rights reserved.

                          Developed by:

                         Visual Analytics
                   Applied Research Institute
            University of Illinois at Urbana-Champaign

               http://appliedresearch.illinois.edu/

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal with the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

+ Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimers.
+ Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimers in
  the documentation and/or other materials provided with the distribution.
+ Neither the names of The PerfSuite Project, NCSA/University of Illinois
  at Urbana-Champaign, nor the names of its contributors may be used to
  endorse or promote products derived from this Software without specific
  prior written permission.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS WITH THE SOFTWARE.
"""

import pandas as pd
import rpy2.robjects.packages as rpackages
from rpy2.robjects.vectors import StrVector
import xlsxwriter

def add_feature_metadata(df_target, df_feature_metadata, df_target_fn_col=None):
    """Adds feature metadata columns to df_target.

    Args:
        df_target - a DataFrame; must contain feature names somewhere
        df_feature_metadata - a DataFrame containing feature metadata,
            as loaded by fst.py's self.feature_metadata
        df_target_fn_col - the name of the column in df_target that contains
            the feature names, or None if it's the index of df_target that
            contains the feature names

    Returns:
        a copy of df_target with the feature metadata added
    """
    original_index = df_target.index
    if df_target_fn_col is not None:
        df_target.index = df_target[df_target_fn_col]
    df_joined = df_target.join(df_feature_metadata)
    # add groups for shadow features
    s_group = df_joined['group']
    feature_names = s_group.index.values
    s_non_shadows = pd.Series(
        [not fname.startswith('shadow_') for fname in feature_names],
        index=feature_names)
    s_group = s_group.where(s_non_shadows, 'Shadow')
    df_joined['group'] = s_group
    # handle any remaining NaN groups
    df_joined['group'].fillna('NA')
    # restore index
    df_target.index = original_index

    return df_joined

def create_refuse_xlsx(df_refuse_table, df_feature_metadata, outpath):
    """Creates an Excel spreadsheet containing the REFUSE Table data,
    annotated with the feature metadata, saved to the given outpath."""

    # merge data
    df_complete = add_feature_metadata(df_refuse_table, df_feature_metadata)
    df_complete['Feature Name'] = df_complete.index.values # easier to iterate

    # sort by VIM_mean
    df_complete.sort(columns='VIM_mean', ascending=False, inplace=True)

    # create spreadsheet
    workbook = xlsxwriter.Workbook(outpath)
    worksheet = workbook.add_worksheet()

    # start from first cell (zero-indexed)
    row = 0
    col = 0

    # styles
    title_style = workbook.add_format({
        'font_size': 12,
        'font_color': 'white',
        'bg_color': '#808080'
        })
    relevant_style = workbook.add_format({
        'font_size': 12,
        'bg_color': '#EBF1DE'
        })
    default_style = workbook.add_format({
        'font_size': 12})

    # these columns should always come first
    column_order = ['Feature Name', 'VIM_mean', 'p_val', 'VIM_var', 'group']
    # there may be user-defined columns to follow
    additional_columns = [x for x in df_complete.columns.values
        if x not in column_order]
    # final order
    column_order += additional_columns

    # some columns get user-friendly names
    column_titles = {
        'VIM_mean': 'Rank (higher=better)',
        'p_val': 'Likelihood of Relevance',
        'VIM_var': 'Variance of Rank',
        'group': 'Group Name'}

    for column in column_order:
        row = 0
        title = column
        if column in column_titles:
            title = column_titles[column]
        worksheet.write(row, col, title, title_style)
        for cell in df_complete[column]:
            row += 1
            style = default_style
            if column == 'p_val' and cell > 0.5:
                style = relevant_style
            worksheet.write(row, col, cell, style)
        col += 1

    # set column widths
    worksheet.set_column(0, len(column_order)-1, 30)

    workbook.close()

def check_r_packages():
    """Ensures required R packages are installed."""
    # import R's utility package
    utils = rpackages.importr('utils')
    # R package names
    packnames = ('classInt',
        'minerva', # should already be installed in dockerfile
        'randomForest', #should already be installed in dockerfile
        #'ggplot2', #used by FST commands that generate PDFs, which aren't currently
        #           #used, and this package doesn't install properly due to versioning problems
        'MASS',
        'gplots')

    # R vector of strings
    for x in packnames:
        print('$$$ ensuring installation of R package: ' + str(x))
        if rpackages.isinstalled(x):
            print('$$$  already installed')
        else:
            print('$$$  INSTALLING: ' + x)
            utils.install_packages(StrVector([x]), verbose=True, quiet=False, dependencies=True, repos="https://cran.rstudio.com", method="curl")
            print('$$$  reported as now installed? ' + str(rpackages.isinstalled(x)) + ' for ' + x)


    #R likes to fail silently, so double check.
    failed_installs = list()
    for x in packnames:
        if not rpackages.isinstalled(x):
            failed_installs.append(x)
    if not len(failed_installs) == 0:
        raise Exception('rpackages claims to have installed these packages, but did not: ' + str(failed_installs))
