from sqlalchemy import Table, Column, Index
from sqlalchemy import Integer, Text, Numeric, ARRAY, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from nest_py.core.db.sqla_maker import SqlaMaker

class TablelikeSqlaMaker(SqlaMaker):

    def __init__(self, schema, security_policy=None):
        self.schema = schema
        name = schema.get_name()
        super(TablelikeSqlaMaker, self).__init__(
            name, schema, security_policy=security_policy)
        return

    def get_sqla_table(self, metadata):
        tbl = ensure_table(metadata, self.schema, self.schema.get_name())
        return tbl


def ensure_table(sqla_metadata, tablelike_schema, table_name):
    """
    create a SQLAlchemy Table object bound to the
    input metadata object, or returns an existing table
    if it's already been registered with sqla_metadata
    (it is safe to call multiple times).
    The SQLA Table will have the given table_name
    and columns appropriate to the schema's attributes.
    Note that 'array' attributes will be postgres 'array'
    columns in the Table.
    Uses 'Text' columns, not 'String' b/c postgres docs say
    there is no difference in effiency between varchar and
    text columns, varchars are just to enforce contraints
    (which we don't care about for categorical and jsonblob
    types).
    """
    if table_name in sqla_metadata.tables:
        tbl = sqla_metadata.tables[table_name]
    else:
        columns = list()

        id_col = Column('id', Integer, primary_key=True)
        columns.append(id_col)

        owner_id_col = Column('owner_id', Integer)
        columns.append(owner_id_col)

        for att in tablelike_schema.get_attributes():
            col = make_column_for_attribute(att)
            columns.append(col)

        #this is smart enough to return the existing table in
        #sqla_metadata if it already has been declared
        #http://docs.sqlalchemy.org/en/latest/core/metadata.html#sqlalchemy.schema.Table
        tbl = Table(table_name, sqla_metadata, *columns)

        #add the indexes declared in the schema
        for list_of_column_names in tablelike_schema.indexes:
            columns = list()
            for cname in list_of_column_names:
                columns.append(tbl.c[cname])
            #we don't really care about the name, but sqlalchemy requires
            #one (postgres does not)
            index_name = 'nestidx_' + '_'.join(list_of_column_names)
            Index(index_name, *columns)

    return tbl

def make_column_for_attribute(tablelike_attribute):
    """
    Given an Attribute of a TablelikeSchema, create a corresponding
    SQLAlchemy Column object for storing that type of data with
    the same name and constraints (where applicable)
    """

    att = tablelike_attribute
    att_type = att.get_type()
    att_name = tablelike_attribute.get_name()
    
    if 'Numeric'== att_type:
        col_type = Numeric(precision=att.precision, scale=att.scale)
    elif 'Categoric' == att_type:
        col_type = Text()
    elif 'ForeignId' == att_type:
        col_type = Integer()
    elif 'Boolean' == att_type:
        col_type = Boolean()
    elif 'Json' == att_type:
        col_type = Text()
    elif 'JsonB' == att_type:
        col_type = JSONB()
    elif 'Int' == att_type:
        col_type = Integer()
    elif 'NumericList' == att_type:
        col_type = ARRAY(Numeric(precision=att.precision, scale=att.scale))
    elif 'CategoricList' == att_type:
        #not using enums in the list for now b/c of this issue:
        #http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#using-enum-with-array
        #TODO: at least make the length as long as the longest possible value
        col_type = ARRAY(Text())
    elif 'ForeignIdList' == att_type:
        col_type = ARRAY(Integer())
    elif 'IntList' == att_type:
        col_type = ARRAY(Integer())
    else:
        raise Exception("Problem making a column for attribute '" + 
            str(att_name) + "' of unrecognized type: '" + str(att_type))

    col = Column(att_name, col_type)
    return col

