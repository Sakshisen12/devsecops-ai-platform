import os

# 🚨 SECURITY FLAW #1: Hardcoded sensitive secret key
# Bandit scanner will flag this as a hardcoded credential risk.
SECRET_API_KEY = "sk_live_998877665544332211_PRODUCTION_KEY"


def calculate_discount(price, discount_percent):
    """Calculates discounted price cleanly."""
    if price < 0 or discount_percent < 0:
        raise ValueError("Price and discount must be non-negative.")
    return price - (price * (discount_percent / 100))


def run_system_health_check(target_host):
    """Checks host health."""
    # 🚨 SECURITY FLAW #2: Command Injection Risk
    # Bandit will flag 'os.system' or shell execution with unformatted inputs
    cmd = f"ping -c 1 {target_host}"
    status = os.system(cmd)
    return status == 0


if __name__ == "__main__":
    print("Running App...")
    print(f"Discount Price: {calculate_discount(100, 20)}")
