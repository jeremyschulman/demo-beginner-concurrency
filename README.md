# Demo Repository for PyCharm Webcast

This repository contains the code used for the 2022-Feb-22 PyCharm Webcast
_Beginner Concurrency with Python asyncio_.

The code in this repo is designed for use with Arista EOS network infrastructure.
You could adapt it for your own use for other networking devices - left as an exercise
for the User.

# Installation

You will need to git-clone and install the project files directly as the repo
is not deployed on PyPi.  The project uses `poetry`, so you will need to create
a Python3.8 virtualenv with poetry.  Once created, you can install the files:

```shell
poetry install
```

You should then have a script called `demo` available in your virtualenv.  You can
verify via:

```shell
demo --help

Usage: demo [OPTIONS] COMMAND [ARGS]...

  Beginner-Concurency Demo CLI

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  find-host  Find switch-port where host with mac-addresss
  versions   Run inventory OS versions demo
  xcvrs      Run inventory transceivers demo
```

# Before You Begin

Before you try out the demo features you will need to export two variables into
your enviornment for network device authentication:

   * `NETWORK_USERNAME` - the login username value
   * `NETWORK_PASSWORD` = the login password

You will also need to create a text-file called `inventory.text` that contains
the list of devices, one per line.  The demo must be run on a computer that has
IP reachability to those devices and DNS for devices in the file.


