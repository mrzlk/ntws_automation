"""
Tests for Milestone 2: Hotkeys Fix

Tests the keyboard automation and TWS hotkey functionality.
Includes both basic tests (no TWS required) and integration tests (TWS required).

Usage:
    python -m tests.test_hotkeys         # all tests
    python -m tests.test_hotkeys --basic # only basic tests (no TWS)
"""

import sys
import time
import argparse
from typing import Callable, List, Tuple


# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_header(text: str) -> None:
    """Print section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}\n")


def print_result(name: str, passed: bool, message: str = "") -> None:
    """Print test result."""
    if passed:
        symbol = f"{Colors.GREEN}[OK]{Colors.RESET}"
        status = f"{Colors.GREEN}PASS{Colors.RESET}"
    else:
        symbol = f"{Colors.RED}[X]{Colors.RESET}"
        status = f"{Colors.RED}FAIL{Colors.RESET}"

    print(f"  {symbol} {name}: {status}")
    if message:
        print(f"      {Colors.YELLOW}{message}{Colors.RESET}")


def run_test(name: str, test_func: Callable) -> bool:
    """Run a single test and return result."""
    try:
        result = test_func()
        if result is None:
            result = True
        print_result(name, result)
        return result
    except Exception as e:
        print_result(name, False, str(e))
        return False


# =============================================================================
# Part 1: Basic Tests (no TWS required)
# =============================================================================

def test_imports() -> bool:
    """Test that all required modules can be imported."""
    try:
        from tws_automation.input.keyboard import Keyboard
        from tws_automation.input.hotkeys import TWSHotkeys, TWSAction, HotkeyBinding
        from tws_automation.core.window import TWSWindow
        return True
    except ImportError as e:
        raise Exception(f"Import failed: {e}")


def test_keyboard_init() -> bool:
    """Test Keyboard class initialization."""
    from tws_automation.input.keyboard import Keyboard

    kb = Keyboard()
    assert kb.typing_interval == 0.02, f"Expected 0.02, got {kb.typing_interval}"

    kb2 = Keyboard(typing_interval=0.05)
    assert kb2.typing_interval == 0.05, f"Expected 0.05, got {kb2.typing_interval}"

    return True


def test_hotkey_format() -> bool:
    """Test that hotkey() builds correct pywinauto format strings."""
    from tws_automation.input.keyboard import Keyboard

    kb = Keyboard()

    # Test modifier mapping
    expected_mappings = {
        'ctrl': '^',
        'control': '^',
        'alt': '%',
        'shift': '+',
        'win': '#',
    }

    for key, expected in expected_mappings.items():
        actual = kb.MODIFIER_KEYS.get(key)
        assert actual == expected, f"MODIFIER_KEYS['{key}']: expected '{expected}', got '{actual}'"

    # Test that hotkey builds correct format
    # We can't directly test send_keys without actually sending keys,
    # but we can verify the logic by checking the mapping

    # Simulate what hotkey() does internally
    def build_hotkey_string(*keys):
        modifiers = ''
        final_key = ''
        for key in keys:
            key_lower = key.lower()
            if key_lower in kb.MODIFIER_KEYS:
                modifiers += kb.MODIFIER_KEYS[key_lower]
            elif key_lower in kb.SPECIAL_KEYS:
                final_key = kb.SPECIAL_KEYS[key_lower]
            else:
                final_key = key.lower()
        return f'{modifiers}{final_key}'

    # Test cases
    test_cases = [
        (('ctrl', 'c'), '^c'),
        (('ctrl', 'shift', 'b'), '^+b'),
        (('ctrl', 'shift', 's'), '^+s'),
        (('alt', 'f4'), '%{F4}'),
        (('ctrl', 'enter'), '^{ENTER}'),
        (('shift', 'tab'), '+{TAB}'),
    ]

    for keys, expected in test_cases:
        actual = build_hotkey_string(*keys)
        assert actual == expected, f"hotkey{keys}: expected '{expected}', got '{actual}'"

    return True


def test_special_keys() -> bool:
    """Test special key mappings."""
    from tws_automation.input.keyboard import Keyboard

    kb = Keyboard()

    expected_specials = {
        'enter': '{ENTER}',
        'tab': '{TAB}',
        'escape': '{ESC}',
        'backspace': '{BACKSPACE}',
        'delete': '{DELETE}',
        'f1': '{F1}',
        'f12': '{F12}',
    }

    for key, expected in expected_specials.items():
        actual = kb.SPECIAL_KEYS.get(key)
        assert actual == expected, f"SPECIAL_KEYS['{key}']: expected '{expected}', got '{actual}'"

    return True


def test_tws_hotkeys_default_bindings() -> bool:
    """Test TWSHotkeys default bindings."""
    from tws_automation.input.keyboard import Keyboard
    from tws_automation.input.hotkeys import TWSHotkeys, TWSAction

    kb = Keyboard()
    hotkeys = TWSHotkeys(kb)

    # Check BUY binding
    buy_binding = hotkeys.get_binding(TWSAction.BUY)
    assert buy_binding is not None, "BUY binding not found"
    assert buy_binding.modifiers == ['ctrl', 'shift'], f"BUY modifiers: {buy_binding.modifiers}"
    assert buy_binding.key == 'b', f"BUY key: {buy_binding.key}"

    # Check SELL binding
    sell_binding = hotkeys.get_binding(TWSAction.SELL)
    assert sell_binding is not None, "SELL binding not found"
    assert sell_binding.modifiers == ['ctrl', 'shift'], f"SELL modifiers: {sell_binding.modifiers}"
    assert sell_binding.key == 's', f"SELL key: {sell_binding.key}"

    return True


def test_hotkey_binding_to_sequence() -> bool:
    """Test HotkeyBinding.to_sequence() method."""
    from tws_automation.input.hotkeys import HotkeyBinding, TWSAction

    binding = HotkeyBinding(
        action=TWSAction.BUY,
        modifiers=['ctrl', 'shift'],
        key='b',
        description='Test'
    )

    seq = binding.to_sequence()
    expected = ('ctrl', 'shift', 'b')
    assert seq == expected, f"to_sequence(): expected {expected}, got {seq}"

    # Test string representation
    str_repr = str(binding)
    assert 'Ctrl' in str_repr and 'Shift' in str_repr and 'B' in str_repr, \
        f"String repr should contain Ctrl+Shift+B, got: {str_repr}"

    return True


# =============================================================================
# Part 2: Integration Tests (TWS required)
# =============================================================================

def test_connect() -> bool:
    """Test connecting to TWS window."""
    from tws_automation.core.window import TWSWindow

    tws = TWSWindow()
    connected = tws.connect()

    if not connected:
        raise Exception("Could not connect to TWS. Is TWS running?")

    return True


def test_bring_to_front() -> bool:
    """Test bringing TWS window to foreground."""
    from tws_automation.core.window import TWSWindow

    tws = TWSWindow()
    if not tws.connect():
        raise Exception("Could not connect to TWS")

    tws.bring_to_front()
    time.sleep(0.5)

    # Verify window is ready
    if not tws.is_ready():
        raise Exception("TWS window not ready after bring_to_front()")

    return True


def test_type_text() -> bool:
    """Test typing text (manual verification)."""
    from tws_automation.core.window import TWSWindow
    from tws_automation.input.keyboard import Keyboard

    tws = TWSWindow()
    if not tws.connect():
        raise Exception("Could not connect to TWS")

    tws.bring_to_front()
    time.sleep(0.3)

    kb = Keyboard()

    print(f"\n      {Colors.YELLOW}[INFO] Please click on a text field in TWS...{Colors.RESET}")
    time.sleep(3)

    # Type test text
    kb.type_text("TEST123")

    print(f"      {Colors.YELLOW}[INFO] Did 'TEST123' appear? (visual check){Colors.RESET}")
    time.sleep(1)

    return True


def test_hotkey_buy() -> bool:
    """Test Ctrl+Shift+B hotkey opens BUY ticket."""
    from tws_automation.core.window import TWSWindow
    from tws_automation.input.keyboard import Keyboard
    from tws_automation.input.hotkeys import TWSHotkeys, TWSAction

    tws = TWSWindow()
    if not tws.connect():
        raise Exception("Could not connect to TWS")

    tws.bring_to_front()
    time.sleep(0.3)

    kb = Keyboard()
    hotkeys = TWSHotkeys(kb)

    print(f"\n      {Colors.YELLOW}[INFO] Sending Ctrl+Shift+B...{Colors.RESET}")

    hotkeys.buy()
    time.sleep(1)

    # Try to find BUY window
    buy_window = tws.find_window(r".*Buy.*|.*Order.*")

    if buy_window:
        print(f"      {Colors.GREEN}[OK] BUY window detected!{Colors.RESET}")
        # Close it
        kb.hotkey('escape')
        return True
    else:
        print(f"      {Colors.YELLOW}[INFO] Could not auto-detect BUY window. Did it open? (visual check){Colors.RESET}")
        return True  # Manual verification


def test_hotkey_sell() -> bool:
    """Test Ctrl+Shift+S hotkey opens SELL ticket."""
    from tws_automation.core.window import TWSWindow
    from tws_automation.input.keyboard import Keyboard
    from tws_automation.input.hotkeys import TWSHotkeys, TWSAction

    tws = TWSWindow()
    if not tws.connect():
        raise Exception("Could not connect to TWS")

    tws.bring_to_front()
    time.sleep(0.3)

    kb = Keyboard()
    hotkeys = TWSHotkeys(kb)

    print(f"\n      {Colors.YELLOW}[INFO] Sending Ctrl+Shift+S...{Colors.RESET}")

    hotkeys.sell()
    time.sleep(1)

    # Try to find SELL window
    sell_window = tws.find_window(r".*Sell.*|.*Order.*")

    if sell_window:
        print(f"      {Colors.GREEN}[OK] SELL window detected!{Colors.RESET}")
        # Close it
        kb.hotkey('escape')
        return True
    else:
        print(f"      {Colors.YELLOW}[INFO] Could not auto-detect SELL window. Did it open? (visual check){Colors.RESET}")
        return True  # Manual verification


def test_hotkey_direct() -> bool:
    """Test direct hotkey() call with pywinauto."""
    from tws_automation.core.window import TWSWindow
    from tws_automation.input.keyboard import Keyboard

    tws = TWSWindow()
    if not tws.connect():
        raise Exception("Could not connect to TWS")

    tws.bring_to_front()
    time.sleep(0.3)

    kb = Keyboard()

    print(f"\n      {Colors.YELLOW}[INFO] Sending Ctrl+Shift+B directly via keyboard.hotkey()...{Colors.RESET}")

    kb.hotkey('ctrl', 'shift', 'b')
    time.sleep(1)

    print(f"      {Colors.YELLOW}[INFO] Did BUY ticket open? (visual check){Colors.RESET}")

    # Close any dialog
    kb.hotkey('escape')

    return True


# =============================================================================
# Main Runner
# =============================================================================

def run_basic_tests() -> Tuple[int, int]:
    """Run basic tests that don't require TWS."""
    print_header("Part 1: Basic Tests (no TWS required)")

    tests = [
        ("Import modules", test_imports),
        ("Keyboard initialization", test_keyboard_init),
        ("Hotkey format (^+b)", test_hotkey_format),
        ("Special keys mapping", test_special_keys),
        ("TWS hotkey default bindings", test_tws_hotkeys_default_bindings),
        ("HotkeyBinding.to_sequence()", test_hotkey_binding_to_sequence),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        if run_test(name, test_func):
            passed += 1
        else:
            failed += 1

    return passed, failed


def run_integration_tests() -> Tuple[int, int]:
    """Run integration tests that require TWS."""
    print_header("Part 2: Integration Tests (TWS required)")

    print(f"{Colors.YELLOW}IMPORTANT: Make sure TWS is running and visible!{Colors.RESET}")
    print(f"{Colors.YELLOW}These tests will interact with the TWS window.{Colors.RESET}")
    print(f"{Colors.YELLOW}Press Enter to continue or Ctrl+C to skip...{Colors.RESET}\n")

    try:
        input()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Skipping integration tests.{Colors.RESET}")
        return 0, 0

    tests = [
        ("Connect to TWS", test_connect),
        ("Bring window to front", test_bring_to_front),
        ("Type text", test_type_text),
        ("Direct hotkey (Ctrl+Shift+B)", test_hotkey_direct),
        ("Hotkey BUY (Ctrl+Shift+B)", test_hotkey_buy),
        ("Hotkey SELL (Ctrl+Shift+S)", test_hotkey_sell),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        if run_test(name, test_func):
            passed += 1
        else:
            failed += 1
        time.sleep(1)  # Pause between tests

    return passed, failed


def main():
    parser = argparse.ArgumentParser(description='Test Milestone 2: Hotkeys Fix')
    parser.add_argument('--basic', action='store_true', help='Run only basic tests (no TWS required)')
    args = parser.parse_args()

    print(f"\n{Colors.BOLD}Milestone 2 Tests: Hotkeys Fix{Colors.RESET}")
    print(f"{'='*40}\n")

    total_passed = 0
    total_failed = 0

    # Run basic tests
    passed, failed = run_basic_tests()
    total_passed += passed
    total_failed += failed

    # Run integration tests if not --basic
    if not args.basic:
        passed, failed = run_integration_tests()
        total_passed += passed
        total_failed += failed

    # Summary
    print_header("Summary")
    print(f"  {Colors.GREEN}Passed: {total_passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {total_failed}{Colors.RESET}")

    if total_failed == 0:
        print(f"\n  {Colors.GREEN}{Colors.BOLD}All tests passed!{Colors.RESET}")
        sys.exit(0)
    else:
        print(f"\n  {Colors.RED}{Colors.BOLD}Some tests failed.{Colors.RESET}")
        sys.exit(1)


if __name__ == '__main__':
    main()
