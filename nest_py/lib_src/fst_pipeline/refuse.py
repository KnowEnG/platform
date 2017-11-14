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

from joblib import Parallel, delayed
from multiprocessing import cpu_count
import numpy as np
import pandas as pd
from rpy2 import rinterface
from rpy2.robjects import numpy2ri
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects import vectors
from rpy2.robjects import r
from scipy.stats import ks_2samp, mannwhitneyu, ttest_ind

numpy2ri.activate()
pandas2ri.activate()

def refuse(
    df_x, s_y, ntree, mtry, node_size, mode, cores,
    outer_reps=10, inner_reps=10, iss=False):
    """REFUSE -- RElevant FeatUre SElector

    Implements the REFUSE method for ranking features where P>>N. Algorithm and
    R implementation by Nate Russell. Python implementation by Nate and Matt.
    Arguments:
      df_x        an n by p dataframe of features n = # examples p = # features
      s_y        numeric or factor vector of length n
      ntree       number of CART trees to build per Random Forest
      mtry        number of features to randomly grab per decision tree
      node_size   minimum size of terminal nodes
      cores       number of cpu cores to use
      outer_reps  number of Shadow Perturbation sets to build
      inner_reps  number of Random Forests to build per Shadow Perturbation set
      iss         whether to use Instance Cross Validation; ask Nate for
                  guidance if setting True
    """
    vim_melted = None
    if outer_reps > 0:
        vim_melted = pd.DataFrame()
        for i in xrange(outer_reps):
            x_with_shadow = __add_shadows(df_x, i+1)
            # note: multiplying mtry by 2 because we've doubled # of features
            df_vim = __run_rf_outer_rep(x_with_shadow, s_y, ntree=ntree,
                mtry=2*mtry, node_size=node_size, mode=mode, cores=cores,
                inner_reps=inner_reps, outer_rep_number=i, iss=iss)
            vim_melted = vim_melted.append(df_vim, ignore_index=True)
    else:
        vim_melted = __run_rf_outer_rep(df_x, s_y, ntree=ntree, mtry=mtry,
            node_size=node_size, mode=mode, cores=cores, inner_reps=inner_reps,
            outer_rep_number=0, iss=iss)

    # reformt as table of features
    vim_structured = __structure_melted(vim_melted)
    vim_structured.to_csv('REFUSE_structured.csv', index_label='index')

    # compute mean and var of each feature's VIM
    vim_importance = __consolidate_importance(vim_structured, ranked=False)
    vim_stability = __consolidate_stability(vim_structured, ranked=False)

    # test each feature against the max shadow
    vim_p, top_shadow_name = __shadow_test(vim_structured)
    vim_reps = __prep_importance(
        vim_structured, vim_importance, num_features=75, shadow=top_shadow_name)
    vim_reps.to_csv('vim_reps.csv', index_label='index')

    # compute mean VIMs and write data to disk
    refuse_table = pd.DataFrame(vim_importance)
    refuse_table[vim_p.name] = vim_p
    refuse_table[vim_stability.name] = vim_stability
    refuse_table.to_csv('REFUSE_Table.csv', index_label='index')

    return refuse_table

def __run_rf_outer_rep(df_x, s_y, ntree, mtry, node_size, mode, cores,
    inner_reps, outer_rep_number, iss):
    # build forests and store results
    df_vim = None
    if iss:
        # advanced method with instance stability wrapper
        df_vim = __instance_stability(
            df_x, s_y, ntree=ntree, mtry=mtry, node_size=node_size,
            mode=mode, cores=cores, reps=inner_reps)
        # save df_vim for iss plotting later (see vis.py for details)
        df_vim.to_csv('ISS melted rep.' + str(outer_rep_number) + '.csv',
            index_label='index')
    else:
        # basic method without instance stability wrapper
        df_vim = __run_rf_inner_reps(
            df_x, s_y, ntree=ntree, mtry=mtry, node_size=node_size,
            mode=mode, set_label='REFUSE', reps=inner_reps, cores=cores,
            plot=False, iss=True)
    return df_vim

