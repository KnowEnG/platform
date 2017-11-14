
class NestEndpointSet(object):
    """
    This class mainly exists to make building groups of endpoints
    and composing them together into a complete API is easier as
    passing around Eve's config dictionary becomes confusing quickly.
    """

    def __init__(self):
        self.endpoints = dict()
        return

    def add_endpoint(self, nest_endpoint):
        """
        """
        fep = nest_endpoint.get_flask_endpoint()
        self.endpoints[fep] = nest_endpoint
        return

    def add_endpoint_set(self, other_endpoint_set):
        """
        adds all endpoint defintions from an existing NestEndpointSet to
        this one
        other_endpoint_set(NestEndpointSet)
        returns None
        """
        for fep in other_endpoint_set.get_flask_endpoints():
            other_endpoint = other_endpoint_set.get_endpoint(fep)
            self.add_endpoint(other_endpoint)
        return

    def get_endpoint(self, flask_ep):
        return self.endpoints[flask_ep]
         
    def get_flask_endpoints(self):
        """
        get the relative_urls of the endpoints this endpointSet has
        definitions for
        Returns list of string
        """
        urls = self.endpoints.keys()
        return urls


