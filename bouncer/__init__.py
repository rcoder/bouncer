#!/usr/bin/env python

# Copyright 2013 by Urban Airship and Lennon Day-Reynolds <lennon@urbanairship.com>
# See license information in COPYING.

import os
import re

VERSION = '0.0.1'
DESC = 'Simple internal URL shortener/expander for teams'

from bouncer.web import app

def main():
  port = os.environ.get("BOUNCER_HTTP_PORT", 5688)
  debug = bool(os.environ.get("BOUNCER_DEBUG", None))
  app.debug = debug
  app.run(port=port)

if __name__ == '__main__':
  main()

