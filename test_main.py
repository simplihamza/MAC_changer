"""Unit tests for main.py.

Run from the project folder with:
    python -m unittest

Importing main is safe because its code only runs under the
if __name__ == "__main__" guard, so no ifconfig command runs here.
"""

import subprocess
import unittest
from unittest.mock import call, patch

import main

# Valid unicast MACs: the first pair is even in every one of them.
VALID_LOWERCASE_MAC = "00:1a:2b:3c:4d:5e"
VALID_UPPERCASE_MAC = "00:1A:2B:3C:4D:5E"
VALID_MIXED_CASE_MAC = "0a:1B:2c:3D:4e:5F"

# Invalid MACs: each one breaks a single rule of a valid MAC.
TOO_SHORT_MAC = "00:11:22:33:44"
WRONG_SEPARATOR_MAC = "00-11-22-33-44-55"
NON_HEX_MAC = "00:11:22:33:44:zz"
MULTICAST_MAC = "01:11:22:33:44:55"

# Fake ifconfig data for the command tests.
INTERFACE = "eth0"
CURRENT_MAC = "08:00:27:aa:bb:cc"
NEW_MAC = "00:11:22:33:44:55"
COMMAND_FAILED = 1

IFCONFIG_OUTPUT_WITH_MAC = (
    b"eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n"
    b"        inet 10.0.2.15  netmask 255.255.255.0  broadcast 10.0.2.255\n"
    b"        ether 08:00:27:aa:bb:cc  txqueuelen 1000  (Ethernet)\n"
)
IFCONFIG_OUTPUT_WITHOUT_MAC = (
    b"lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536\n"
    b"        inet 127.0.0.1  netmask 255.0.0.0\n"
    b"        loop  txqueuelen 1000  (Local Loopback)\n"
)

# The three commands change_mac should run, in order.
DOWN_CALL = call(["ifconfig", INTERFACE, "down"])
SET_MAC_CALL = call(["ifconfig", INTERFACE, "hw", "ether", NEW_MAC])
UP_CALL = call(["ifconfig", INTERFACE, "up"])

# How many random MACs to generate. Enough to hit every allowed first
# byte many times, while the test still runs in well under a second.
RANDOM_SAMPLE_COUNT = 1000


class TestIsValidMac(unittest.TestCase):
    """Tests for main.is_valid_mac."""

    def test_lowercase_is_valid(self):
        """A lowercase unicast MAC is accepted."""
        self.assertTrue(main.is_valid_mac(VALID_LOWERCASE_MAC))

    def test_uppercase_is_valid(self):
        """An uppercase unicast MAC is accepted."""
        self.assertTrue(main.is_valid_mac(VALID_UPPERCASE_MAC))

    def test_mixed_case_is_valid(self):
        """A mixed-case unicast MAC is accepted."""
        self.assertTrue(main.is_valid_mac(VALID_MIXED_CASE_MAC))

    def test_too_short_is_invalid(self):
        """A MAC with only 5 pairs is rejected."""
        self.assertFalse(main.is_valid_mac(TOO_SHORT_MAC))

    def test_wrong_separator_is_invalid(self):
        """A MAC separated by "-" instead of ":" is rejected."""
        self.assertFalse(main.is_valid_mac(WRONG_SEPARATOR_MAC))

    def test_non_hex_letters_are_invalid(self):
        """A MAC containing letters outside a-f is rejected."""
        self.assertFalse(main.is_valid_mac(NON_HEX_MAC))

    def test_multicast_first_byte_is_invalid(self):
        """A well-formed MAC with an odd (multicast) first byte is rejected."""
        self.assertFalse(main.is_valid_mac(MULTICAST_MAC))


