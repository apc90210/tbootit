import os
import re
import pytest

FORBIDDEN_PATTERNS = [
    r"stealth",
    r"fingerprint_spoof",
    r"navigator\.webdriver\s*=",
    r"proxy_rotation",
    r"captcha_solver",
    r"bypass_captcha",
    r"sms_bypass",
]

def test_no_anti_bot_evasion_code_in_avito_module():
    app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
    pattern = re.compile("|".join(FORBIDDEN_PATTERNS), re.IGNORECASE)
    
    violations = []
    for root, _, files in os.walk(app_dir):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                    matches = pattern.findall(content)
                    if matches:
                        violations.append((f, matches))
                        
    assert len(violations) == 0, f"Found forbidden anti-bot evasion patterns in source code: {violations}"
