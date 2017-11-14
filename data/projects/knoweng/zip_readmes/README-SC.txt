This file contains a description of the different output files of the sample 
clustering (SC) pipeline. 

The downloaded zip file will contain four files for users to further examine 
their results.

A) "cluster_labels.tsv" Sample Cluster Assignment File. 
The columns of this file are defined as follows.
  1) sample_id: the identifier for a sample from the genomic spreadsheet
  2) cluster_assignment: integer value (from 0 to number_of_clusters - 1) for 
the sample’s assigned cluster 

B) "consensus_matrix.tsv" Bootstrap Consensus Matrix File.  
This file contains a matrix with the genomic spreadsheet sample_ids as the row 
and column names.  The values in the matrix indicate the proportion of the 
number of bootstraps where the corresponding samples co-cluster.  If 
bootstrapping was not used, these values will be binary {0, 1}. 

C) “top_genes_by_cluster.tsv” Cluster Genes Spreadsheet File. 
This file contains a matrix with the cluster numbers as the columns headers and 
stable Ensembl gene_ids as the rows. A ‘1’ in this table indicates that the 
row gene was one of the top 100 most important (highest scoring) genes for that 
specific column cluster.  All other values are 0.  Importance is calculated as 
the average value across the cluster.  If the Knowledge Network was used, then 
it is the average of the stationary probabilities of the random walks on each 
sample.

D) “gene_name_mapping.tsv” Gene Identifier Mapping File.  
The columns of this file are defined as follows.
    1) KN_gene_id: the internal KnowEnG id for a gene used in the 
top_genes_by_cluster.tsv
    2) user_gene_id: the corresponding gene/transcript/protein identifier 
supplied by the user in the original genomic spreadsheet.
