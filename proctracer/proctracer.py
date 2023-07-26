#!/usr/bin/python3

import os
import time
import sys
import signal
import yaml
from string import Template
from collections import defaultdict
import argparse

import functools
from daemonize import Daemonize

try:
    from . import plugins
except:
    import plugins

from plugin_proc_tracer_base import ProcTracerBase

import ctypes, threading
LIB = 'libcap.so.2'
try:
    libcap = ctypes.CDLL(LIB)
except OSError:
    print(
        'Library {} not found. Unable to set thread name.'.format(LIB)
    )
else:
    def _name_hack(self):
        # PR_SET_NAME = 15
        libcap.prctl(15, self.name.encode())
        threading.Thread._bootstrap_original(self)

    threading.Thread._bootstrap_original = threading.Thread._bootstrap
    threading.Thread._bootstrap = _name_hack

DEFAULT_CONFIG_YAML_PATH = "~/proctracer-config.yaml"

DEFAULT_CONFIG_YAML= """
report_name: proctracer-report
report_output_path: ${HOME}
pipe_path: ${HOME}/proctracer.pipe
pid_path: ~/proctracer.pid
plugins:
    text_pipe:
        active: true
        period: 0.2
    pressure_cpu:
        active: true
        period: 1.0
    pressure_io:
        active: true
        period: 1.0
    pressure_memory:
        active: true
        period: 1.0
    stat:
        active: true
        period: 7.0
    pid_stat:
        active: true
        period: 5.0
    net_dev:
        active: true
        period: 1.0
    net_snmp_udp:
        active: true
        period: 0.2
    net_udp4:
        active: true
        period: 0.2
    net_udp6:
        active: false
        period: 0.2
"""

def env_expand(string):
    env_dict = defaultdict(lambda: '')
    env_dict.update(**os.environ)
    return Template(string).substitute(env_dict)

def run(config):    
    ProcTracerBase.start_plugins(config)
    ProcTracerBase.register_signal_handlers()
    ProcTracerBase.consolidate()

def main():    
    #parser
    parser = argparse.ArgumentParser(prog='/proc Tracer (Daemon)')

    parser.add_argument('-c', '--config', type=str, required=False, default=DEFAULT_CONFIG_YAML_PATH , help='Path to /proc Tracer config yaml.')
    parser.add_argument('-o', '--output_path', type=str, required=False, default='' , help='Output path for report.')
    parser.add_argument('-n', '--report_name', type=str, required=False, default='' , help='Name of the report file.')
    parser.add_argument('-f', '--foreground', action='store_true', help='Start Tracer in foreground, not daemonized.')

    sp = parser.add_subparsers()
    sp_start = sp.add_parser('start', help='Start Tracer')
    sp_start.set_defaults(task='start')

    sp_stop = sp.add_parser('stop', help='Stop Tracer')
    sp_stop.set_defaults(task='stop')

    sp_restart = sp.add_parser('restart', help='Restart Tracer')
    sp_restart.set_defaults(task='restart')

    sp_message = sp.add_parser('message', help='Message to Running Tracer')
    sp_message.set_defaults(task='message')
    sp_message.add_argument('string', type=str, nargs='+', help='Message String')

    options = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    
    config_path = os.path.expanduser(options.config)
    
    #config
    if not os.path.isfile(config_path):
        print("No config existing at %s. Created and applied default config: %s "% (config_path, DEFAULT_CONFIG_YAML_PATH) )
        config_path = os.path.expanduser(DEFAULT_CONFIG_YAML_PATH)
        open(config_path, 'w').write(DEFAULT_CONFIG_YAML)
        
    if os.path.isfile(config_path):
        yaml_source = open(config_path, 'r').read()
    
    yaml_source=env_expand(yaml_source)
    config = yaml.safe_load(yaml_source)
    
    if options.output_path:
        config["report_output_path"] = os.path.expanduser(options.output_path)
    
    if 'start' == options.task:
        os.makedirs(config["report_output_path"], exist_ok=True)
    
    if options.report_name:
        config["report_name"] = options.report_name
    
    pid_path = os.path.expanduser(config["pid_path"])
    pipe_path = os.path.expanduser(config["pipe_path"])
    
    #daemon
    daemon = Daemonize(app="proctracer_daemon", pid=pid_path, action=functools.partial(run,config), foreground=options.foreground)
    
    def stop_daemon(pid):
        with open(pid, 'r') as f:
            pid = f.read()
        os.kill(int(pid), signal.SIGTERM)

    if 'start' == options.task:
        print("Start /proc Tracer (Daemon)...")
        print("Output will be written to: %s" % config["report_output_path"]) 
        daemon.start()
    elif 'stop' == options.task:
        print("Stop /proc Tracer (Daemon).")
        stop_daemon(pid_path)
    elif 'restart' == options.task:
        print("Stop. Restart /proc Tracer (Daemon)...")
        stop_daemon(pid_path)
        daemon.start()
    elif 'message' == options.task:
        print("Message to running /proc Tracer (Daemon) ...")
        with open(pipe_path, "w") as f:
            f.write("%s" % " ".join(options.string))
            
            
if __name__ == '__main__':
    main()

'''
benchmark: python3 -m cProfile -s tottime ./proctracer.py

iperf -u -sS
iperf -u -c 0.0.0.0 -t 60 -b 50G

iperf -u -s -V
iperf -u -c :: -t 60 -b 50G
'''