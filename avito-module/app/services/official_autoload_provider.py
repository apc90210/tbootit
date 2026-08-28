import json
import urllib.parse
import urllib.request
import urllib.error
import time
from typing import Optional, Dict, Any, List, Tuple
from app.config import settings

ALLOWED_AVITO_HOSTS = {
    "api.avito.ru",
    "autoload.avito.ru",
    "autoload-static.avito.ru"
}

class OfficialAvitoAutoloadSchemaProvider:
    """
    Official Avito Autoload Schema Provider.
    Owned strictly by avito-module (never Core).
    Handles external Avito OAuth, category tree, and fields discovery.
    """
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_base: Optional[str] = None
    ):
        self.client_id = client_id or settings.AVITO_CLIENT_ID
        self.client_secret = client_secret or settings.AVITO_CLIENT_SECRET
        self.api_base = (api_base or settings.AVITO_API_BASE or "https://api.avito.ru").rstrip('/')
        self._token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def authenticate(self) -> Dict[str, Any]:
        """Authenticate via POST /token using client_credentials grant."""
        if not self.is_configured:
            raise ValueError("Official Avito API is not configured: missing client_id or client_secret")

        url = f"{self.api_base}/token"
        data = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            self._token = body.get("access_token")
            expires_in = body.get("expires_in", 3600)
            self._token_expires_at = time.time() + float(expires_in) - 60
            return {
                "authenticated": True,
                "expires_in": expires_in
            }

    def fetch_tree(self, if_modified_since: Optional[str] = None) -> Tuple[int, Dict[str, Any], Optional[str]]:
        """Fetch official category tree from GET /autoload/v1/user-docs/tree."""
        if not self.is_configured:
            raise ValueError("Official Avito API is not configured")

        headers = {
            "Authorization": f"Bearer {self._token}" if self._token else "",
            "Accept": "application/json"
        }
        if if_modified_since:
            headers["If-Modified-Since"] = if_modified_since

        url = f"{self.api_base}/autoload/v1/user-docs/tree"
        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                last_modified = resp.headers.get("Last-Modified")
                data = json.loads(resp.read().decode("utf-8"))
                return status, data, last_modified
        except urllib.error.HTTPError as e:
            if e.code == 304:
                return 304, {}, None
            raise

    def fetch_node_fields(self, node_slug: str, if_modified_since: Optional[str] = None) -> Tuple[int, Dict[str, Any], Optional[str]]:
        """Fetch fields schema for a category node from GET /autoload/v1/user-docs/node/{node_slug}/fields."""
        if not self.is_configured:
            raise ValueError("Official Avito API is not configured")

        headers = {
            "Authorization": f"Bearer {self._token}" if self._token else "",
            "Accept": "application/json"
        }
        if if_modified_since:
            headers["If-Modified-Since"] = if_modified_since

        url = f"{self.api_base}/autoload/v1/user-docs/node/{node_slug}/fields"
        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                last_modified = resp.headers.get("Last-Modified")
                data = json.loads(resp.read().decode("utf-8"))
                return status, data, last_modified
        except urllib.error.HTTPError as e:
            if e.code == 304:
                return 304, {}, None
            raise

    @staticmethod
    def parse_content_rules(field_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse raw content rules from field payload without destructive flattening."""
        rules = []
        contents = field_data.get("content") or []
        if isinstance(contents, dict):
            contents = [contents]

        for idx, item in enumerate(contents):
            if not isinstance(item, dict):
                continue
            rule = {
                "ordinal": idx,
                "rule_source": "official_api",
                "field_type": item.get("type") or item.get("field_type") or "input",
                "data_type": item.get("data_type") or "string",
                "required": bool(item.get("required")),
                "required_by_dependency": bool(item.get("required_by_dependency")),
                "default": item.get("default"),
                "dependencies": item.get("dependencies") or item.get("dependencies_text"),
                "values": item.get("values") or [],
                "values_link_json": item.get("values_link_json"),
                "values_range": item.get("values_range"),
                "raw_json": json.dumps(item, ensure_ascii=False)
            }
            rules.append(rule)
        return rules

    @staticmethod
    def validate_linked_json_url(url: str) -> bool:
        """Validate linked JSON url host and protocol for security."""
        if not url or not url.startswith("https://"):
            return False
        parsed = urllib.parse.urlparse(url)
        return parsed.hostname in ALLOWED_AVITO_HOSTS

    def fetch_linked_json_values(self, url: str) -> List[Dict[str, Any]]:
        """Fetch linked values from Avito CDN with host allowlist and size limit."""
        if not self.validate_linked_json_url(url):
            raise ValueError(f"Insecure or non-allowed Avito host for linked values: {url}")

        headers = {
            "Accept": "application/json"
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw_bytes = resp.read(5 * 1024 * 1024 + 1)
            if len(raw_bytes) > 5 * 1024 * 1024:
                raise ValueError("Response payload exceeded 5MB size limit")
            data = json.loads(raw_bytes.decode("utf-8"))
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("values") or [data]
            return []

    def build_normalized_schema_payload(
        self,
        node_slug: str,
        category_name: str,
        fields_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert official Avito fields payload into normalized schema payload for Core ingestion.
        Contains ZERO credentials, tokens, or secrets.
        """
        normalized_fields = []
        raw_fields = fields_payload.get("fields") or []

        for f_item in raw_fields:
            tag = f_item.get("tag") or f_item.get("id") or "Unknown"
            label = f_item.get("label") or tag
            rules = self.parse_content_rules(f_item)

            normalized_fields.append({
                "official_tag": tag,
                "display_name": label,
                "internal_key": tag.lower().replace("-", "_"),
                "rules": rules
            })

        return {
            "official_slug": node_slug,
            "category_name": category_name,
            "fields": normalized_fields
        }

    def sync_schema_to_core(
        self,
        core_base_url: str,
        node_slug: str,
        category_name: str,
        fields_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transmit normalized schema payload to Core internal HTTP endpoint.
        """
        payload = self.build_normalized_schema_payload(node_slug, category_name, fields_payload)
        url = f"{core_base_url.rstrip('/')}/api/integrations/avito/autoload-schema/import"
        body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
