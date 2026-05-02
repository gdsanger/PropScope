#!/bin/bash

set -e

cp -R "/Users/admin/Library/Application Support/WSJT-X/ALL.TXT" "/Users/admin/PropScope/data/ALL.TXT"

/Users/admin/PropScope/venv/bin/python /Users/admin/PropScope/manage.py poll_wsjtx_log
