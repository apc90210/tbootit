import json
import pytest

# Simulator of service_worker.js parseJsonResponseSafely for Python unit testing

class DummyHeaders:
    def __init__(self, headers_dict):
        self._headers = {k.lower(): v for k, v in headers_dict.items()}
    def get(self, key, default=""):
        return self._headers.get(key.lower(), default)

class DummyResponse:
    def __init__(self, status, text, headers=None):
        self.status = status
        self.ok = 200 <= status < 300
        self._text = text
        self.headers = DummyHeaders(headers or {})

    async def text(self):
        return self._text


def parse_json_response_safely_py(status, text, content_type=""):
    res_ok = 200 <= status < 300
    data = None
    if text and ("application/json" in content_type or text.strip().startswith("{") or text.strip().startswith("[")):
        try:
            data = json.loads(text)
        except Exception:
            data = None

    if res_ok:
        if data is not None:
            return {"ok": True, "status": status, "data": data}
        else:
            return {"ok": False, "status": status, "error": "Некорректный (не-JSON) ответ сервера при успешном HTTP статусе.", "text": text}
    else:
        if data is not None:
            err_msg = None
            if isinstance(data.get("detail"), str):
                err_msg = data["detail"]
            elif isinstance(data.get("detail"), dict):
                err_msg = data["detail"].get("message") or data["detail"].get("error") or json.dumps(data["detail"])
            elif data.get("message"):
                err_msg = data["message"]
            elif data.get("error"):
                err_msg = data["error"]

            if err_msg:
                return {"ok": False, "status": status, "error": f"Ошибка сервера {status}: {err_msg}", "data": data}

        safe_text = text[:150].strip() if text else "Internal Server Error"
        return {"ok": False, "status": status, "error": f"Ошибка сервера {status}: {safe_text}"}


def test_500_plain_text_never_throws_unexpected_token():
    status = 500
    text = "Internal Server Error"
    content_type = "text/plain"

    result = parse_json_response_safely_py(status, text, content_type)
    assert result["ok"] is False
    assert result["status"] == 500
    assert "Ошибка сервера 500: Internal Server Error" in result["error"]
    assert "Unexpected token" not in result["error"]


def test_500_json_detail_formatting():
    status = 500
    text = json.dumps({"detail": "Database connection lost"})
    content_type = "application/json"

    result = parse_json_response_safely_py(status, text, content_type)
    assert result["ok"] is False
    assert result["status"] == 500
    assert "Ошибка сервера 500: Database connection lost" in result["error"]


def test_504_gateway_timeout():
    status = 504
    text = json.dumps({"detail": "Превышено время ожидания ответа от модуля Avito (60с)"})
    content_type = "application/json"

    result = parse_json_response_safely_py(status, text, content_type)
    assert result["ok"] is False
    assert result["status"] == 504
    assert "Превышено время ожидания" in result["error"]


def test_502_html_error_page():
    status = 502
    text = "<html><body><h1>502 Bad Gateway</h1></body></html>"
    content_type = "text/html"

    result = parse_json_response_safely_py(status, text, content_type)
    assert result["ok"] is False
    assert result["status"] == 502
    assert "Ошибка сервера 502" in result["error"]
    assert "Unexpected token" not in result["error"]


def test_200_invalid_json():
    status = 200
    text = "OK but not json"
    content_type = "text/plain"

    result = parse_json_response_safely_py(status, text, content_type)
    assert result["ok"] is False
    assert result["status"] == 200
    assert "Некорректный (не-JSON) ответ сервера" in result["error"]


def test_200_valid_json_success():
    status = 200
    text = json.dumps({"status": "success", "product_id": 58, "photos_imported": 8})
    content_type = "application/json"

    result = parse_json_response_safely_py(status, text, content_type)
    assert result["ok"] is True
    assert result["data"]["product_id"] == 58
    assert result["data"]["photos_imported"] == 8
