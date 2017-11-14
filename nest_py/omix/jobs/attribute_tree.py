from nest_py.omix.jobs.sparse_array import SparseArray

class AttributeTree(object):
    """
    A tree where every node has a dictionary of
    attributes and a list of child subtrees.
    """

    def __init__(self):
        self.attributes = dict()
        self.child_trees = list()
        return

    def copy(self):
        tr = AttributeTree()
        for k in self.attributes:
            tr.set_attribute(k, self.attributes[k])
        for child in self.child_trees:
            tr.add_child(child.copy())
        return tr

    def add_child(self, subtree):
        """
        subtree (AttributeTree)
        """
        self.child_trees.append(subtree)
        return

    def get_children(self):
        return self.child_trees

    def set_attribute(self, key, value):
        self.attributes[key] = value
        return

    def get_attribute(self, key):
        return self.attributes[key]

    def has_attribute(self, key):
        return (key in self.attributes)

    def is_leaf(self):
        return (len(self.child_trees) == 0)

    def init_common_sparse_array_attribute(self, att_name, 
        array_size, not_set_value=0.0):
        sparse_ary = SparseArray(array_size, not_set_value=not_set_value)
        self.set_attribute(att_name, sparse_ary)
        for child_tree in self.child_trees:
            child_tree.init_common_sparse_array_attribute(
                att_name, array_size, not_set_value=not_set_value)
        return

    def find_child(self, match_key, match_value):
        """
        finds the immediate child that has the attribute
        match_key = match_value. return None if it doesn't match.
        only returns the first one found if there are multiple
        """
        for child_tree in self.child_trees:
            if child_tree.has_attribute(match_key):
                if (match_value == child_tree.get_attribute(match_key)):
                    return child_tree
        return None
    
    def to_jdata(self):
        """
        dump to all nested dicts
        """
        jdata = dict()
        jdata['attributes'] = dict()
        for k in self.attributes:
            v = self.attributes[k]
            try: 
                jdata['attributes'][k] = v.to_jdata()
            except:
                jdata['attributes'][k] = v

        children_jdata = list()
        for child_tree in self.child_trees:
            children_jdata.append(child_tree.to_jdata())
        jdata['children'] = children_jdata
        return jdata
               
