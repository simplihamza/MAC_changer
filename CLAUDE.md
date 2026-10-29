# MAC Changer

## What it does
Command-line script that changes a network interface's MAC address on Linux
using `ifconfig`, then re-reads the address to report whether the change
matched the requested value.

## How to run
Linux only, needs root and `ifconfig` (`net-tools` package):

```bash
sudo python3 main.py -i <interface> -m <new_mac>
```

It cannot run on this Windows dev machine; test it on a Linux system or VM.
There are no tests and no third-party dependencies (standard library only).

## Configuration
No environment variables or config files. All input comes from the two
command-line options:
- `-i` / `--interface`: interface to change
- `-m` / `--mac`: new MAC address

## Architecture
Everything is in `main.py`:
- `get_arguments()`: parses options with `optparse`, exits via
  `parser.error` if either is missing
- `get_current_mac_address(interface)`: runs `ifconfig <interface>` and
  regex-matches the first `xx:xx:xx:xx:xx:xx`; returns `None` if none found
- `change_mac(interface, new_mac)`: runs `ifconfig` down, `hw ether`, up
- Module-level code (no `if __name__ == "__main__"` guard) calls these in
  order: parse args, print current MAC, wait 2 seconds, change MAC, re-read
  it, compare with the requested value
