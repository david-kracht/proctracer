<picture>
  <!-- These are also used for https://github.com/proctracer-io/.github/blob/main/profile/README.md 
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/proctracer-io/proctracer/develop2/.github/proctracer2-logo-for-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/proctracer-io/proctracer/develop2/.github/proctracer2-logo-for-light.svg">
  <img alt="JFrog | proctracer 2.0 Logo" src="https://raw.githubusercontent.com/proctracer-io/proctracer/develop2/.github/proctracer2-logo-with-bg.svg">
  -->
</picture>

# /proc Tracer

This is the **developer/maintainer** documentation. For user documentation, go to https://github.com/david-kracht/proctracer


## Setup

You can run proctracer from source in Windows, MacOS, and Linux:

- **Install pip following** [pip docs](https://pip.pypa.io/en/stable/installation/).

- **Clone proctracer repository:**

  ```bash
  $ git clone https://github.com/david-kracht/proctracer.git
  ```

  > **Note**: repository directory name matters, some directories are known to be problematic to run tests (e.g. `proctracer`).

- **Install in editable mode**

  ```bash
  $ cd proctracer && sudo pip install -e .
  ```

  If you are in Windows, using ``sudo`` is not required.

- **You are ready, try to run proctracer:**

  ```bash
  $ proctracer --help

  Consumer commands
    install    Installs the requirements specified in a recipe (proctracerfile.py or proctracerfile.txt).
    ...

    proctracer commands. Type "proctracer <command> -h" for help
  ```

## License

[MIT LICENSE](LICENSE.md)
