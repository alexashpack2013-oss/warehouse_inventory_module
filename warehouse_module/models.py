from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


def generate_id() -> str:
    return uuid4().hex


class MovementType(str, Enum):
    RECEIPT = "receipt"
    ISSUE = "issue"
    TRANSFER = "transfer"
    INVENTORY_ADJUSTMENT = "inventory_adjustment"


@dataclass(slots=True)
class Product:
    sku: str
    name: str
    unit: str = "шт"
    min_stock: float = 0
    id: str = field(default_factory=generate_id)


@dataclass(slots=True)
class Warehouse:
    name: str
    code: str
    id: str = field(default_factory=generate_id)


@dataclass(slots=True)
class Movement:
    movement_type: MovementType
    product_id: str
    quantity: float
    operator: str
    source_warehouse_id: str | None = None
    target_warehouse_id: str | None = None
    document_number: str | None = None
    comment: str | None = None
    resulting_balance: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=generate_id)
