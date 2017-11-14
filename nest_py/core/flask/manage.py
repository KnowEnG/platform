# -*- coding: utf-8 -*-
"""
    This script defines commonly-used CLI commands.

    FIXME: This hasn't been tested in a while. Decide
    if we want to keep it. If so, could use a nest_ops
        command
"""
from flask_script import Manager, Shell, Server

from nest_py.core.flask import app2

APP = app2.make_flask_app()

MANAGER = Manager(APP)

def _make_context():
    """Return context dict for a shell session so you can access
    app by default.
    """
    return {'app': APP}

@MANAGER.command
def routes():
    """Print the application's routes to stdout."""
    import urllib
    output = []
    for rule in APP.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.unquote("{:50s} {:20s} {}".format(
            rule.endpoint, methods, rule))
        output.append(line)
    for line in sorted(output):
        print line

MANAGER.add_command('shell', Shell(make_context=_make_context))
#MANAGER.add_command('runserver', Server(host='0.0.0.0', port=80, static_files={'/static': '/app/client/dist'}))

if __name__ == '__main__':
    MANAGER.run()
