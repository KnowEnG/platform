from nest_py.core.db.security_policy import SecurityPolicy
from nest_py.core.db.crud_db_client import CrudDbClient

class SqlaMaker(object):

    def __init__(self, table_name, sqla_transcoder, security_policy=None):
        self.transcoder = sqla_transcoder
        self.name = table_name
        if security_policy is None:
            self.security_policy = SecurityPolicy()
        else:
            self.security_policy = security_policy
        return

    def get_table_name(self):
        return self.name

    def get_sqla_table(self, metadata):
        if self.name in metadata.tables:
            table = metadata.tables[self.name]
        else:
            raise Exception("Did not find and don't know how to build" +
                " table: " + str(self.name))
        return table

    def get_db_client(self, db_engine, metadata):
        sqla_table = self.get_sqla_table(metadata)
        sp = self.security_policy
        db_client = CrudDbClient(db_engine, sqla_table, self.transcoder,
            security_policy=sp)
        return db_client
