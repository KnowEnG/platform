import pytest

def test_biom_lib():
    """
    the biom-format library has difficult dependencies to get
    correct. this just makes sure the module is available

    this example is taken from: 
    http://biom-format.org/documentation/table_objects.html
    """
    import biom
    from biom.table import Table as BiomTable

    import numpy as np

    data = np.arange(40).reshape(10, 4)
    sample_ids = ['S%d' % i for i in range(4)]
    observ_ids = ['O%d' % i for i in range(10)]
    sample_metadata = [{'environment': 'A'}, {'environment': 'B'},
                       {'environment': 'A'}, {'environment': 'B'}]
    observ_metadata = [{'taxonomy': ['Bacteria', 'Firmicutes']},
                       {'taxonomy': ['Bacteria', 'Firmicutes']},
                       {'taxonomy': ['Bacteria', 'Proteobacteria']},
                       {'taxonomy': ['Bacteria', 'Proteobacteria']},
                       {'taxonomy': ['Bacteria', 'Proteobacteria']},
                       {'taxonomy': ['Bacteria', 'Bacteroidetes']},
                       {'taxonomy': ['Bacteria', 'Bacteroidetes']},
                       {'taxonomy': ['Bacteria', 'Firmicutes']},
                       {'taxonomy': ['Bacteria', 'Firmicutes']},
                       {'taxonomy': ['Bacteria', 'Firmicutes']}]
    table = BiomTable(data, observ_ids, sample_ids, observ_metadata,
                   sample_metadata, table_id='Example Table')

    print table.ids(axis='observation')
    print table.ids(axis='sample')
    return