class TestGenerateRandomMac(unittest.TestCase):
    """Tests for main.generate_random_mac.

    The output is random, so each test checks many samples. subTest
    reports the exact MAC that failed instead of stopping at the first.
    """

    def test_random_macs_are_valid(self):
        """Every generated MAC is accepted by is_valid_mac."""
        for _ in range(RANDOM_SAMPLE_COUNT):
            mac = main.generate_random_mac()
            with self.subTest(mac=mac):
                self.assertTrue(main.is_valid_mac(mac))

    def test_random_macs_are_locally_administered(self):
        """Every generated MAC has the locally administered bit set."""
        for _ in range(RANDOM_SAMPLE_COUNT):
            mac = main.generate_random_mac()
            first_byte = int(mac.split(main.MAC_SEPARATOR)[0], main.HEX_BASE)
            with self.subTest(mac=mac):
                self.assertTrue(first_byte & main.LOCALLY_ADMINISTERED_BIT)


@patch("main.subprocess")
class TestCommands(unittest.TestCase):
    """Tests for the functions that run ifconfig.

    main.subprocess is replaced by a mock in every test, so the real
    ifconfig never runs. The mock is passed in as mock_subprocess.
    """

    def test_get_mac_finds_mac_in_output(self, mock_subprocess):
        """The MAC in the ifconfig output is returned."""
        mock_subprocess.check_output.return_value = IFCONFIG_OUTPUT_WITH_MAC
        self.assertEqual(main.get_current_mac_address(INTERFACE), CURRENT_MAC)
        mock_subprocess.check_output.assert_called_once_with(["ifconfig", INTERFACE])

    def test_get_mac_returns_none_without_mac(self, mock_subprocess):
        """None is returned when the output contains no MAC."""
        mock_subprocess.check_output.return_value = IFCONFIG_OUTPUT_WITHOUT_MAC
        self.assertIsNone(main.get_current_mac_address(INTERFACE))

    def test_get_mac_raises_when_ifconfig_fails(self, mock_subprocess):
        """CalledProcessError from ifconfig is passed on to the caller."""
        mock_subprocess.check_output.side_effect = subprocess.CalledProcessError(
            COMMAND_FAILED, ["ifconfig", INTERFACE])
        with self.assertRaises(subprocess.CalledProcessError):
            main.get_current_mac_address(INTERFACE)

    def test_get_mac_raises_when_ifconfig_missing(self, mock_subprocess):
        """FileNotFoundError (no ifconfig installed) is passed on."""
        mock_subprocess.check_output.side_effect = FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            main.get_current_mac_address(INTERFACE)

    def test_change_mac_succeeds(self, mock_subprocess):
        """All three commands succeed, so change_mac returns True."""
        mock_subprocess.call.return_value = main.COMMAND_SUCCESS
        self.assertTrue(main.change_mac(INTERFACE, NEW_MAC))
        self.assertEqual(mock_subprocess.call.call_args_list,
                         [DOWN_CALL, SET_MAC_CALL, UP_CALL])

    def test_change_mac_stops_when_down_fails(self, mock_subprocess):
        """If "down" fails, nothing else runs and False is returned."""
        mock_subprocess.call.return_value = COMMAND_FAILED
        self.assertFalse(main.change_mac(INTERFACE, NEW_MAC))
        self.assertEqual(mock_subprocess.call.call_args_list, [DOWN_CALL])

    def test_change_mac_brings_interface_up_when_set_fails(self, mock_subprocess):
        """If "hw ether" fails, "up" still runs and False is returned."""
        mock_subprocess.call.side_effect = [main.COMMAND_SUCCESS, COMMAND_FAILED,
                                            main.COMMAND_SUCCESS]
        self.assertFalse(main.change_mac(INTERFACE, NEW_MAC))
        self.assertEqual(mock_subprocess.call.call_args_list,
                         [DOWN_CALL, SET_MAC_CALL, UP_CALL])

    def test_change_mac_fails_when_up_fails(self, mock_subprocess):
        """If "up" fails, change_mac returns False."""
        mock_subprocess.call.side_effect = [main.COMMAND_SUCCESS, main.COMMAND_SUCCESS,
                                            COMMAND_FAILED]
        self.assertFalse(main.change_mac(INTERFACE, NEW_MAC))


if __name__ == "__main__":
    unittest.main()
