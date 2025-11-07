#!/usr/bin/env python3

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from chrplunk.application import Application

if __name__ == '__main__':
    app = Application()
    sys.exit(app.run(sys.argv))
