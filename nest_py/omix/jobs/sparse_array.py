import numpy

class SparseArray(object):
    """
    simple sparse array impl with conversions for json and numpy
    """

    def __init__(self, size, not_set_value=0.0):
        """
        not_set_value is what gets returned if the value
        at an index has never been set but gets requested
        through get_value().
        """
        self.size = size
        self.not_set_value = not_set_value
        self.data = dict()
        return

    def __len__(self):
        return self.size

    def set_value(self, index, value):
        if index < self.size:
            if not value == self.not_set_value:
                self.data[index] = value
        else:
            raise Exception('sparse array out of bounds')
        return

    def get_value(self, index):
        ret_value = self.not_set_value
        if (index >= self.size) or (index < 0):
            raise Exception('sparse array out of bounds')
        else:
            if index in self.data:
                ret_value = self.data[index]
        return ret_value

    def extract_specified_values(self):
        """
        Returns all values that do not have the 'NOT_SET_VALUE'.
        The order is unspecified.
        """
        vals = list()
        for idx in self.data:
            vals.append(self.data[idx])
        return vals

    def to_npary(self):
        """
        convert the data in this array to a numpy array. only works
        with numbers. does NOT use a sparse numpy representation
        """
        npary = numpy.zeros(self.size)
        for i in range(self.size):
            npary[i] = self.get_value(i)
        return npary

    def get_max(self):
        mx = self.not_set_value
        for k in self.data:
            if self.data[k] > mx:
                mx = self.data[k]
        return mx

    def __str__(self):
        return str(self.to_jdata())
    
    def to_jdata(self):
        return self.data

