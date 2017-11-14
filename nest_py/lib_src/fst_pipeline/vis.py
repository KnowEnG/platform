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

import fst_utils
import os
import pandas as pd
import rpy2.robjects as ro
from rpy2.robjects import vectors

def process_refuse_output(refuse_dir, feature_metadata, group_metadata,
    df_x, s_y, mode, data_label, ntree, mtry, iss, outer_reps, inner_reps):

    run_info = data_label + "\nNtree: " + str(ntree) + "\nMtry: " + \
        str(mtry) + "\nISS: " + str(iss) + "\nOuter: " + str(outer_reps)

    data_results = None
    parameter_search_stats = None
    parameter_search_storage = None
    refuse_table = None
    vim_reps = None

    for filename in os.listdir(refuse_dir):
        filepath = os.path.join(refuse_dir, filename)
        if filename == 'Data_Results.csv':
            data_results = pd.DataFrame.from_csv(filepath)
        elif filename == 'Parameter_search_stats.csv':
            parameter_search_stats = pd.DataFrame.from_csv(filepath)
        elif filename == 'Parameter_search_storage.csv':
            parameter_search_storage = pd.DataFrame.from_csv(filepath)
        elif filename == 'REFUSE_structured.csv':
            refuse_structured = pd.DataFrame.from_csv(filepath)
        elif filename == 'REFUSE_Table.csv':
            refuse_table = pd.DataFrame.from_csv(filepath)
        elif filename == 'vim_reps.csv':
            vim_reps = pd.DataFrame.from_csv(filepath)
        else:
            print 'WARNING: unexpected file ' + filename

    # make R load the vis script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    ro.r.source(os.path.join(script_dir, 'vis.r'))

    # set the working directory for R
    ro.r.setwd(os.getcwd())

    # draw plots
    if parameter_search_stats is not None:
        ro.r['plot.parameter.search.stats'](parameter_search_stats)
    else:
        print "WARNING: Missing 'Parameter_search_stats.csv'"

    if parameter_search_storage is not None:
        ro.r['plot.parameter.search.growth'](parameter_search_storage)
    else:
        print "WARNING: Missing 'Parameter_search_storage.csv'"

    if data_results is not None:
        data_results = fst_utils.add_feature_metadata(
            data_results, feature_metadata, 'name')
        ro.r['plot.compare.methods'](data_results)

        plot_importance = ro.r['plot.importance']
        plot_importance(
            vim=ro.FloatVector(data_results['vim']),
            labels=ro.StrVector(data_results['name']),
            group=ro.StrVector(data_results['segment3']),
            main='Auto Segment 3')
        plot_importance(
            vim=ro.FloatVector(data_results['vim']),
            labels=ro.StrVector(data_results['name']),
            group=ro.StrVector(data_results['segment5']),
            main='Auto Segment 5')
    else:
        print "WARNING: Missing 'Data_Results.csv'"

    if refuse_table is not None:
        refuse_table = fst_utils.add_feature_metadata(
            refuse_table, feature_metadata)
        if mode == 'classification':
            threshold = 0.6
            keepers = refuse_table[refuse_table['p_val'] > threshold]
            if len(keepers) > 0:
                df_x_best = df_x[keepers.index.values]
                my_y = vectors.FactorVector(s_y)
                # make summary plots
                ro.r['plot.summary.vis'](df_x_best, my_y)
                # plot small multiples
                ro.r['small.multiples'](df_x_best, my_y)
            else:
                print "WARNING: 0 features with p_val > " + str(threshold) + "; skipping summary plots"

        palette = ro.StrVector(group_metadata['color'].tolist())
        palette.names = ro.StrVector(group_metadata.index.tolist())
        # make stability plots
        plot_stability = ro.r['plot.stability']
        plot_stability(
            importance=ro.FloatVector(refuse_table['VIM_mean']),
            stability=ro.FloatVector(refuse_table['VIM_var']),
            labels=ro.StrVector(refuse_table.index.values),
            factor_colour=ro.StrVector(refuse_table['group']),
            palette=palette,
            main="Feature Importance vs Sensitivity",
            info=run_info)
        plot_stability(
            importance=ro.FloatVector(refuse_table['p_val']),
            stability=ro.FloatVector(refuse_table['VIM_var']),
            labels=ro.StrVector(refuse_table.index.values),
            factor_colour=ro.StrVector(refuse_table['group']),
            palette=palette,
            main="Feature p-value vs Sensitivity",
            xlabel="Likelihood that a Feature is Relevant",
            info=run_info)

        # the following portion requires refuse_table and vim_reps
        if vim_reps is not None:
            # make box plots
            plot_importance_box = ro.r['plot.importance.box']
            # in addition to vim_reps DF, need to pass version of refuse_table
            vim_reps_supplement = refuse_table.loc[vim_reps.columns.values,
                ['group', 'p_val']]
            vim_reps_supplement.sort(columns='p_val',
                ascending=False, inplace=True)
            samples = outer_reps * inner_reps
            if iss:
                samples *= len(df_x.index)
            plot_importance_box(
                df_vim_reps=vim_reps,
                df_supplement=vim_reps_supplement,
                palette=palette,
                title=data_label + ' Feature Importance Box Plot',
                type="box", info=run_info + "\n# of samples: " + str(samples))
        else:
            print "WARNING: Missing 'vim_reps.csv'"
    else:
        print "WARNING: Missing 'REFUSE_Table.csv'"

###    TODO for each instance_stability_vim_melted, do the following:
###    
###            # Consolidate and Plot: Sensitivity
###            cat("\nComputing Importance, Sensitivity and Relative Sensitivity\n")
###            vim.importance <- consolidate.importance(vim_melted$Feature.Name,
###                                                     vim_melted$VIM,
###                                                     vim_melted$Feature.Source,
###                                                     ranked=F)
###            vim.stability <- consolidate.stability(vim_melted$Feature.Name,
###                                                   vim_melted$VIM,
###                                                   vim_melted$Feature.Source,
###                                                   ranked=F)
###    
###            # Consolidate and Plot: Box
###            YO, PREP.IMPORTANCE NOW REQUIRES VIM_IMPORTANCE PASSED, NOT VIM_MELTED
###            vim.reps <- prep.importance(vim_melted$Feature.Name,
###                                        vim_melted$VIM,
###                                        vim_melted$Feature.Source,
###                                        n=75)
###            plot.importance.box(df=vim.reps,title=paste("Instance Stability Box plot Demo"),type="box",p.val=rep("57%",75))
###    
###    
###            # Build a Grouping vector based upon naming conventions
###            group <- build.grouping(names(vim.importance))
###            grouping <- data.frame("Group"=group)
###    
###            cat("Plotting Importance vs Sensitivty")
###            plot.stability(importance=vim.importance,
###                           stability=vim.stability,
###                           labels=names(vim.importance),
###                           factor.colour=grouping$Group,
###                           main=paste("Feature importance vs Sensitivity 11"))
