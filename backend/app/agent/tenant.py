from pydantic import BaseModel
from typing import Optional
import uuid
import time
from collections import defaultdict


class TenantLimits(BaseModel):
    max_requests_per_min: int = 60
    max_executions: int = 100


class Tenant(BaseModel):
    id: str
    api_key: str
    name: str
    limits: TenantLimits = TenantLimits()
    active: bool = True


class TenantManager:
    def __init__(self):
        self.tenants: dict[str, Tenant] = {}
        self.api_key_index: dict[str, str] = {}
        self.request_counts: dict[str, list[float]] = defaultdict(list)
        self._register_default()

    def _register_default(self):
        default_key = "ecomos-default-key"
        self.register(Tenant(
            id="default",
            api_key=default_key,
            name="Default Tenant",
            limits=TenantLimits(max_requests_per_min=100, max_executions=1000)
        ))

    def register(self, tenant: Tenant):
        self.tenants[tenant.id] = tenant
        self.api_key_index[tenant.api_key] = tenant.id

    def get_by_api_key(self, api_key: str) -> Optional[Tenant]:
        tenant_id = self.api_key_index.get(api_key)
        if not tenant_id:
            return None
        tenant = self.tenants.get(tenant_id)
        if tenant and tenant.active:
            return tenant
        return None

    def get(self, tenant_id: str) -> Optional[Tenant]:
        return self.tenants.get(tenant_id)

    def check_rate_limit(self, tenant_id: str) -> bool:
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False

        now = time.time()
        window = 60

        self.request_counts[tenant_id] = [
            t for t in self.request_counts[tenant_id]
            if now - t < window
        ]

        if len(self.request_counts[tenant_id]) >= tenant.limits.max_requests_per_min:
            return False

        self.request_counts[tenant_id].append(now)
        return True

    def create_api_key(self, tenant_id: str) -> Optional[str]:
        if tenant_id not in self.tenants:
            return None
        new_key = f"ecomos-{uuid.uuid4().hex[:16]}"
        self.tenants[tenant_id].api_key = new_key
        self.api_key_index[new_key] = tenant_id
        return new_key

    def list_tenants(self) -> list[dict]:
        return [
            {"id": t.id, "name": t.name, "active": t.active}
            for t in self.tenants.values()
        ]
