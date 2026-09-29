"""Runtime configuration.

Resource identifiers are injected by the Databricks App through app.yaml
`valueFrom` bindings. Nothing here is hardcoded, and none of these values is
ever returned to the browser.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

from .errors import NotConfigured

APP_NAME = "Blue River Grid Intelligence"

RISK_DISCLAIMER = (
    "The risk score is a transparent portfolio demonstration heuristic. It is not a "
    "production engineering, protection, safety, or asset-health model."
)

SYNTHETIC_NOTICE = (
    "Synthetic Blue River Power portfolio environment. Blue River Power is not a real utility."
)

# Model validated in Stage 3. Invoked only through ai_query on the SQL warehouse.
MODEL_NAME = "system.ai.gpt-oss-20b"


@dataclass(frozen=True)
class Settings:
    warehouse_id: str | None
    search_index: str | None

    def require_warehouse(self) -> str:
        if not self.warehouse_id:
            raise NotConfigured("SQL warehouse")
        return self.warehouse_id

    def require_index(self) -> str:
        if not self.search_index:
            raise NotConfigured("AI Search index")
        return self.search_index


@lru_cache
def get_settings() -> Settings:
    return Settings(
        warehouse_id=os.environ.get("DATABRICKS_WAREHOUSE_ID") or None,
        search_index=os.environ.get("DATABRICKS_AI_SEARCH_INDEX") or None,
    )


@lru_cache
def get_workspace_client():
    """Databricks unified auth: the app service principal when deployed,
    the developer's CLI profile (DATABRICKS_CONFIG_PROFILE) locally."""
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()
