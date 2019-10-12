class BasicEqualityMixin(object):
    """
    Provides equals and not-equals methods based on the
    member variables of the object being equal. Can be
    inherited by any class where only those variables
    are considered for equality
    """

    def __eq__(self, other):
        #note: I'm not checking for the class to be the same
        #b/c I don't want to make assumptions about how
        #subclasses will work.
        is_eq = (self.__dict__ == other.__dict__)
        return is_eq

    def __ne__(self, other):
        return not self.__eq__(other)

class BasicPrintMixin(object):
    """
    Provides simple str and repr methods to a class based on whatever the
    member variables of the class are
    """

    def __repr__(self):
        """unambigous/exact string"""
        cname = self.__class__.__name__
        s =  cname + '::' + str(self.__dict__)
        return s
 
    def __str__(self):
        """human readable string"""
        return repr(self)

class BasicPopoMixin(BasicEqualityMixin, BasicPrintMixin):
    """
    Inherits the individual Basic*Mixin classes for a class that
    can be treated as a data container (plain old python object: POPO)
    """
    pass
       
