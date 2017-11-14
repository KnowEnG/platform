from sqlalchemy import Table, Column, Index
from sqlalchemy import Integer, Text, Numeric, ARRAY, Enum, Boolean
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

        for att in tablelike_schema.numeric_attributes:
            nm = att.get_name()
            col_type = Numeric(precision=12, scale=6)
            #TODO: think through 'nullable'
            col = Column(nm, col_type)
            columns.append(col)
     
        for att in tablelike_schema.categoric_attributes:
            nm = att.get_name()
            col_type = Text()
            
            #removing use of 'Enum' columns b/c you can't
            #reuse the name (of the column) between tables
            #if att.valid_values is None:
            #    col_type = Text()
            #else:
            #    enum_name = nm + '_enum'
            #    col_type = Enum(*att.valid_values, name=enum_name)
            col = Column(nm, col_type)
            columns.append(col)
      
        for att in tablelike_schema.foreignid_attributes:
            nm = att.get_name()
            col_type = Integer()
            col = Column(nm, col_type)
            columns.append(col)
       
        for att in tablelike_schema.boolean_attributes:
            nm = att.get_name()
            col_type = Boolean()
            col = Column(nm, col_type)
            columns.append(col)
        
        for att in tablelike_schema.json_attributes:
            nm = att.get_name()
            col_type = Text()
            col = Column(nm, col_type)
            columns.append(col)
 
        for att in tablelike_schema.int_attributes:
            nm = att.get_name()
            col_type = Integer()
            col = Column(nm, col_type)
            columns.append(col)
                      
        for att in tablelike_schema.numeric_list_attributes:
            nm = att.get_name()
            col_type = ARRAY(Numeric(precision=12, scale=6))
            col = Column(nm, col_type)
            columns.append(col)
     
        #not using enums in the list for now b/c of this issue:
        #http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#using-enum-with-array
        for att in tablelike_schema.categoric_list_attributes:
            nm = att.get_name()
            #TODO: at least make the length as long as the longest possible value
            col_type = ARRAY(Text())
            col = Column(nm, col_type)
            columns.append(col)

        for att in tablelike_schema.foreignid_list_attributes:
            nm = att.get_name()
            col_type = ARRAY(Integer())
            col = Column(nm, col_type)
            columns.append(col)

        for att in tablelike_schema.int_list_attributes:
            nm = att.get_name()
            col_type = ARRAY(Integer())
            col = Column(nm, col_type)
            columns.append(col)

        #TODO: put the columns back in order that they were
        #declared in the schema (follow the developer's intent)

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

