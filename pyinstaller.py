"""
This file is able to create a self contained Conan executable that contains all it needs,
including the Python interpreter, so it wouldnt be necessary to have Python installed
in the system
It is important to install the dependencies and the project first with "pip install -e ."
which configures the project as "editable", that is, to run from the current source folder
After creating the executable, it can be pip uninstalled

$ pip install -e .
$ python pyinstaller.py

This has to run in the same platform that will be using the executable, pyinstaller does
not cross-build

The resulting executable can be put in the system PATH of the running machine
"""

import os
import platform
import shutil
import subprocess
from distutils import dir_util

from proctracer import __version__


def _install_pyinstaller(pyinstaller_path):
    subprocess.call("pip install pyinstaller", shell=True)
    # try to install pyinstaller if not installed
    if not os.path.exists(pyinstaller_path):
        os.mkdir(pyinstaller_path)


def _run_bin(pyinstaller_path):
    # run the binary to test if working
    proctracer_bin = os.path.join(pyinstaller_path, 'dist', 'proctracer', 'proctracer')
    retcode = os.system(proctracer_bin)
    if retcode != 0:
        raise Exception("Binary not working")

def pyinstall(source_folder):
    pyinstaller_path = os.path.join(os.getcwd(), 'pyinstaller')
    _install_pyinstaller(pyinstaller_path)
    command = "pyinstaller"  # "python pyinstaller.py"

    try:
        shutil.rmtree(os.path.join(pyinstaller_path))
    except Exception as e:
        print("Unable to remove old folder", e)

    proctracer_path = os.path.join(source_folder, 'proctracer', 'proctracer.py')
    hidden = ("--hidden-import=glob "
              "--hidden-import=pathlib "
              "--hidden-import=distutils.dir_util "
             )

    hidden += " --hidden-import=setuptools.msvc"
    #hidden=()
    win_ver = ""

    if not os.path.exists(pyinstaller_path):
        os.mkdir(pyinstaller_path)
    subprocess.call('%s -y -p "%s" --console "%s" %s %s'
                    % (command, source_folder, proctracer_path, hidden, win_ver),
                    cwd=pyinstaller_path, shell=True)

    _run_bin(pyinstaller_path)

    return os.path.abspath(os.path.join(pyinstaller_path, 'dist', 'proctracer'))


if __name__ == "__main__":
    src_folder = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
    output_folder = pyinstall(src_folder)
    print("\n**************Proc Tracer binaries created!******************\n"
          "\nAppend this folder to your system PATH: '%s'\n"
          "Feel free to move the whole folder to another location." % output_folder)