def __run_rf_inner_reps(df_x, s_y, ntree, mtry, node_size, mode, set_label,
    reps, cores, plot, iss):
    """Uses random forest to compute variable importance measures for features
    in df_x relative to s_y.

    Args:
      df_x      dataframe of dim (n,P) with feature columns and sample rows
      s_y      either a binary factor vector or a numeric vector that is to be
                predicted from x. length(y) = n
      ntree     number of trees per random forest model
      mtry      number of features randomly grabbed for a CART tree
      node_size minimum node size of terminal nodes
      set_label string to label output plots and data. it should describe the
                x and y uniquely.
      reps      number of random forest models to grow
                (each with a different seed)
      cores     number of processores to use during the replication process.
                shouldn't exceed reps or the max number of cores available
      plot      whether to generate output for plots -- TODO currently ignored
      iss       whether this is part of an Instance Cross Validation run

    Returns:
      iterable of variable importance measures
    """

    vim_melted = pd.DataFrame()
    #apple = Parallel(n_jobs=min(reps, cores, cpu_count()), temp_folder='/code_live/data/projects/mmbdb/')(
    apple = Parallel(n_jobs=min(reps, cores, cpu_count()))(
        delayed(__run_rf_single)(
            df_x, s_y, ntree, mtry, node_size, mode, i, set_label, plot)
            for i in xrange(reps))
    for vim in apple:
        vim_melted = vim_melted.append(vim, ignore_index=True)

    if iss:
        return vim_melted
    else:
        vim_storage = __structure_melted(vim_melted)
        return __consolidate_importance(vim_storage, ranked=False)

def __run_rf_single(df_x, s_y, ntree, mtry, node_size, mode, seed, set_label, plot):
    """Runs random forest once."""

    my_y = s_y
    if mode == 'classification':
        my_y = vectors.FactorVector(s_y)
    r('set.seed(' + str(seed) + ')')
    random_forest = importr('randomForest')
    data_rf = random_forest.randomForest(
        x=df_x,
        y=my_y,
        ntree=ntree,
        mtry=mtry,
        nodesize=node_size,
        importance=rinterface.TRUE,
        keep_forest=rinterface.TRUE,
        proximity=rinterface.TRUE)

    # TODO do we use these plots?
    # previous implementation would produce only one set of plots for
    # all iterations (the rest were overwritten due to filename
    # collisions), which makes me suspect we don't use them
    # if plot:
    #    plot.standard(data_rf, s_y, set_label)

    # data_rf is a list; we need the member named importance
    # if we convert it directly to a pd.DataFrame, we lose the col and row
    # names for some reason, so convert first to a rpy2 Matrix, then
    # copy the col and row names from there
    m_vim = data_rf.rx2('importance')
    df_vim = pandas2ri.ri2py_dataframe(data_rf.rx2('importance'))
    df_vim.columns = m_vim.colnames
    # restore original names, which may have been mangled by R
    df_vim['row.names'] = df_x.columns.values
    # df_vim has one column "row.names" then...
    if mode == 'classification':
        # one column for each class, then "MeanDecreaseAccuracy"
        # and "MeanDecreaseGini"
        df_vim = df_vim[['row.names', 'MeanDecreaseAccuracy']]
    else:
        # "%IncMSE" and "IncNodePurity"
        df_vim = df_vim[['row.names', 'IncNodePurity']]
    df_vim.columns = ['Feature.Name', 'vim']
    return df_vim

def __add_shadows(df_x, random_seed):
    """
    Adds shadow features to a data frame.
    """

    # make shadow features
    # note: need to be very careful how we do this--np.random.permutation
    # only works if all columns have the same numeric type, so we instead
    # of applying it to the data, we have to apply it to the column indices--
    # otherwise, a single non-numeric column in the df, or a mix of numeric
    # types, will prevent anything from being shuffled
    np.random.seed(random_seed)
    df_combined = df_x.copy()

    for i in xrange(df_x.shape[1]):
        shadow_name = 'shadow_' + str(i)
        col = df_combined.iloc[:,i]
        shadow_col = col.reindex(np.random.permutation(col.index))
        df_combined[shadow_name] = shadow_col.values

    return df_combined

def __structure_melted(df_vim_melted):
    """Converts REFUSE_melted to REFUSE_structured.

    Args:
      - df_vim_melted: DataFrame containing at least feature names
                       in a column called 'Feature.Name' and VIM values
      - vim_name: Column name for VIM values in df_vim_melted

    Returns:
      - DataFrame prepped for box plots and aggregation
    """
    grouped = df_vim_melted.groupby('Feature.Name')
    return pd.concat([
        pd.Series(list(group['vim']), name=name) for name, group in grouped
        ], axis=1)

