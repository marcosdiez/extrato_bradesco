from collections import OrderedDict
import os
import json
import sys

data = json.load(open(sys.argv[1]), object_pairs_hook=OrderedDict)


print data["ofx"]