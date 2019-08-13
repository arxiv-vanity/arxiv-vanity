#!/usr/bin/env python
from gevent import monkey

monkey.patch_all()
from psycogreen.gevent import patch_psycopg

patch_psycopg()

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arxiv_vanity.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