def __shadow_test(df_vim_structured):
    """Finds top shadow feature and computes p values for all features.

    Arguments:
      - df_vim_importance -- dataframe with feature columns and vim replication
        rows (as returned by __structure_melted)
    Returns:
      - list [0]: vector with a p.value for each feature
                  + the top shadow feature
             [1]: string with name of shadow with highest mean vim score
    """

    s_ttest = None
    top_shadow_name = None

    # find the top shadow
    s_shadow_mean_vims = df_vim_structured.filter(regex='shadow_').mean()
    if s_shadow_mean_vims.size > 0:
        top_shadow_name = s_shadow_mean_vims.idxmax()

        # calculate the t-test values
        ttests = ttest_ind(df_vim_structured[top_shadow_name],
            df_vim_structured, equal_var=False)

        s_ttest = pd.Series(
            [p/2 if t > 0 else 1-p/2 for t, p in zip(ttests[0], ttests[1])],
            index=df_vim_structured.columns.values, name='p_val')

        # disabled for now--when switching to utest, delete ttest code above
        # and ttest include
        #    top_shadow_col = df_vim_structured[top_shadow_name]
        #    s_utest = pd.Series(
        #        [utest(cdata, top_shadow_col)
        #            for cname, cdata in df_vim_structured.iteritems()],
        #        index=df_vim_structured.columns.values, name='p_val')
    else:
        s_ttest = pd.Series([-1 for x in xrange(df_vim_structured.shape[1])],
            index=df_vim_structured.columns.values, name='p_val')
    return [s_ttest, top_shadow_name]

def utest(a, b):
    """
    MannWhitney U statistic

    scipy.stats.mannwhitneyu tests for a != b
    Use only when the number of observation in each sample is > 20 and yo
    have 2 independent samples of ranks.
    Mann-Whitney U is significant if the u-obtained is LESS THAN or equal to
    the critical value of U.

    This test corrects for ties and by default uses a continuity correction.
    The reported p-value is for a one-sided hypothesis; to get the two-sided
    p-value multiply the returned p-value by 2.
    this function modifes that to a > b
    """
    val = mannwhitneyu(a, b)
    if np.median(a) >= np.median(b):
        return 1-val[1]
    else:
        return val[1]


def compare_methods(df_x, s_y, mode):
    """Computes statistics on each feature."""

    # Permutation
    permutation = __run_rf_inner_reps(
        df_x, s_y, ntree=1000, mtry=300, node_size=1, mode=mode,
        set_label="All_Data_Sources",
        reps=30, cores=14, plot=False, iss=False)

    df_stats = pd.DataFrame(
        columns=['name', 'vim', 'pearson', 'kendall', 'spearman',
        'mean', 'var'])

    my_y = s_y
    if mode == 'classification':
        my_y = pd.Series(s_y.factorize()[0])

    # Correlation
    for name, col in df_x.iteritems():
        stats_dict = {'name': name}
        stats_dict['vim'] = permutation[name]
        stats_dict['pearson'] = col.corr(my_y, method='pearson')
        stats_dict['kendall'] = col.corr(my_y, method='kendall')
        stats_dict['spearman'] = col.corr(my_y, method='spearman')
        stats_dict['mean'] = col.mean()
        stats_dict['var'] = col.var()
        df_stats = df_stats.append(stats_dict, ignore_index=True)

    # Reorder
    df_stats.sort(columns='vim', ascending=False, inplace=True)

    df_stats['segment3'] = __auto_segment(df_stats['vim'], 3)
    df_stats['segment5'] = __auto_segment(df_stats['vim'], 5)
    df_stats.to_csv('Data_Results.csv', index_label='index')

def __consolidate_importance(df_vim_structured, ranked=True):
    """Calculates the mean of each feature's VIMs. Returns a Series.
    """
    return_val = df_vim_structured.mean(axis=0)
    return_val.name = 'VIM_mean'
    if ranked:
        return_val.sort()
    return return_val

def __consolidate_stability(df_vim_structured, ranked=True):
    """Calculates the variance of each feature's VIMs.
    """
    return_val = df_vim_structured.var(axis=0)
    return_val.name = 'VIM_var'
    if ranked:
        return_val.sort()
    return return_val

