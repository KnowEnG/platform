
class SecurityPolicy(object):
    """
    For a single collection (usually a table in a database), 
    provides the rules for what a given user can access.
    Intended to be used at the level of CrudDbClient.

    Mostly a placeholder at the moment, hopefully can add
    more elaborate security management incrementally.
    """

    def __init__(self, anyone_can_write=True, anyone_can_read_all=False):
        """

        """
        self.anyone_can_write = anyone_can_write
        self.anyone_can_read_all = anyone_can_read_all
        return

    def can_read_all_entries(self, nest_user):
        """
        nest_user (NestUser): the NestUser trying to access the 
            table
        Returns True if the NestUser is allowed to read all rows
            in the table, regardless of whether they are the
            owner or not.
        """
        if nest_user.is_superuser():
            permission = True
        else:
            permission = self.anyone_can_read_all
        return permission

    def can_write_entries(self, nest_user):
        """
        nest_user (NestUser): the NestUser trying to access the 
            table
        Returns True if the NestUser is allowed to write new rows
            in the table.
        """
        if nest_user.is_superuser():
            permission = True
        else:
            permission = self.anyone_can_write
        return permission


class SecurityException(Exception):
    """
    Exception to indicate an attempt to access data in the database,
    as determined by the rules Nest tries to enforce itself for
    data access (only a user who created a data entry can access it)
    """

    def __init__(self, *args):
        super(SecurityException, self).__init__(self, *args)
        return

