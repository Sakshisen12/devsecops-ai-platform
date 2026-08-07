import os
import re
import subprocess


# Secret is now read from the environment instead of hardcoded in source.
# Set SECRET_API_KEY as a pipeline/library secret variable, never commit it.
SECRET_API_KEY = os.environ.get("SECRET_API_KEY", "")


def calculate_discount(price, discount_percent):
    """Calculates discounted price cleanly."""
    if price < 0 or discount_percent < 0:
        raise ValueError("Price and discount must be non-negative.")
    return price - (price * (discount_percent / 100))


def run_system_health_check(target_host):
    """Checks host health by pinging target_host once.

    target_host is validated against a strict hostname/IP pattern and passed
    to subprocess as an argument list (no shell=True), so it can't be used
    to inject arbitrary shell commands.
    """
    if not re.fullmatch(r"[A-Za-z0-9.\-]+", target_host):
        raise ValueError(f"Invalid host: {target_host!r}")

    result = subprocess.run(
        ["ping", "-c", "1", target_host],
        capture_output=True,
        timeout=5,
    )
    return result.returncode == 0


if __name__ == "__main__":
    print("Running App...")
    print(f"Discount Price: {calculate_discount(100, 20)}")
