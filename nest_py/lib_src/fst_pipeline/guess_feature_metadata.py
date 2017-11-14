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

import csv
import pandas as pd
import sys

def guess_feature_metadata(infile, outfile):
    """Reads infile, guesses a group name for each feature found therein,
    and writes a table of feature names and group names to outfile."""
    with open(infile, 'r') as f_infile:
        reader = csv.reader(f_infile)
        for line in reader:
            groups = [guess_feature_group(feature) for feature in line]
            df_out = pd.DataFrame(
                data={'group': groups},
                index=line)
            df_out.to_csv(outfile, index_label='feature')
            break

def guess_feature_group(feature):
    """Given a feature name, returns a best-guess group name."""
    prefix_list = (
        ('Sha', 'Shadow'),
        ('miRNA', 'miRNA'),
        ('chr', 'mRNA'),
        ('Fir', 'Firmicutes'),
        ('Act', 'Actinobacteria'),
        ('Bac', 'Bacterodetes'),
        ('Pro', 'Proteobacteria'),
        ('Ami', 'Amino Acid'),
        ('Pep', 'Peptide'),
        ('Car', 'Carbohydrate'),
        ('Ene', 'Energy'),
        ('Lip', 'Lipid'),
        ('Nuc', 'Nucleotide'),
        ('Cof', 'Cofactor or Vitamin'),
        ('Xen', 'Xenobiotics'),
        ('Gen', 'Genus OTU'),
        ('MET', 'Metabolite'),
        ('OTU', 'OTU'),
        ('V.K', 'Vaginal Functional'),
        ('F.K', 'Fecal Functional'),
        ('V.G', 'Vaginal Gene'),
        ('F.G', 'Fecal Gene'),
        ('V.', 'Vaginal OTU'),
        ('F.', 'Fecal OTU')
    )
    for prefix, group in prefix_list:
        if feature.startswith(prefix):
            return group
    return 'NA'

if __name__ == '__main__':
    guess_feature_metadata(sys.argv[1], sys.argv[2])