def __prep_importance(
    df_vim_structured, s_vim_importance, style="tail", shadow="null",
    num_features=50):
    """Given a DataFrame containing the structured VIM scores and a Series
    containing mean VIMs, finds the n head or tail features (and the top
    shadow, if it's not among the n), and returns the columns of
    df_vim_structured for those features.
    """
    s_sorted = s_vim_importance.copy()
    s_sorted.sort_values(inplace=True)

    # subset the top or bottom features
    s_truncated = None
    if style is 'tail':
        # gives us the names of the n best features
        s_truncated = s_sorted.tail(num_features)
    else:
        # gives us the names of the n worst features
        s_truncated = s_sorted.head(num_features)

    # ensure that the passed shadow feature is included
    if shadow and shadow not in s_truncated:
        s_truncated[shadow] = s_sorted[shadow]

    return df_vim_structured[s_truncated.index]

def __scale_01(s_vim):
    """Scales vims."""
    s_vim = s_vim - s_vim.median()
    s_vim = s_vim / s_vim.std()
    return s_vim

def parameter_search(
    df_x, s_y, ntree_start, mtry, node_size, mode, cores, stepsize, max_steps,
    plot_title):
    """Tries a range of ntree values and reports results."""

    # storage for stats @ each rep
    df_stats = pd.DataFrame(columns=['ntree', 'mean', 'median', 'mode',
        'var', 'skewness', 'kurtosis', 'ks_p', 'corr'])
    # storage for results @ each rep
    df_growth_storage = pd.DataFrame()
    # results of last rep
    s_previous = None

    for step in xrange(max_steps+1):
        ntree = ntree_start + step * stepsize

        s_this = __run_rf_inner_reps(
            df_x, s_y, ntree=ntree, mtry=mtry, node_size=node_size, mode=mode,
            set_label=plot_title, reps=10,
            cores=cores, plot=True, iss=False)
        s_this = __scale_01(s_this)
        s_this.name = str(ntree)

        df_growth_storage = df_growth_storage.join(s_this, how='outer')

        stats_dict = {'ntree': ntree}
        stats_dict['mean'] = s_this.mean()
        stats_dict['median'] = s_this.median()
        stats_dict['mode'] = s_this.mode()
        if len(stats_dict['mode']) == 0:
            stats_dict['mode'] = stats_dict['mean']
        else:
            stats_dict['mode'] = stats_dict['mode'][0]
        stats_dict['var'] = s_this.var()
        stats_dict['skewness'] = s_this.skew()
        stats_dict['kurtosis'] = s_this.kurtosis()
        stats_dict['ks_p'] = 0
        stats_dict['corr'] = 0
        if s_previous is not None:
            stats_dict['ks_p'] = ks_2samp(s_previous, s_this)[1]
            stats_dict['cor'] = s_previous.corr(s_this)
        df_stats = df_stats.append(stats_dict, ignore_index=True)
        s_previous = s_this

    df_stats.to_csv('Parameter_search_stats.csv', index_label='index')
    df_growth_storage.to_csv('Parameter_search_storage.csv',
        index_label='index')

def __auto_segment(s_vims, num_segments):
    """Given a Series of VIMs and a number of segments, returns a new Series
    assigning each of the VIMs to a segment.
    """
    # use R to find segment breaks
    class_int = importr('classInt')
    segment = class_int.classIntervals(var=s_vims,
        n=num_segments,
        style="fisher")
    breaks = list(segment.rx2('brks'))
    # assign segment # to each VIM
    s_segs = s_vims.apply(
        lambda x: 'Segment ' + str(__find_segment(breaks, x)))
    s_segs.name = 'segment'
    return s_segs

def __find_segment(l_breaks, number):
    """Given a list of segment breaks and a number, returns the segment
    containing the number.
    """
    for i in xrange(1, len(l_breaks)):
        if number < l_breaks[i]:
            return i
    return len(l_breaks)

def __instance_stability(df_x, s_y, ntree, mtry, node_size, mode, cores, reps=10):
    """Given features df_x and response s_y, iteratively calculates VIMs
    dropping one sample at a time.
    """
    vim_melted = pd.DataFrame()

    # iteratively drop instances and recompute PRNG replicated RF run
    for row in df_x.index:
        # subset data
        df_x_i = df_x.drop(row)
        s_y_i = s_y.drop(row)

        # build forests and store results
        df_vim = __run_rf_inner_reps(df_x_i, s_y_i, ntree=ntree, mtry=mtry,
            node_size=node_size, mode=mode,
            set_label="Instance Stability" + str(row),
            reps=reps, cores=cores, plot=False, iss=True)
        vim_melted = vim_melted.append(df_vim, ignore_index=True)

    return vim_melted
