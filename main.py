#!/usr/bin/env python

import subprocess
import optparse
import re
from time import sleep


def get_current_mac_address(interface):
    ifconfig_output = str(subprocess.check_output(["ifconfig", interface]))
    current_mac_search_result = re.search(r"\w\w:\w\w:\w\w:\w\w:\w\w:\w\w", ifconfig_output)
    if current_mac_search_result:
        return current_mac_search_result.group(0)
    else:
        print("[-] No MAC address found.")

def get_arguments():
    parser = optparse.OptionParser()
    parser.add_option("-i", "--interface", dest="interface", help="Interface to change MAC address")
    parser.add_option("-m", "--mac", dest="new_mac", help="New MAC address")
    (options, arguments) = parser.parse_args()
    if not options.interface:
        parser.error("[-] Please specify the interface to change MAC address, use --help for more info.")
    elif not options.new_mac:
        parser.error("[-] Please specify the new MAC address. use --help for more info.")
    return options

def change_mac(interface, new_mac):
    print(f"[+] Changing MAC address for {interface} to {new_mac}")
    subprocess.call(["ifconfig", interface,"down"])
    subprocess.call(["ifconfig", interface,"hw", "ether", new_mac])
    subprocess.call(["ifconfig", interface,"up"])

options = get_arguments()
current_mac = get_current_mac_address(options.interface)
print(f"[+] Current MAC address: {current_mac}")
sleep(2)
change_mac(options.interface, options.new_mac)
current_mac = get_current_mac_address(options.interface)

if current_mac == options.new_mac:
    print(f"[+] MAC address successfully changed to the requested MAC address {current_mac}.")
else:
    print("[-] MAC address did not change to the requested MAC address.")