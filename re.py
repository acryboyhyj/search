# -*- coding: utf-8 -*-

import re

line = "ni    hao"
reg_str = "(ni\shao)"

match = re.match(reg_str,line)
if match:
    print (match.group(1))
