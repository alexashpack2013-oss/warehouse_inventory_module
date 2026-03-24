from __future__ import annotations

from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .repository import InMemoryInventoryRepository
from .service import InventoryService

app = FastAPI(title="Warehouse Inventory Module", version="1.0.0")
repository = InMemoryInventoryRepository()
service = InventoryService(repository)


class ProductCreate(BaseModel):
    sku: str = Field(..., description="Артикул товара")
    name: str = Field(..., description="Наименование товара")
    unit: str = Field(default="шт", description="Единица измерения")
    min_stock: float = Field(default=0, ge=0, description="Минимальный остаток")


class WarehouseCreate(BaseModel):
    name: str
    code: str


class ReceiptRequest(BaseModel):
    product_id: str
    warehouse_id: str
    quantity: float = Field(..., gt=0)
    operator: str
    document_number: str | None = None
    comment: str | None = None


class IssueRequest(BaseModel):
    product_id: str
    warehouse_id: str
    quantity: float = Field(..., gt=0)
    operator: str
    document_number: str | None = None
    comment: str | None = None


class TransferRequest(BaseModel):
    product_id: str
    source_warehouse_id: str
    target_warehouse_id: str
    quantity: float = Field(..., gt=0)
    operator: str
    document_number: str | None = None
    comment: str | None = None


class InventoryAdjustmentRequest(BaseModel):
    product_id: str
    warehouse_id: str
    actual_quantity: float = Field(..., ge=0)
    operator: str
    comment: str | None = None


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Модуль учета движения товара запущен"}


@app.post("/products")
def create_product(payload: ProductCreate) -> dict[str, object]:
    try:
        product = service.create_product(**payload.model_dump())
        return asdict(product)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/warehouses")
def create_warehouse(payload: WarehouseCreate) -> dict[str, object]:
    try:
        warehouse = service.create_warehouse(**payload.model_dump())
        return asdict(warehouse)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/movements/receipt")
def receive_goods(payload: ReceiptRequest) -> dict[str, object]:
    try:
        movement = service.receive_goods(**payload.model_dump())
        return asdict(movement)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/movements/issue")
def issue_goods(payload: IssueRequest) -> dict[str, object]:
    try:
        movement = service.issue_goods(**payload.model_dump())
        return asdict(movement)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/movements/transfer")
def transfer_goods(payload: TransferRequest) -> dict[str, object]:
    try:
        movement = service.transfer_goods(**payload.model_dump())
        return asdict(movement)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/movements/inventory-adjustment")
def inventory_adjustment(payload: InventoryAdjustmentRequest) -> dict[str, object]:
    try:
        movement = service.inventory_adjustment(**payload.model_dump())
        return asdict(movement)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/stock")
def stock_report() -> list[dict[str, object]]:
    return service.get_stock_report()


@app.get("/reports/low-stock")
def low_stock_report() -> list[dict[str, object]]:
    return service.get_low_stock_report()


@app.get("/movements")
def movement_history() -> list[dict[str, object]]:
    return service.get_movements()