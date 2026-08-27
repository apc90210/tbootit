import re
import json
import urllib.parse
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app import models

ALLOWED_AVITO_HOSTS = {
    "api.avito.ru",
    "autoload.avito.ru",
    "autoload-static.avito.ru"
}

class OfficialAvitoAutoloadSchemaProvider:
    """
    Optional adapter for official Avito Autoload Schema endpoints.
    Enabled strictly when API credentials (client_id + client_secret) are configured.
    """
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_base: Optional[str] = None
    ):
        self.client_id = client_id or settings.avito_client_id
        self.client_secret = client_secret or settings.avito_client_secret
        self.api_base = (api_base or settings.avito_api_base or "https://api.avito.ru").rstrip('/')
        self._token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        self._tree_cache: Dict[str, Any] = {}
        self._fields_cache: Dict[str, Any] = {}

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate via POST /token using client_credentials grant.
        """
        if not self.is_configured:
            raise ValueError("Official Avito API is not configured: missing client_id or client_secret")

        import urllib.request
        import time

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
        """
        Fetch official category tree from GET /autoload/v1/user-docs/tree.
        Supports 304 Not Modified.
        """
        if not self.is_configured:
            raise ValueError("Official Avito API is not configured")

        import urllib.request
        import urllib.error

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
        """
        Fetch fields schema for a category node from GET /autoload/v1/user-docs/node/{node_slug}/fields.
        Supports 304 Not Modified.
        """
        if not self.is_configured:
            raise ValueError("Official Avito API is not configured")

        import urllib.request
        import urllib.error

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
        """
        Parse raw content rules from an Avito API field payload without flattening.
        """
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
        """
        Fetch linked values from Avito CDN with host allowlist and size limit.
        """
        if not self.validate_linked_json_url(url):
            raise ValueError(f"Insecure or non-allowed Avito host for linked values: {url}")

        import urllib.request
        headers = {
            "Accept": "application/json"
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            # 5MB size limit protection
            raw_bytes = resp.read(5 * 1024 * 1024 + 1)
            if len(raw_bytes) > 5 * 1024 * 1024:
                raise ValueError("Response payload exceeded 5MB size limit")
            data = json.loads(raw_bytes.decode("utf-8"))
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("values") or [data]
            return []

    def sync_official_category_to_db(
        self,
        db: Session,
        node_slug: str,
        category_name: str,
        fields_payload: Dict[str, Any]
    ) -> models.AvitoCanonicalCategory:
        """
        Sync fetched official category fields into Canonical models in Core DB.
        """
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)

        internal_key = f"official_{node_slug.replace('-', '_')}"
        canonical_cat = db.query(models.AvitoCanonicalCategory).filter(
            (models.AvitoCanonicalCategory.official_slug == node_slug) |
            (models.AvitoCanonicalCategory.internal_key == internal_key)
        ).first()

        if not canonical_cat:
            canonical_cat = models.AvitoCanonicalCategory(
                internal_key=internal_key,
                display_name=category_name,
                official_slug=node_slug,
                official_source="autoload_api",
                capability_source="official_api",
                active=True,
                created_at=now
            )
            db.add(canonical_cat)
            db.flush()
        else:
            canonical_cat.official_slug = node_slug
            canonical_cat.official_source = "autoload_api"
            canonical_cat.capability_source = "official_api"
            canonical_cat.updated_at = now
            db.flush()

        fields_list = fields_payload.get("fields") or []
        for field_item in fields_list:
            tag = field_item.get("tag") or field_item.get("id") or "Unknown"
            label = field_item.get("label") or tag
            field_key = tag.lower().replace("-", "_")

            field = db.query(models.AvitoCanonicalField).filter(
                models.AvitoCanonicalField.category_id == canonical_cat.id,
                models.AvitoCanonicalField.internal_key == field_key
            ).first()

            if not field:
                field = models.AvitoCanonicalField(
                    category_id=canonical_cat.id,
                    internal_key=field_key,
                    display_name=label,
                    official_tag=tag,
                    official_source="autoload_api",
                    active=True,
                    created_at=now
                )
                db.add(field)
                db.flush()

            # Parse content rules
            parsed_rules = self.parse_content_rules(field_item)
            for r_data in parsed_rules:
                rule = models.AvitoCanonicalFieldRule(
                    field_id=field.id,
                    ordinal=r_data["ordinal"],
                    rule_source="official_api",
                    required=r_data["required"],
                    required_by_dependency=r_data["required_by_dependency"],
                    dependencies_json=json.dumps(r_data["dependencies"], ensure_ascii=False) if r_data["dependencies"] else None,
                    values_range_json=json.dumps(r_data["values_range"], ensure_ascii=False) if r_data["values_range"] else None,
                    raw_json=r_data["raw_json"],
                    created_at=now
                )
                db.add(rule)
                db.flush()

                # Add inline values
                for v in r_data["values"]:
                    val_str = str(v.get("value") if isinstance(v, dict) else v).strip()
                    desc_str = str(v.get("description") if isinstance(v, dict) else "") or None
                    if val_str:
                        db.add(models.AvitoCanonicalFieldValue(
                            field_id=field.id,
                            rule_id=rule.id,
                            value=val_str,
                            description=desc_str,
                            official_value=val_str,
                            source="inline",
                            active=True,
                            created_at=now
                        ))

        db.flush()
        return canonical_cat
