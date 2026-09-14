from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = REPO_ROOT / "admin-shell" / "app" / "templates"

MANUAL_LINK = '<a href="/help/user-manual.pdf" class="nav-item" data-path="manual" style="color: #cbd5e1; text-decoration: none; padding: 6px 11px; border-radius: 4px; font-weight: 500; transition: all 0.15s ease;">📘 Инструкция</a>'

MANUAL_JS = """            } else if (href === '/help/user-manual.pdf' && (p.indexOf('/help') === 0)) {
                isActive = true;"""

def update_templates():
    updated = []
    for f in TEMPLATES_DIR.glob("*.html"):
        content = f.read_text(encoding="utf-8")
        if 'class="main-nav"' not in content:
            continue
        
        orig = content
        
        # Add link after settings if not already present
        if '/help/user-manual.pdf' not in content:
            if '<a href="/inventory/settings/organization"' in content:
                target_str = '<a href="/inventory/settings/organization" class="nav-item" data-path="settings" style="color: #cbd5e1; text-decoration: none; padding: 6px 11px; border-radius: 4px; font-weight: 500; transition: all 0.15s ease;">Настройки</a>'
                if target_str in content:
                    content = content.replace(target_str, f"{target_str}\n        {MANUAL_LINK}")
                else:
                    # Generic regex replace
                    import re
                    content = re.sub(
                        r'(<a href="/inventory/settings/organization"[^>]*>.*?</a>)',
                        rf'\1\n        {MANUAL_LINK}',
                        content
                    )
            elif '<a href="/repairs/repairs"' in content and 'operations.html' in f.name:
                import re
                content = re.sub(
                    r'(<a href="/certificates"[^>]*>.*?</a>)',
                    rf'\1\n            {MANUAL_LINK}',
                    content
                )

        # Add active check in JS if not already present
        if "href === '/help/user-manual.pdf'" not in content:
            if "} else if (href === '/certificates'" in content:
                content = content.replace(
                    "} else if (href === '/certificates'",
                    f"{MANUAL_JS}\n            }} else if (href === '/certificates'"
                )
            elif "} else if (href === '/backups'" in content:
                content = content.replace(
                    "} else if (href === '/backups'",
                    f"{MANUAL_JS}\n            }} else if (href === '/backups'"
                )

        if content != orig:
            f.write_text(content, encoding="utf-8")
            updated.append(f.name)

    print("Updated templates:", updated)

if __name__ == "__main__":
    update_templates()
