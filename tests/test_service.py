import pytest

from warehouse_module.repository import InMemoryInventoryRepository
from warehouse_module.service import InventoryService


@pytest.fixture()
def service() -> InventoryService:
    repo = InMemoryInventoryRepository()
    service = InventoryService(repo)
    return service


def test_receipt_increases_stock(service: InventoryService) -> None:
    product = service.create_product(sku="SKU-001", name="Ноутбук", min_stock=2)
    warehouse = service.create_warehouse(name="Основной склад", code="MSK-01")

    service.receive_goods(
        product_id=product.id,
        warehouse_id=warehouse.id,
        quantity=10,
        operator="Иванов И.И.",
        document_number="PR-001",
    )

    stock = service.get_stock_report()
    assert stock[0]["quantity"] == 10


def test_issue_decreases_stock(service: InventoryService) -> None:
    product = service.create_product(sku="SKU-002", name="Монитор")
    warehouse = service.create_warehouse(name="Основной склад", code="EKB-01")

    service.receive_goods(product_id=product.id, warehouse_id=warehouse.id, quantity=5, operator="Петров П.П.")
    service.issue_goods(product_id=product.id, warehouse_id=warehouse.id, quantity=2, operator="Петров П.П.")

    stock = service.get_stock_report()
    assert stock[0]["quantity"] == 3


def test_transfer_moves_goods_between_warehouses(service: InventoryService) -> None:
    product = service.create_product(sku="SKU-003", name="Клавиатура")
    source = service.create_warehouse(name="Склад №1", code="WH-01")
    target = service.create_warehouse(name="Склад №2", code="WH-02")

    service.receive_goods(product_id=product.id, warehouse_id=source.id, quantity=7, operator="Сидоров С.С.")
    service.transfer_goods(
        product_id=product.id,
        source_warehouse_id=source.id,
        target_warehouse_id=target.id,
        quantity=4,
        operator="Сидоров С.С.",
    )

    stock = service.get_stock_report()
    quantities = {(row["warehouse_name"], row["quantity"]) for row in stock}
    assert ("Склад №1", 3) in quantities
    assert ("Склад №2", 4) in quantities


def test_issue_raises_error_when_stock_is_insufficient(service: InventoryService) -> None:
    product = service.create_product(sku="SKU-004", name="Мышь")
    warehouse = service.create_warehouse(name="Тестовый склад", code="TST-01")

    with pytest.raises(ValueError, match="Недостаточно товара"):
        service.issue_goods(product_id=product.id, warehouse_id=warehouse.id, quantity=1, operator="Тест")


def test_inventory_adjustment_sets_actual_balance(service: InventoryService) -> None:
    product = service.create_product(sku="SKU-005", name="Принтер")
    warehouse = service.create_warehouse(name="Резервный склад", code="RSV-01")

    service.receive_goods(product_id=product.id, warehouse_id=warehouse.id, quantity=9, operator="Орлов А.А.")
    movement = service.inventory_adjustment(
        product_id=product.id,
        warehouse_id=warehouse.id,
        actual_quantity=6,
        operator="Орлов А.А.",
        comment="Инвентаризация марта",
    )

    assert movement.quantity == -3
    assert service.get_stock_report()[0]["quantity"] == 6
