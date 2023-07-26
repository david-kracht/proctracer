# /proc Tracer

This is the developer/maintainer documentation. For user documentation, go to https://github.com/david-kracht/proctracer

## Setup

You can run proctracer from source in Windows, MacOS, and Linux:

- Install pip following [pip docs](https://pip.pypa.io/en/stable/installation/).

- Clone proctracer repository:
```bash
$ git clone https://github.com/david-kracht/proctracer.git
```

- Install in editable mode
```bash
$ cd proctracer && sudo pip install -e .
```

- You are ready, try to run proctracer:
```bash
$  proctracer --help
usage: /proc Tracer (Daemon) [-h] [-c CONFIG] [-o OUTPUT_PATH] [-n REPORT_NAME] [-f] {start,stop,restart,message} ...

positional arguments:
  {start,stop,restart,message}
    start               Start Tracer
    stop                Stop Tracer
    restart             Restart Tracer
    message             Message to Running Tracer

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to /proc Tracer config yaml.
  -o OUTPUT_PATH, --output_path OUTPUT_PATH
                        Output path for report.
  -n REPORT_NAME, --report_name REPORT_NAME
                        Name of the report file.
  -f, --foreground      Start Tracer in foreground, not daemonized.
```

- Examplary usage and result:
```bash
$ proctracer -o ~/1/2 -n proc_report start
Start /proc Tracer (Daemon)...
Output will be written to: /root/1/2

$ proctracer message first
Message to running /proc Tracer (Daemon) ...
$ proctracer message 2nd
Message to running /proc Tracer (Daemon) ...
$ proctracer message 2nd
Message to running /proc Tracer (Daemon) ...
$ proctracer message 3rd
Message to running /proc Tracer (Daemon) ...

$ stress -c 1 -t 5
stress: info: [514601] dispatching hogs: 1 cpu, 0 io, 0 vm, 0 hdd
stress: info: [514601] successful run completed in 5s

$ proctracer stop
Stop /proc Tracer (Daemon).

$ tree ~/1
/home/user/1
└── 2
    └── proc_report.pdf
```

- Package and Upload
Place token in ```~/.pypirc```, i.e

> [pypi]
> username = __token__
> password = pypi-AgEIcHlwa0A5vasXU4w


```bash
$ chmod 600 ~/.pypirc

$ sudo pip install twine

$ python3 setup.py sdist bdist_wheel
$ twine upload dist/*
```