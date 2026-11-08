#!/usr/bin/env python

import subprocess
import optparse
import re
import sys

# Return code that subprocess.call gives back when a command succeeds.
COMMAND_SUCCESS = 0

# Status codes this script exits with (checked on Linux with "echo $?").
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

# A MAC address: 6 hex pairs joined by ":". Used with re.search to find
# one inside ifconfig output, and with re.fullmatch to validate input.
MAC_PATTERN = r"[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}"
MAC_SEPARATOR = ":"
HEX_BASE = 16

# Lowest bit of the first byte: 1 means multicast, 0 means unicast.
MULTICAST_BIT = 0x01

# --- Part 4: --random option ---
#
# TODO 19: Write generate_random_mac() returning a string. Which two
#   bits of the first byte must be set, and to what ("locally
#   administered" and "unicast")? Generate a random first byte, then
#   set/clear those bits with bitwise operators. Name the masks as
#   constants.
#
# TODO 20: Add a -r/--random option in get_arguments, used instead of
#   -m, never together with it. optparse can't enforce that, so check
#   it yourself: what happens with both, or neither?
#
# TODO 21: Test it: call generate_random_mac many times in a loop and
#   assert is_valid_mac accepts every result.
#
# TODO 22: Commit "feat: add --random option".
#
# --- Part 5: Docs and push ---
#
# TODO 23: Update README.md: remove fixed Known Issues, add --random
#   and how to run the tests, add new lessons to What I Learned.
#
# TODO 24: Update CLAUDE.md (architecture, test command, new option).
#   Commit "docs: update README and CLAUDE.md".
#
# TODO 25: Test on a real Linux machine/VM: valid MAC, uppercase MAC,
#   --random, bad interface name, running without sudo. Then git push.
#
# =====================================================================

def get_current_mac_address(interface):
    """Return the current MAC address of a network interface.

    Args:
        interface: Name of the network interface, e.g. "eth0".

    Returns:
        The MAC address as a string like "08:00:27:aa:bb:cc", or None if no MAC address appears in the ifconfig output.

    Raises:
        subprocess.CalledProcessError: If ifconfig fails, e.g. because
            the interface does not exist.
        FileNotFoundError: If the ifconfig program is not installed.
    """
    ifconfig_output = subprocess.check_output(["ifconfig", interface]).decode()
    current_mac_search_result = re.search(MAC_PATTERN, ifconfig_output)
    if current_mac_search_result:
        return current_mac_search_result.group(0)
    else:
        return None

def is_valid_mac(mac):
    """Check whether a string is a usable unicast MAC address.

    Args:
        mac: The MAC address to check, e.g. "00:11:22:33:44:55".

    Returns:
        True if the whole string is 6 hex pairs joined by ":" and the
        first byte has its multicast bit cleared, otherwise False.
    """
    if not re.fullmatch(MAC_PATTERN, mac):
        return False
    first_byte = int(mac.split(MAC_SEPARATOR)[0], HEX_BASE)
    return (first_byte & MULTICAST_BIT) == 0

def get_arguments():
    """Parse the command-line options.

    Returns:
        The parsed options, with the attributes "interface" and
        "new_mac". "new_mac" is converted to lowercase, the same case
        ifconfig prints, so the final comparison ignores the case the
        user typed.

    Exits the program with an error message (status 2) if either
    option is missing or the MAC address is not a valid unicast
    address.
    """
    parser = optparse.OptionParser()
    parser.add_option("-i", "--interface", dest="interface", help="Interface to change MAC address")
    parser.add_option("-m", "--mac", dest="new_mac", help="New MAC address")
    (options, arguments) = parser.parse_args()
    if not options.interface:
        parser.error("[-] Please specify the interface to change MAC address, use --help for more info.")
    elif not options.new_mac:
        parser.error("[-] Please specify the new MAC address. use --help for more info.")
    elif not is_valid_mac(options.new_mac):
        parser.error(f"[-] Invalid MAC address '{options.new_mac}'. Use 6 hex pairs separated by ':' "
                     "(e.g. 00:11:22:33:44:55), and the first pair must be even (unicast).")
    options.new_mac = options.new_mac.lower()
    return options

def change_mac(interface, new_mac):
    """Change the MAC address of a network interface using ifconfig.

    Brings the interface down, sets the new hardware address, and brings
    it back up. If bringing the interface down fails, nothing else runs.
    Once it is down, "up" always runs, even if setting the address
    failed, so the interface is never left switched off.

    Args:
        interface: Name of the network interface, e.g. "eth0".
        new_mac: The MAC address to set, e.g. "00:11:22:33:44:55".

    Returns:
        True if every ifconfig command succeeded, otherwise False.
    """
    if subprocess.call(["ifconfig", interface, "down"]) != COMMAND_SUCCESS:
        return False

    mac_set = subprocess.call(["ifconfig", interface, "hw", "ether", new_mac]) == COMMAND_SUCCESS
    interface_up = subprocess.call(["ifconfig", interface, "up"]) == COMMAND_SUCCESS
    return mac_set and interface_up

def main():
    """Run the tool: parse options, change the MAC, and verify the result.

    Prints the current MAC address, changes it to the requested one,
    then reads it again, and reports whether it matches the request.
    If ifconfig fails or is not installed, prints an error and stops.

    Returns:
        EXIT_SUCCESS if the MAC address now matches the request,
        otherwise EXIT_FAILURE.
    """
    options = get_arguments()
    try:
        current_mac = get_current_mac_address(options.interface)
        if current_mac is None:
            print("[-] Could not read MAC address.")
            return EXIT_FAILURE
        print(f"[+] Current MAC address: {current_mac}")
        print(f"[+] Changing MAC address for {options.interface} to {options.new_mac}")
        if not change_mac(options.interface, options.new_mac):
            print(f"[-] ifconfig could not change the MAC address of {options.interface}.")
            return EXIT_FAILURE
        current_mac = get_current_mac_address(options.interface)
    except subprocess.CalledProcessError:
        print(f"[-] ifconfig failed for interface {options.interface}. Check that the interface exists.")
        return EXIT_FAILURE
    except FileNotFoundError:
        print("[-] ifconfig not found. Install the net-tools package.")
        return EXIT_FAILURE

    if current_mac == options.new_mac:
        print(f"[+] MAC address successfully changed to the requested MAC address {current_mac}.")
        return EXIT_SUCCESS
    print("[-] MAC address did not change to the requested MAC address.")
    return EXIT_FAILURE

if __name__ == "__main__":
    sys.exit(main())