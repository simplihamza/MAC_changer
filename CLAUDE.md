# MAC Changer

## What it does
Command-line script that changes a network interface's MAC address on Linux
using `ifconfig`, then re-reads the address to report whether the change
matched the requested value. The new MAC is either typed by the user (`-m`)
or generated at random (`-r`). Exits with a status code that reflects the
result.

## How to run
Linux only, needs root and `ifconfig` (`net-tools` package):

```bash
sudo python3 main.py -i <interface> -m <new_mac>
sudo python3 main.py -i <interface> -r
echo $?   # 0 success, 1 failure, 2 invalid or missing option
```

The script cannot run on this Windows dev machine; test it on a Linux system
or VM. The unit tests do run here, with no root, Linux or `ifconfig`:

```bash
python -m unittest -v
```

No third-party dependencies (standard library only). `.gitattributes`
forces LF line endings for `*.py` so the shebang works on Linux.

## Configuration
No environment variables or config files. All input comes from
command-line options:
- `-i` / `--interface`: interface to change (required)
- `-m` / `--mac`: new MAC address, validated with `is_valid_mac` and
  lowercased
- `-r` / `--random`: flag, use `generate_random_mac()` instead of `-m`

Exactly one of `-m` and `-r` must be given; `get_arguments` enforces this
itself because `optparse` cannot.

## Architecture
The script is `main.py`; its tests are `test_main.py`.

Module-level constants in `main.py`:
- `COMMAND_SUCCESS` (0): return code of a successful `subprocess.call`
- `EXIT_SUCCESS` (0) / `EXIT_FAILURE` (1): the script's own exit codes
- `MAC_PATTERN`: hex-only regex for 6 pairs joined by `:`; used with
  `re.search` on ifconfig output and `re.fullmatch` on user input
- `MAC_SEPARATOR` (`:`), `HEX_BASE` (16)
- `MULTICAST_BIT` (0x01) / `LOCALLY_ADMINISTERED_BIT` (0x02): bits of the
  first byte
- `MAC_BYTE_COUNT` (6), `MAX_BYTE_VALUE` (0xFF)

Functions:
- `get_current_mac_address(interface)`: runs `ifconfig <interface>` with
  `check_output`, decodes the bytes, and returns the first match of
  `MAC_PATTERN`, or `None`. Lets `CalledProcessError` (bad interface) and
  `FileNotFoundError` (no `ifconfig`) propagate.
- `is_valid_mac(mac)`: `True` if the whole string matches `MAC_PATTERN`
  and the first byte's multicast bit is 0. Does not check the locally
  administered bit.
- `generate_random_mac()`: 6 random bytes, first byte with the locally
  administered bit set and the multicast bit cleared; returns lowercase.
- `get_arguments()`: parses options with `optparse`. `parser.error` exits
  with status 2 if the interface is missing, both or neither of `-m`/`-r`
  are given, or `-m` is invalid. With `-r` it fills `new_mac` from
  `generate_random_mac()`. Always lowercases `new_mac`, since ifconfig
  prints lowercase; that is what makes the final comparison
  case-insensitive.
- `change_mac(interface, new_mac)`: runs `ifconfig` down, `hw ether`, up,
  checking each return code. Stops if `down` fails; otherwise always runs
  `up` so the interface is not left off. Returns `True` only if setting
  the address and `up` both succeeded. Prints nothing.
- `main()`: parses args, prints the current MAC, changes it, re-reads it,
  and compares with `new_mac`. Catches the two exceptions above and prints
  a friendly message. Returns `EXIT_SUCCESS` or `EXIT_FAILURE`.
- `if __name__ == "__main__": sys.exit(main())` is the only exit point, so
  importing `main` has no side effects.

## Tests
`test_main.py` uses `unittest` with three classes:
- `TestIsValidMac`: one test per rule (valid lower/upper/mixed case;
  invalid too short, wrong separator, non-hex, multicast).
- `TestGenerateRandomMac`: generates `RANDOM_SAMPLE_COUNT` MACs and checks
  each with `is_valid_mac` and for the locally administered bit, using
  `subTest`.
- `TestCommands`: class-level `@patch("main.subprocess")`, so the real
  ifconfig never runs. Covers `get_current_mac_address` and `change_mac`,
  including call order via `call_args_list`.

`main()` and `get_arguments()` have no unit tests. If `main()` is ever
tested, patch `main.subprocess.check_output` / `.call` individually:
patching the whole module turns `subprocess.CalledProcessError` in its
`except` clause into a mock, which raises `TypeError`.

## In progress
The comment block at the top of `main.py` holds the remaining numbered
TODO: TODO 25 (manual testing on Linux, then push). Finished TODOs are
deleted from that block.
