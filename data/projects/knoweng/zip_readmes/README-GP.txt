README (Gene Prioritization)

In the output folder, you will see four types of files. The file called 
"gene_name_mapping.tsv" contains the mapping between your gene names and 
ENSEMBL IDs. In addition, a file that its name starts with 
"ranked_genes_per_phenotype" contains the ranked list of genes for each 
phenotype, and a file that its name starts with "top_genes_per_phenotype" 
conatains a binary value for each gene for each phenotype where 1 means the 
gene was among the top 100 for that phenotype and 0 otherwise. This file can be 
used in the Gene Set Characterization pipeline. Finally, for each phenotype, 
there exists a file that its name starts with the name of phenotype, provides 
several types of information for each gene. This type contains column names 
"Response", "Gene_ENSEMBL_ID", "quantitative_sorting_score", 
"visualization_score", and "baseline_score". Depending on the options you have 
selected for the GP pipeline, these columns and their interpretations are 
different, described below.


################################################################################

Option 1 (Pearson Correlation):

Choices:
Primary prioritization method = Absolute Pearson Correlation
Use knowledge Network = No
Use bootstrapping = No

Column headers and their interpretation:
Response: Name of the phenotype of interest.
Gene_ENSEMBL_ID: The ENSEMBL ID of the gene.
quantitative_sorting_score: The absolute value of the Pearson correlation 
coefficient between the phenotype and the gene.  A higher value shows the gene 
is more relevant to the phenotype. This value is between 0 and 1.
visualization_score: The min-max normalized value of 
quantitative_sorting_score. This value is always between 0 and 1.
baseline_score: The Pearson correlation coefficient between the phenotype and 
the gene.


Option 2 (Robust Pearson Correlation):

Choices:
Primary prioritization method = Absolute Pearson Correlation
Use knowledge Network = No
Use bootstrapping = Yes

Column headers and their interpretation:
Response: Name of the phenotype of interest.
Gene_ENSEMBL_ID: The ENSEMBL ID of the gene.
quantitative_sorting_score: The aggregate score of the gene.  This score is 
obtained by aggregating ranked lists of genes using Borda method. Each ranked 
list corresponds to one instance of bootstrap sampling and is ranked using the 
absolute Pearson correlation coefficient. A higher value shows the gene is more 
relevant to the phenotype. This value is always between 1 and the total number 
of genes.
visualization_score: The min-max normalized value of 
quantitative_sorting_score. This value is always between 0 and 1.
baseline_score: The Pearson correlation coefficient between the phenotype and 
the gene.


Option 3 (ProGENI):

Choices:
Primary prioritization method = Absolute Pearson Correlation
Use knowledge Network = Yes
Use bootstrapping = No

Column headers and their interpretation:
Response: Name of the phenotype of interest.
Gene_ENSEMBL_ID: The ENSEMBL ID of the gene.
quantitative_sorting_score: The ProGENI score of the gene.  A higher value 
shows the gene is more relevant to the phenotype. This value is always between 
-1 and 1.
visualization_score: The min-max normalized value of 
quantitative_sorting_score. This value is always between 0 and 1.
baseline_score: The Pearson correlation coefficient between the phenotype and 
the gene.
Percent_appearing_in_restart_set: Multiplying this number with 100 gives the 
percent of the bootstrapping instances in which this gene was used in the 
restart set of ProGENI. Since no bootstrapping was done in this option, these 
values are either 0 or 1.


Option 4 (Robust-ProGENI):

Choices:
Primary prioritization method = Absolute Pearson Correlation
Use knowledge Network = Yes
Use bootstrapping = Yes

