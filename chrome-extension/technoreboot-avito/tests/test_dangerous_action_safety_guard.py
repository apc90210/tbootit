import os
import pytest

def test_dangerous_action_keywords_presence():
    """Verify DANGEROUS_ACTION_KEYWORDS is defined with all prohibited button/action terms."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    assert os.path.exists(content_js_path)

    with open(content_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DANGEROUS_ACTION_KEYWORDS" in content
    assert "isDangerousControl" in content

    for kw in ["разместить", "опубликовать", "подать объявление", "отправить", "подтвердить", "оплатить", "купить", "продолжить", "далее", "готово"]:
        assert kw in content

def test_no_programmatic_form_submit():
    """Verify content.js and popup.js NEVER call submit() or requestSubmit()."""
    for file_rel in ["chrome-extension/technoreboot-avito/content.js", "chrome-extension/technoreboot-avito/popup.js"]:
        path = os.path.abspath(file_rel)
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()

        assert ".submit()" not in code
        assert ".requestSubmit()" not in code

def test_file_inputs_protected():
    """Verify content.js specifically ignores input[type=file] elements."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    with open(content_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "el.type === 'file'" in content or 'el.type === "file"' in content
