import os
import sys
from importlib import util
import glob

import_path_order  = [
    'plugin_base.py',
    'plugin_proc_tracer_base.py',
    '**/*.plugin.py',
    ]

def load_module(path):
    module_name = os.path.split(path)[-1].split('.')[0]
    spec = util.spec_from_file_location(module_name, path)
    module = util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

for path in import_path_order:
    for plugin_path in glob.glob('%s/%s' % ( __file__.rsplit(os.sep,1)[0], path) , recursive = True):
        load_module(plugin_path)
