#!/usr/bin/python
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

import argparse
import collections
import fst_utils
from multiprocessing import cpu_count
import os
import pandas as pd
import re
import refuse
from rpy2.robjects import numpy2ri
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
import shutil
import sys
import textwrap
from yaml import load
import vis

numpy2ri.activate()

def _filter_by_variance(frame, threshold=0.005):
    """Removes from frame any columns with a relative variance
    beneath the given threshold.
    """
    # first, for each column X, compute relative variance as
    # var((X-min(X))/(max(X)-min(X)))
    numerators = frame.subtract(frame.min(axis='index'), axis='columns')
    denominators = frame.max(axis='index') - frame.min(axis='index')
    quotients = numerators.div(denominators, axis='columns')
    variances = quotients.var(axis='index', ddof=0)
    # now apply the filter
    return frame.loc[:, variances.map(lambda x: x > threshold)]

class FST(object):
    """Feature Selection Tool

    Provides a unified interface to the many components of the
    Feature Selection Tool.
    """
    def __init__(self, config, noprompt):
        self._config = config
        self._noprompt = noprompt
        self._df_x = None
        self._s_y = None
        self._feature_metadata = None
        self._group_metadata = None

    @property
    def df_x(self):
        """Returns a dataframe containing the predictors."""
        if self._df_x is None:
            errors = self.__read_data()
            if errors:
                FST.__print_errors(errors)
                sys.exit("Aborting")
        return self._df_x

    @property
    def s_y(self):
        """Returns a series containing the response."""
        if self._s_y is None:
            errors = self.__read_data()
            if errors:
                FST.__print_errors(errors)
                sys.exit("Aborting")
        return self._s_y

    @property
    def feature_metadata(self):
        """Returns a dataframe containing the feature metadata.

        Looks for a property named feature_metadata_path in the yaml file.
        If the property is found, loads the file at that path. Otherwise,
        prints a warning message and uses defaults.
        """
        if self._feature_metadata is None:
            if 'feature_metadata_path' in self._config:
                self._feature_metadata = pd.DataFrame.from_csv(
                    self._config['feature_metadata_path'])
                # make sure feature names are unique
                names_counter = collections.Counter(
                    self._feature_metadata.index.values)
                duplicates = \
                    [item for item, count in names_counter.items() if count > 1]
                if duplicates:
                    raise ValueError(
                        'feature metadata file contains duplicate name' + \
                        ((" '" + duplicates[0] + "'") if len(duplicates) == 1 \
                        else ('s: ' + str(duplicates))))
                # make sure feature names cover df_x
                uncovered = [name for name in self.df_x.columns.values \
                    if names_counter[name] == 0]
                if uncovered:
                    raise ValueError(
                        'feature metadata file contains no entry for name' + \
                        ((" '" + uncovered[0] + "'") if len(uncovered) == 1 \
                        else ('s: ' + str(uncovered))))
                if 'group' not in self._feature_metadata.columns:
                    raise ValueError(
                        'feature metadata file contains no column "group"')
                self._feature_metadata['group'].fillna('Unknown', inplace=True)
            else:
                print 'Warning: No feature_metadata_path found in yaml ' + \
                    'file. Will use defaults.'
                feature_names = self.df_x.columns.values
                self._feature_metadata = pd.DataFrame(index=feature_names,
                    data={'group': ['NA' for x in feature_names]})
        return self._feature_metadata

    @property
    def group_metadata(self):
        """Returns a dataframe containing the group metadata.

        Looks for a property named group_metadata_path in the yaml file.
        If the property is found, loads the file at that path. Otherwise,
        prints a warning message and uses defaults.
        """
        # defaults
        default_palette = ["#d66166", "#fdb800", "#ff8f57", "#6699ff",
            "#81b578", "#c4acfc", "#96e0d7", "#d55e00", "#cc79a7", "#000000",
            "#e6a0a3", "#fed466", "#ffbc9a", "#a3c2ff", "#b3d3ae", "#dccdfd",
            "#c0ece7", "#e69e66", "#e0afca", "#d5d5d5"]
        # from http://tools.medialab.sciences-po.fr/iwanthue/
        extended_palette = ["#5EA0DE", "#E83923", "#61D13C", "#E040D6",
            "#3D4110", "#E3B22E", "#6F2249", "#94C39D", "#D79280", "#7247A5",
            "#E2346B", "#2A3D63", "#E29AC7", "#9CC464", "#3D6866", "#9F3C1F",
            "#E046A3", "#AFADC4", "#D1A967", "#A860E9", "#577E26", "#8A524B",
            "#52CC6D", "#D4842F", "#8E699F", "#8B975E", "#96622F", "#55C6BF",
            "#40829F", "#566CDA", "#A7C230", "#52CE98", "#CF6B7F", "#962838",
            "#542B63", "#983488", "#70BDD9", "#5AA362", "#AB9D34", "#623014",
            "#6D6B83", "#DD4245", "#47A02C", "#3D4E91", "#AE82EA", "#73A19E",
            "#DE7360", "#356633", "#489377", "#B5A7E0", "#C14179", "#D783D3",
            "#303F2C", "#532729", "#7090E8", "#C65DCE", "#DC5F25", "#7A6D2E",
            "#3A3443", "#825969", "#687DB0", "#CC95A6", "#856FBE", "#A65B8B"]
        shadow_color = "#4a4a4a"
        # initialize if necessary
        if self._group_metadata is None:
            if 'group_metadata_path' in self._config:
                self._group_metadata = pd.DataFrame.from_csv(
                    self._config['group_metadata_path'])
                # make sure group names are unique
                names_counter = collections.Counter(
                    self._group_metadata.index.values)
                duplicates = \
                    [item for item, count in names_counter.items() if count > 1]
                if duplicates:
                    raise ValueError(
                        'group metadata file contains duplicate name' + \
                        ((" '" + duplicates[0] + "'") if len(duplicates) == 1 \
                        else ('s: ' + str(duplicates))))
                # make sure feature names cover feature_metadata
                uncovered = [name for name in \
                    self.feature_metadata['group'].order().unique() \
                    if names_counter[name] == 0]
                if uncovered:
                    raise ValueError(
                        'group metadata file contains no entry for name' + \
                        ((" '" + uncovered[0] + "'") if len(uncovered) == 1 \
                        else ('s: ' + str(uncovered))))
                if 'Shadow' not in self._group_metadata.index:
                    raise ValueError(
                        'group metadata file does not contain Shadow')
                if 'color' not in self._group_metadata.columns:
                    group_names = self._group_metadata.index
                    palette = default_palette
                    if len(group_names) > len(default_palette): 
                        if len(group_names) <= len(extended_palette):
                            palette = extended_palette
                        else:
                            raise ValueError('too many groups to color-code')
                    self._group_metadata['color'] = palette[:len(group_names)]
                    self._group_metadata['color']['Shadow'] = shadow_color
            else:
                print 'Warning: No group_metadata_path found in yaml ' + \
                    'file. Will use defaults.'
                group_names = self.feature_metadata['group'].order().unique()
                self._group_metadata = pd.DataFrame(
                    index=group_names.tolist()+['Shadow'])
                palette = default_palette
                if len(group_names) > len(default_palette):
                    if len(group_names) <= len(extended_palette):
                        palette = extended_palette
                    else:
                        raise ValueError('too many groups to color-code')
                self._group_metadata['color'] = palette[:len(group_names)] + \
                    [shadow_color]
        return self._group_metadata

    def main(self):
        """Parses command-line arguments and dispatches to instance methods."""
        commands = self.__commands_dict()

        subcommand_list = ['\t' + x + '\t' + self.__subcommand_short_message(x)
                           for x in sorted(commands.iterkeys())]
        parser = argparse.ArgumentParser(
            description='Feature Selection Tool',
            usage='fst <subcommand> [<args>]\n\n' +
            'The subcommands are as follows:\n' + '\n'.join(subcommand_list)
        )
        parser.add_argument('subcommand', help='Subcommand to run')
        # parse_args defaults to [1:] for args, but we need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not args.subcommand in commands:
            print 'Unrecognized subcommand'
            parser.print_help()
            exit(1)
        subargs = self.__subcommand_args(args.subcommand)
        if hasattr(subargs, 'config') and subargs.config.mode is 'r':
            self._config = load(subargs.config)
            subargs.config.close()
        if hasattr(subargs, 'noprompt'):
            self._noprompt = subargs.noprompt
        # use dispatch pattern to invoke method with same name
        getattr(self, args.subcommand)()

    def all(self):
        """Runs clean, valid, refuse, mic, vis, dist, web, and box.

        Is equivalent to
        fst clean valid refuse mic vis dist web box [<args>]
        (Does not include setup, status, test, or yaml.)
        """
        self.clean()
        if not self.valid():
            sys.exit("Aborting")
        self.refuse()
        self.mic()
        self.vis()
        self.dist()
        self.web()
        self.box()

    def box(self):
        """Copies outputs to Box.

        Copies to Box all outputs associated with the provided config file, or
        if no config file is provided, all outputs associated with fst.yaml in
        the current working directory. Will prompt if Box directory already
        exists (overwrite/rename/cancel) unless called with the -noprompt
        flag, in which case it will overwrite the output directory. Will warn
        if outputs from refuse, mic, vis, dist, or web are missing.
        """
        print 'TODO check status'
        print 'TODO warn if outputs missing'
        print 'TODO prompt if overwriting'
        print 'TODO copy'

    def clean(self):
        """Clears output directories.

        Clears any output directories associated with the provided config
        file, or if no config file is provided, any output directories
        associated with fst.yaml in the current working directory. Prompts for
        confirmation on each directory to be deleted unless called with the
        -noprompt flag.
        """
        dirs = ['dist', 'output_mic', 'output_refuse', 'output_vis',
            'output_web']
        if os.path.isdir(self._config['results_directory']):
            for fname in os.listdir(self._config['results_directory']):
                ospath = os.path.join(self._config['results_directory'], fname)
                # check for auto-renamed output dirs, too (thus the re.sub)
                if os.path.isdir(ospath) and \
                    re.sub(r'_\d+$', '', fname) in dirs:
                    if self._noprompt:
                        shutil.rmtree(ospath)
                    else:
                        decision = None
                        while decision not in ['y', 'n', 'c']:
                            decision = raw_input('Delete ' + ospath + \
                                ' or cancel? (y/n/c)')
                        if decision == 'y':
                            shutil.rmtree(ospath)
                        elif decision == 'n':
                            continue
                        elif decision == 'c':
                            sys.exit(130)
                        else:
                            raise ValueError('decision ' + decision + \
                                ' slipped through loop')
        print 'TODO make sure we clear status, too'

    def dist(self):
        """Generates deliverables.

        Generates deliverables directory using the provided config file, or if
        no config file is provided, using fst.yaml in the current working
        directory. Will prompt if dist directory already exists
        (overwrite/rename/cancel) unless called with the -noprompt flag, in
        which case it will overwrite the dist directory. Depends upon outputs
        from refuse and vis.
        """
        print 'TODO check status'
        print 'TODO error if outputs missing'
        # create output dir
        parentdir = self._config['results_directory']
        outdir = os.path.join(parentdir, 'dist')
        self.__careful_mkdir(outdir)
        # copy visualization
        visdir = os.path.join(parentdir, 'output_vis')
        if not os.path.isdir(visdir):
            print 'Warning: ' + visdir + ' does not exist. Run the vis command.'
        else:
            for filename in os.listdir(visdir):
                if 'Small_Multiples' in filename or \
                    'Feature_Importance_Box_Plot' in filename:
                    filepath = os.path.join(visdir, filename)
                    shutil.copy(filepath, outdir)
        # copy mic results
        micpath = os.path.join(parentdir, 'output_mic', 'MIC.csv')
        if not os.path.exists(micpath):
            print 'Warning: ' + micpath + ' does not exist. ' + \
                'Run the mic command.'
        else:
            shutil.copy(micpath, outdir)
        # copy refuse results
        refusedir = os.path.join(parentdir, 'output_refuse')
        rtpath = os.path.join(refusedir, 'REFUSE_Table.csv')
        xlsxpath = os.path.join(outdir, 'Feature_Table.xlsx')
        fst_utils.create_refuse_xlsx(
            pd.DataFrame.from_csv(rtpath),
            self.feature_metadata,
            xlsxpath)

    def mic(self):
        """Runs MIC analysis.

        Runs MIC analysis using the provided config file, or if no config file
        is provided, using fst.yaml in the current working directory. Will
        prompt if output directory already exists (use/rename/cancel) unless
        called with the -noprompt flag, in which case it will reuse the output
        directory. Will prompt if output file already exists
        (overwrite/rename/cancel) unless called with the -noprompt flag, in
        which case it will overwrite the output file.
        """
        # create output dir
        outdir = os.path.join(self._config['results_directory'], 'output_mic')
        self.__careful_mkdir(outdir)
        # prepare data
        filtered = _filter_by_variance(self.df_x)
        # call R
        # TODO just a sec and we'll probably switch this to minepy
        minerva = importr('minerva')
        # pylint: disable=no-member
        mine_out = minerva.mine(filtered.values)
        # pylint: enable=no-member
        mic_out = pandas2ri.ri2py_dataframe(mine_out.rx2(1))
        # restore names
        names_list = list(filtered.columns.values)
        mic_out.rename(columns=lambda x: names_list[int(x)],
                       index=lambda x: names_list[int(x)],
                       inplace=True)
        # save and return
        mic_out.to_csv(os.path.join(outdir, 'MIC.csv'), index_label='feature')

    def refuse(self):
        """Runs REFUSE analysis.

        Runs REFUSE analysis using the provided config file, or if no config
        file is provided, using fst.yaml in the current working directory. Will
        prompt if output directory already exists (use/rename/cancel) unless
        called with the -noprompt flag, in which case it will reuse the output
        directory. Will prompt if output files already exist
        (overwrite/rename/cancel) unless called with the -noprompt flag, in
        which case it will overwrite the output files.
        """
        # create output dir
        outdir = os.path.join(self._config['results_directory'],
                              'output_refuse')
        self.__careful_mkdir(outdir)
        original_dir = os.getcwd()
        os.chdir(outdir)
        if self._config['refuse_search_parameters']:
            # run parameter search
            refuse.parameter_search(
                self.df_x, self.s_y, ntree_start=1000, mtry=200,
                node_size=int(self._config['refuse_node_size']),
                cores=cpu_count(), mode=self._config['mode'], stepsize=2500,
                max_steps=4, plot_title="All Features Mtry = 200")
        # determine feature relevance
        refuse.refuse(
            self.df_x, self.s_y, ntree=int(self._config['ntree']),
            mtry=int(self._config['mtry']),
            node_size=int(self._config['refuse_node_size']), cores=cpu_count(),
            outer_reps=int(self._config['refuse_subsets']),
            inner_reps=int(self._config['refuse_forests']),
            mode=self._config['mode'], iss=False)
        if self._config['refuse_compare_methods']:
            # compare methods
            refuse.compare_methods(self.df_x, self.s_y, mode=self._config['mode'])
        os.chdir(original_dir)

    def setup(self):
        """Installs required R packages.

        Assumes R itself is already installed. Will prompt whether to install
        packages in your home directory; answer yes and agree to any directories
        it wants to create.
        """
        fst_utils.check_r_packages()

    def status(self):
        """Prints list of subcommands already run.

        Examines the output directory associated with the provided config file,
        or if no config file is provided, associated with fst.yaml in the
        current working directory. Prints to console a list of fst subcommands
        and whether each has been run
        (e.g., "...mic: no...refuse: yes...vis: yes...").
        """
        print 'TODO check status'
        print 'TODO print'

    def test(self):
        """Runs tests.

        Runs tests.
        """
        print 'TODO write tests, etc.'

    def valid(self):
        """Validates input files.

        Validates the input files associated with the provided config file, or
        if no config file is provided, validates the input files associated
        with fst.yaml in the current working directory.
        """
        msgs = self.__read_data()
        if len(msgs) == 0:
            try:
                self.feature_metadata
                self.group_metadata
            except ValueError as ve:
                msgs.append(('ERROR', str(ve)))
        FST.__print_errors(msgs)
        return len(msgs) == 0

    def vis(self):
        """Generates visualizations.

        Generates visualizations using the provided config file, or if no
        config file is provided, using fst.yaml in the current working
        directory. Will prompt if output files already exist
        (overwrite/rename/cancel) unless called with the -noprompt flag, in
        which case it will overwrite the output files. Depends upon outputs
        from refuse.
        """
        print 'TODO check status'
        print 'TODO error if outputs missing'
        # create output dir
        outdir = os.path.join(self._config['results_directory'], 'output_vis')
        self.__careful_mkdir(outdir)
        original_dir = os.getcwd()
        os.chdir(outdir)
        vis.process_refuse_output(
            os.path.join(self._config['results_directory'], 'output_refuse'),
            self.feature_metadata, self.group_metadata, self.df_x, self.s_y,
            self._config['mode'], self._config['data_label'],
            self._config['ntree'], self._config['mtry'], False,
            self._config['refuse_subsets'], self._config['refuse_forests'])
        os.chdir(original_dir)

    def web(self):
        """Generates web assets.

        Generates web assets using the provided config file, or if no config
        file is provided, using fst.yaml in the current working directory. Will
        prompt if output files already exist (overwrite/rename/cancel) unless
        called with the -noprompt flag, in which case it will overwrite the
        output files. Depends upon outputs from refuse, mic, vis, and dist.
        """
        print 'TODO check status'
        print 'TODO error if outputs missing'
        # create output dir
        outdir = os.path.join(self._config['results_directory'], 'output_web')
        self.__careful_mkdir(outdir)
        print 'TODO copy/generate'

    def yaml(self):
        """Prints skeleton config file to STDOUT.

        Prints skeleton config file to STDOUT.
        """
        print 'results_directory: /path/to/results/dir'
        print 'data_path: /path/to/input.csv'
        print 'feature_metadata_path: /path/to/feature_metadata.csv'
        print 'group_metadata_path: /path/to/group_metadata.csv'
        print 'data_label: Title for Analysis'
        print 'to_drop:'
        print '   - FeatureX'
        print '   - FeatureY'
        print 'response: ResponseFeatureLabel'
        print 'mode: classification'
        print 'vim_score: MeanDecreaseAccuracy'
        print 'ntree: 20000'
        print 'mtry: 300'
        print 'refuse_subsets: 10'
        print 'refuse_forests: 10'
        print 'refuse_compare_methods: false'
        print 'refuse_search_parameters: false'
        print 'refuse_node_size: 1'

    def version(self):
        """Prints version information.

        Prints version information and exits.
        """
        print 'TODO print'

    def __subcommand_short_message(self, subcommand):
        """Returns the first line of the given method's doc string."""
        doc = getattr(self, subcommand).__doc__
        return doc.split('\n\n', 1)[0]

    def __subcommand_long_message(self, subcommand):
        """Returns all but the first line of the given method's doc string."""
        doc = getattr(self, subcommand).__doc__
        doc = getattr(self, subcommand).__doc__
        return textwrap.dedent(doc.split('\n\n', 1)[1])

    def __subcommand_args(self, subcommand):
        """Parses and returns the subcommand-level arguments."""
        command_info = self.__commands_dict()[subcommand]
        parser = argparse.ArgumentParser(
            description=self.__subcommand_long_message(subcommand),
            usage='fst ' + subcommand + ' [<args>]',
            formatter_class=argparse.RawDescriptionHelpFormatter)
        if command_info['config']:
            parser.add_argument(
                '-c',
                '--config',
                default='fst.yaml',
                metavar='/path/to/fst.yaml',
                type=command_info['config'],
                help='Optional path to config file (defaults to ./fst.yaml)')
        if command_info['noprompt']:
            parser.add_argument(
                '-n',
                '--noprompt',
                action='store_true',
                help='Suppresses prompts when overwriting files')
        # now that we're inside a subcommand, ignore the first TWO argvs
        return parser.parse_args(sys.argv[2:])

    def __commands_dict(self):
        """Returns a dictionary containing information about the subcommands."""
        return {
            'all': {'config': argparse.FileType('r'), 'noprompt': True},
            'box': {'config': argparse.FileType('r'), 'noprompt': True},
            'clean': {'config': argparse.FileType('r'), 'noprompt': True},
            'dist': {'config': argparse.FileType('r'), 'noprompt': True},
            'mic': {'config': argparse.FileType('r'), 'noprompt': True},
            'refuse': {'config': argparse.FileType('r'), 'noprompt': True},
            'setup': {'config': None, 'noprompt': False},
            'status': {'config': argparse.FileType('r'), 'noprompt': True},
            'test': {'config': None, 'noprompt': False},
            'valid': {'config': argparse.FileType('r'), 'noprompt': True},
            'vis': {'config': argparse.FileType('r'), 'noprompt': True},
            'web': {'config': argparse.FileType('r'), 'noprompt': True},
            'yaml': {'config': None, 'noprompt': False},
            'version': {'config': None, 'noprompt': False},
        }

    def __read_data(self):
        """Loads the data file into dataframes."""
        return_val = []
        # read data
        try:
            self._df_x = pd.read_csv(self._config['data_path'],
                mangle_dupe_cols=False)
        except IOError as err:
            print str(err)
            sys.exit(1)
        # make sure to_drop and response refer to existing columns
        # pylint: disable=maybe-no-member
        col_names_counter = collections.Counter(self._df_x.columns.values)
        # pylint: enable=maybe-no-member
        to_drop = self._config['to_drop']
        response = self._config['response']
        for drop_col in to_drop:
            if col_names_counter[drop_col] == 0:
                return_val.append(('ERROR',
                    'dropped column ' + drop_col + \
                    ' does not match a column name'))
        if col_names_counter[response] == 0:
            return_val.append(('ERROR',
                    'response ' + response + \
                    ' does not match a column name'))
        # make sure column names are unique
        duplicates = \
            [item for item, count in col_names_counter.items() if count > 1]
        if duplicates:
            return_val.append(('ERROR',
                    'duplicate column name' + \
                    ((" '" + duplicates[0] + "'") if len(duplicates) == 1 \
                    else ('s: ' + str(duplicates)))))
        if not return_val:
            # save response column
            self._s_y = self._df_x[response]
            if self._config['mode'].lower() == 'regression':
                if self._s_y.dtype.name not in ['float64', 'int64']:
                    return_val.append(('ERROR',
                        'regression selected but response type is ' + \
                        self._s_y.dtype.name))
        if not return_val:
            # drop features in to_drop
            # pylint: disable=maybe-no-member
            if response not in to_drop:
                to_drop.append(response)
            self._df_x.drop(to_drop, axis=1, inplace=True)
            # check predictor types
            df_x_types = self._df_x.dtypes
            # pylint: enable=maybe-no-member
            unknown_types = df_x_types.apply(
                lambda x: x.name not in ['float64', 'int64'])
            for label, ukn in df_x_types.iloc[list(unknown_types)].iteritems():
                return_val.append(('ERROR',
                    'unexpected type ' + ukn.name + \
                    ' for column ' + label))
        if not return_val:
            # make sure no feature names begin with "shadow"
            if sum([x.lower().startswith('shadow')
                for x in self._df_x.columns.values]):
                return_val.append(('ERROR',
                    'Feature names cannot begin with shadow/Shadow.'))
        return return_val

    @staticmethod
    def __print_errors(msgs):
        """Given a list of 2-tuples, each consisting of an error type and an
        error message, prints the list to stdout."""
        for msg in msgs:
            print msg[0] + ': ' + msg[1]

    def __careful_mkdir(self, ospath):
        """Creates a directory, first checking for for existence and prompting
        to overwrite.
        """
        if os.path.exists(ospath):
            if self._noprompt:
                shutil.rmtree(ospath)
            else:
                decision = None
                while decision not in ['o', 'r', 'c']:
                    decision = raw_input('Directory ' + ospath + \
                        ' exists. Overwrite, rename, or cancel? (o/r/c)')
                if decision == 'o':
                    shutil.rmtree(ospath)
                elif decision == 'r':
                    suffix = 1
                    while os.path.exists(ospath + '_' + str(suffix)):
                        suffix += 1
                    os.rename(ospath, ospath + '_' + str(suffix))
                elif decision == 'c':
                    sys.exit(130)
                else:
                    raise ValueError('decision ' + decision + \
                        ' slipped through loop')
        os.makedirs(ospath)

if __name__ == '__main__':
    FST(None, None).main()
