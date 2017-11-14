# -*- coding: utf-8 -*-
"""Python 2/3 compatibility module."""

#FIXME: can we delete this whole module? I don't understand 
# when it is supposed to get imported. I don't think it currently
#is getting imported at all
#
import sys

PY2 = int(sys.version[0]) == 2

# pylint: disable=redefined-builtin
# pylint: disable=invalid-name
if PY2:
    text_type = unicode
    binary_type = str
    string_types = (str, unicode)
    unicode = unicode
    basestring = basestring
else:
    text_type = str
    binary_type = bytes
    string_types = (str,)
    unicode = str
    basestring = (str, bytes)
# pylint: enable=redefined-builtin
# pylint: enable=invalid-name
