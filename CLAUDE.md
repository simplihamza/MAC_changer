# MAC Changer

## What it does
Command-line script that changes a network interface's MAC address on Linux
using `ifconfig`, then re-reads the address to report whether the change
matched the requested value. Exits with a status code that reflects the
result.

## How to run
Linux only, needs root and `ifconfig` (`net-tools` package):

```bash
sudo python3 main.py -i <interface> -m <new_mac>
echo $?   # 0 success, 1 failure, 2 missing option
```

It cannot run on this Windows dev machine; test it on a Linux system or VM.
There are no tests yet and no third-party dependencies (standard library
only). `.gitattributes` forces LF line endings for `*.py` so the shebang
works on Linux.

## Configuration
No environment variables or config files. All input comes from the two
command-line options:
- `-i` / `--interface`: interface to change
- `-m` / `--mac`: new MAC address (not validated yet, passed straight to
  `ifconfig`)

## Architecture
Everything is in `main.py`.

Module-level constants:
- `COMMAND_SUCCESS` (0): return code of a successful `subprocess.call`
- `EXIT_SUCCESS` (0) / `EXIT_FAILURE` (1): the script's own exit codes
- `MAC_SEARCH_PATTERN`: hex-only regex for 6 pairs joined by `:`

Functions:
- `get_current_mac_address(interface)`: runs `ifconfig <interface>` with
  `check_output`, decodes the bytes, and returns the first match of
  `MAC_SEARCH_PATTERN`, or `None`. Lets `CalledProcessError` (bad
  interface) and `FileNotFoundError` (no `ifconfig`) propagate.
- `get_arguments()`: parses options with `optparse`; `parser.error` exits
  with status 2 if either option is missing.
- `change_mac(interface, new_mac)`: runs `ifconfig` down, `hw ether`, up,
  checking each return code. Stops if `down` fails; otherwise always runs
  `up` so the interface is not left off. Returns `True` only if setting
  the address and `up` both succeeded. Prints nothing.
- `main()`: parses args, prints the current MAC, changes it, re-reads it,
  and compares with the requested value (exact, case-sensitive string
  comparison). Catches the two exceptions above and prints a friendly
  message. Returns `EXIT_SUCCESS` or `EXIT_FAILURE`.
- `if __name__ == "__main__": sys.exit(main())` is the only exit point, so
  importing `main` has no side effects.

## In progress
The comment block at the top of `main.py` holds the remaining numbered
TODOs (10 to 25): MAC validation, case-insensitive comparison, unit tests
in `test_main.py`, a `--random` option, and doc updates. Finished TODOs are
deleted from that block.
