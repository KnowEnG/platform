This file contains a description of the different output files of the gene set 
characterization (GSC) pipeline. The format of some output files will vary 
depending on the parameter options selected.

The downloaded zip file will contain one directory for each public gene set 
collection that was selected during the analysis configuration.

Within each directory will be two files:
  A) a "*.edge" file that describes the gene set membership in the public 
collection and
  B) a "*.df" file that contains the results of the analysis


A) "*.edge" Gene Set Membership File

  The columns of this file are defined as follows.

  1) property_gene_set_id: the internal KnowEnG id for a the public gene set
  2) gene_id: the internal KnowEnG id for a gene in that public gene set
  3) normalized_score: the score of the membership interaction normalized to 
sum to one for the whole file.  For most public gene sets collections, the 
membership score is the same of all interactions, so this is just 1/(number of 
lines in the file)
  4) edge_type: the KnowEnG internal keyword for the edge type of this public 
gene sets collection
  5) dataset_source: the KnowEnG internal keyword for the name of the public 
resource file we extracted the membership relationship from
  6) source_line_number: the line number in the original public resource file 
we extracted this relationship from

B) "*.df" Association Results File

  The format of this file will depend on the choice you made whether to "Use 
the Knowledge Network"

  - "Yes" Option (DRaWR):

    The columns of the "drawr_sorted_by_property_score_*.df" file are defined 
as follows.

    1) user_gene_set: the names of the gene sets that you submitted
    2) property_gene_set: the internal KnowEnG ids for public gene sets from 
one public gene set collection
    3) difference_score: difference of query_score (col4) and 
baseline_score(col5) divided by the largest difference in the file. This value 
is between 0 and 1 and reported when it is greater than 0.5
    4) query_score: converged stationary probability of being at the 
property_gene_set node in the chosen heterogenous network given that you 
restart at any only gene node from the user gene set. This value is between 0 
and 1.
    5) baseline_score: converged stationary probability of being at the 
property_gene_set node in the chosen heterogenous network given that you 
restart at any gene node. This value is between 0 and 1.


  - "No" Option (Fisher Exact):

    The columns of the "fisher_sorted_by_property_score_*.df" file are defined 
as follows.

    1) user_gene_set: the names of the gene sets that you submitted
    2) property_gene_set: the internal KnowEnG ids for public gene sets from 
one public gene set collection
    3) pvalue: the -1 * log10 pvalue of the one sided (alternative = 'greater') 
Fisher Exact Test using the contingency table corresponding to the user set and 
property gene set of the row. This value is reported when it is greater than 2.
        NOTE1: You can take 10^-x to convert these values back into the 
original pvalues.
        NOTE2: These pvalues (-1*log10) have not been corrected for multiple 
hypothesis testing.
    4) universe_count: total number of genes annotated by the public gene set 
collection and listed in your spreadsheet (or known for the species of your 
submitted gene list).
    5) user_count: size of your gene set in the universe
    6) property_count: size of the public gene set in the universe
    7) overlap_count: size of the overlap between the two in the universe