Column headers and their interpretation:
Response: Name of the phenotype of interest.
Gene_ENSEMBL_ID: The ENSEMBL ID of the gene.
quantitative_sorting_score: The aggregate score of the gene.  This score is 
obtained by aggregating ranked lists of genes using Borda method. Each ranked 
list corresponds to one instance of bootstrap sampling and is ranked using the 
ProGENI score. A higher value shows the gene is more relevant to the phenotype. 
This value is always between 1 and the total number of genes.
visualization_score: The min-max normalized value of 
quantitative_sorting_score. This value is always between 0 and 1.
baseline_score: The Pearson correlation coefficient between the phenotype and 
the gene.
Percent_appearing_in_restart_set: Multiplying this number with 100 gives the 
percent of the bootstrapping instances in which this gene was used in the 
restart set of ProGENI.


################################################################################

Option 2 (T-test):

Choices:
Primary prioritization method = T-test
Use knowledge Network = No
Use bootstrapping = No

Column headers and their interpretation:
Response: Name of the phenotype of interest.
Gene_ENSEMBL_ID: The ENSEMBL ID of the gene.
quantitative_sorting_score: The absolute value of the T-statistic.  A higher 
value shows the gene is more differentially expressed. 
visualization_score: The min-max normalized value of 
quantitative_sorting_score. This value is always between 0 and 1.
baseline_score: The T-statistic for each gene obtained by comparing gene 
expression for the two phenotype options.


Option 2 (Robust T-test):

Choices:
Primary prioritization method = T-test
Use knowledge Network = No
Use bootstrapping = Yes

Column headers and their interpretation:
Response: Name of the phenotype of interest.
Gene_ENSEMBL_ID: The ENSEMBL ID of the gene.
quantitative_sorting_score: The aggregate score of the gene.  This score is 
obtained by aggregating ranked lists of genes using Borda method. Each ranked 
list corresponds to one instance of bootstrap sampling and is ranked using the 
absolute value of the T-statistic. A higher value shows the gene is more 
differentially expressed. This value is always between 1 and the total number 
of genes.
visualization_score: The min-max normalized value of 
quantitative_sorting_score. This value is always between 0 and 1.
baseline_score: The T-statistic for each gene obtained by comparing gene 
expression for the two phenotype options.


Option 3 (ProGENI):

Choices:
Primary prioritization method = T-test
Use knowledge Network = Yes
Use bootstrapping = No

Column headers and their interpretation:
Response: Name of the phenotype of interest.
Gene_ENSEMBL_ID: The ENSEMBL ID of the gene.
quantitative_sorting_score: The ProGENI score of the gene.  A higher value 
shows the gene is more relevant to the phenotype. This value is always between 
-1 and 1.
visualization_score: The min-max normalized value of 
quantitative_sorting_score. This value is always between 0 and 1.
baseline_score: The T-statistic for each gene obtained by comparing gene 
expression for the two phenotype options.
Percent_appearing_in_restart_set: Multiplying this number with 100 gives the 
percent of the bootstrapping instances in which this gene was used in the 
restart set of ProGENI. Since no bootstrapping was done in this option, these 
values are either 0 or 1.


Option 4 (Robust-ProGENI):

Choices:
Primary prioritization method = T-test
Use knowledge Network = Yes
Use bootstrapping = Yes

Column headers and their interpretation:
Response: Name of the phenotype of interest.
Gene_ENSEMBL_ID: The ENSEMBL ID of the gene.
quantitative_sorting_score: The aggregate score of the gene.  This score is 
obtained by aggregating ranked lists of genes using Borda method. Each ranked 
list corresponds to one instance of bootstrap sampling and is ranked using the 
ProGENI score. A higher value shows the gene is more relevant to the phenotype. 
This value is always between 1 and the total number of genes.
visualization_score: The min-max normalized value of 
quantitative_sorting_score. This value is always between 0 and 1.
baseline_score: The T-statistic for each gene obtained by comparing gene 
expression for the two phenotype options.
Percent_appearing_in_restart_set: Multiplying this number with 100 gives the 
percent of the bootstrapping instances in which this gene was used in the 
restart set of ProGENI.

