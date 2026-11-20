from dataclasses import dataclass
from uuid import UUID

from app.core.ids import new_uuid


@dataclass(frozen=True)
class ProviderIntent:
    provider: str
    provider_ref: str
    status: str


class LocalCashProvider:
    name = "local_cash"

    def create_intent(self, amount, currency, reference) -> ProviderIntent:
        _ = (amount, currency, reference)
        return ProviderIntent(provider=self.name, provider_ref=str(new_uuid()), status="completed")

    def verify(self, provider_ref: str) -> str:
        _ = provider_ref
        return "settled"


class MockMobilePendingProvider:
    name = "mock_mobile_pending"

    def create_intent(self, amount, currency, reference) -> ProviderIntent:
        _ = (amount, currency, reference)
        return ProviderIntent(provider=self.name, provider_ref=f"momo-{new_uuid()}", status="pending")

    def verify(self, provider_ref: str) -> str:
        _ = provider_ref
        return "pending"


def provider_for(method: str, requested: str | None):
    if method == "cash":
        return LocalCashProvider()
    if method == "mobile_money":
        if requested and requested not in {MockMobilePendingProvider.name, "mock_mobile_pending"}:
            raise ValueError(requested)
        return MockMobilePendingProvider()
    if method in {"card", "bank_transfer"}:
        return MockMobilePendingProvider()
    if method == "store_credit":
        return LocalCashProvider()
    raise ValueError(method)
