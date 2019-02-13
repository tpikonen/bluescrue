Bluescrue is a Python 3 module for receiving and decoding Bluetooth
low-energy (BLE) advertisement packets from
[Ruuvitags](https://ruuvi.com/).

It uses the [bluepy](https://github.com/IanHarvey/bluepy) library to
talk to the Bluetooth interface.

# Installation

These instructions are meant for a Debian-based Linux system.

This repository needs to be on your $PYTHONPATH, so that you can import
the `bluescrue` subdir as a module. Add it there via `.bashrc` or
similar.

## Bluepy

The bluepy library is an essential dependency of bluescrue. It is
probably easiest to install it via pip, like this:

```
pip3 install bluepy
```

## hcitool and hciconfig

At least my bluetooth adapter requires occasional resetting when it's
run continously. Bluescrue resets the adapter automatically, with the
`hcitool` and `hciconfig` commands from the Bluez package.

Bluez is easiest to install from your distributions repository:

```
sudo apt install bluez
```

## Permissions

You probably want to run your scanner code as a normal (non-root) user
and thus want to set the necessary capabilities to the programs which
interact with the bluetooth adapter.

The capabilities are 'cap_net_raw,cap_net_admin+eip' and the programs
are the bluepy helper binary `bluepy-helper`, `hcitool` and `hciconfig`.

Ensure that you have `setcap` installed:

```
sudo apt install libcap2-bin
```

Find the `bluepy-helper` binary in your bluepy installation. In a local
pip install it's in
`~/.local/lib/python3.7/site-packages/bluepy/bluepy-helper` or similar.

Run `setcap` on the bluetooth programs:

```
sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool`
sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hciconfig`
sudo setcap 'cap_net_raw,cap_net_admin+eip' <path to bluepy-helper>
```

And you are done.

# Usage

See `bluescrue/__main__.py` for a simple scanner which prints decoded
Ruuvitag BLE messages to stdout. The shell script `ruuviscan.sh` which
calls this code, is provided for convenience.

