"""
Common interface to get the main global SQLAlchemy classes from
either Flask or to build the directly (as Jobs must do).
"""
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

class FlaskSqlaResources(object):
    """
    Interface to sqlalchemy system when accessing db from
    flask. Intended to be used as a Singleton (only one
    instance running at a time)
    """

    def __init__(self, flask_sqla, db_config):
        """
        flask_sqla (flask_sqlalchemy.SQLAlchemy) already bound
        to the flask app but not the tables in the db.
        db_config (dict of params) see nest_db for default config
        """
        self.flask_sqla = flask_sqla
        self.config = db_config
        return

    def get_session(self):
        """
        get an sqla Session
        """
        session = self.flask_sqla.session
        return session

    def get_engine(self):
        """
        """
        engine = self.flask_sqla.engine
        return engine

    def get_declarative_base(self):
        base = self.flask_sqla.Model
        return base

    def get_metadata(self):
        md = self.flask_sqla.metadata
        return md

class JobsSqlaResources(object):
    """
    Interface to sqlalchemy system when accessing db from
    jobs.
    """

    def __init__(self, config): 
        self.config = config
        self.session = None
        self.declarative_base = None
        self.engine = None
        return

    def set_config(self, config):
        self.config = config
        return

    def get_session(self):
        """
        get an sqla Session
        """
        if self.session is None:
            engine = self.get_engine()
            Session = sessionmaker(bind=engine)
            self.session = Session()
        return self.session

    def get_engine(self):
        """
        """
        if self.engine is None:
            engine_url = get_engine_url(self.config)
            verbose_logging = self.config['verbose_logging']
            self.engine = create_engine(engine_url, echo=verbose_logging)
        return self.engine

    def get_declarative_base(self):
        if self.declarative_base is None:
            self.declarative_base = declarative_base()
        return self.declarative_base

    def get_metadata(self):
        md = self.get_declarative_base().metadata
        return md

def get_engine_url(config):
    #http://docs.sqlalchemy.org/en/latest/core/engines.html#sqlalchemy.create_engine
    engine_url = 'postgres://'
    engine_url += config['user'] 
    if not config['password'] is None:
        engine_url += ':' + config['password']
    engine_url += '@' + config['host']
    engine_url += '/' + config['db_name']
    return engine_url

