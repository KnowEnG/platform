# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""

from flask_cache import Cache
CACHE = Cache()

from flask_debugtoolbar import DebugToolbarExtension
DEBUG_TOOLBAR = DebugToolbarExtension()
