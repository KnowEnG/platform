# -*- coding: utf-8 -*-
"""Defines the user type."""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema
from nest_py.core.data_types.tablelike_entry import TablelikeEntry

COLLECTION_NAME = 'nest_users'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_categoric_attribute('username')
    schema.add_categoric_attribute('given_name')
    schema.add_categoric_attribute('family_name')
    schema.add_categoric_attribute('thumb_url')
    schema.add_categoric_attribute('passlib_hash')
    schema.add_boolean_attribute('is_superuser')

    #origin is simple name for how the user was created, e.g.
    #users defined in the core nest_config have origin 'config:core'
    schema.add_categoric_attribute('origin')

    #optional: if 'origin' is an external system, external_id
    #allows you to save an identifier (as a string) to
    #cross-reference across the two systems
    schema.add_categoric_attribute('external_id')
    return schema

class NestUser(object):
    """Represents a user of the system."""

    def __init__(self, nest_id, username, given_name, family_name, 
        is_superuser=False, passlib_hash='EXTERNAL', 
        thumb_url='', origin='Unspecified', 
        external_id=None):
        """
        Creates a NestUser instance.

        Args:
        nest_id (NestId): a UUID for the user. Can be None 
            TODO: should it be optional since it can be None?
        username (str): the login name for the user.
        given_name (str): the user's given name to display on screen.
        family_name (str): the user's family name to display on screen.
        thumb_url (Optional[str]): a URL for the user's thumbnail image.
        origin (Optional[str]): an identifier for how the user was defined
        external_id (optional(str)): if 'origin' is an external system,
            this field can hold a key of the user on that system
        passlib_hash(optional(str)): if the user is a native user
        """
        self.nest_id = nest_id
        self.username = username

        self.given_name = given_name
        self.family_name = family_name
        self.thumb_url = thumb_url

        self.origin = origin
        self.external_id = external_id

        self.passlib_hash = passlib_hash
        self.superuser = is_superuser
        return

    def get_nest_id(self):
        """Returns the userid.
        """
        return self.nest_id

    def set_nest_id(self, nest_id):
        self.nest_id = nest_id
        return

    def get_username(self):
        """Returns the login name.
        """
        return self.username

    def is_superuser(self):
        return self.superuser

    def get_given_name(self):
        """Returns the given name to display on screen."""
        return self.given_name

    def get_family_name(self):
        """Returns the family name to display on screen."""
        return self.family_name

    def get_thumb_url(self):
        """Returns the thumbnail image URL."""
        return self.thumb_url

    def get_origin(self):
        return self.origin

    def get_external_id(self):
        return self.external_id

    def __eq__(self, other):
        if other is None:
            return False
        jd = self.to_tablelike_entry()
        ojd = other.to_tablelike_entry()
        return (jd == ojd)

    def __str__(self):
        tle = self.to_tablelike_entry()
        s = str(tle)
        return s

    def to_tablelike_entry(self):
        tl_schema = generate_schema()
        tle = TablelikeEntry(tl_schema)
        tle.set_nest_id(self.nest_id)
        tle.set_value('username', self.username)
        tle.set_value('given_name', self.given_name)
        tle.set_value('family_name', self.family_name)
        tle.set_value('thumb_url', self.thumb_url)
        tle.set_value('origin', self.origin)
        tle.set_value('external_id', self.external_id)
        tle.set_value('passlib_hash', self.passlib_hash)
        tle.set_value('is_superuser', self.superuser)
        return tle

    @staticmethod
    def from_tablelike_entry(tle):
        nid = tle.get_nest_id()
        nu = NestUser(
            nid,
            tle.get_value('username'),
            tle.get_value('given_name'),
            tle.get_value('family_name'),
            passlib_hash=tle.get_value('passlib_hash'),
            thumb_url=tle.get_value('thumb_url'),
            origin=tle.get_value('origin'),
            external_id=tle.get_value('external_id'),
            is_superuser=tle.get_value('is_superuser')
            )
        return nu

    def to_jdata(self):
        tle = self.to_tablelike_entry()
        schema = tle.get_schema()
        jd = schema.object_to_jdata(tle)
        return jd
