#!/usr/bin/env python
#
# Wrap around the CASA pipeline to get logging working properly
#

from datetime import datetime
import os

now = datetime.now()
date_str = now.strftime("%Y%m%d-%H%M%S")
logfile = 'phangs_pipeline_%s.log' % date_str

command = 'python3 run_reduction.py | tee -a %s' % logfile

os.system(command)
