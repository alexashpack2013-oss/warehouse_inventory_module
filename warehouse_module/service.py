from __future__ import annotations

from dataclasses import asdict

from .models import Movement, MovementType, Product, Warehouse
from .repository import InMemoryInventoryRepository


class InventoryService:
    """Сервисный слой модуля складского учета.

    Реализует ключевые бизнес-операции:
    - приход товара;
    - расход товара;
    - перемещение между складами;
    - корректировка остатков по результатам инвентаризации;
    - формирование отчетов по остаткам.
    """

    def __init__(self, repository: InMemoryInventoryRepository) -> None:
        self.repository = repository

    def create_product(self, *, sku: str, name: str, unit: str = "шт", min_stock: float = 0) -> Product:
        if min_stock < 0:
            raise ValueError("Минимальный остаток не может быть отрицательным")
        product = Product(sku=sku.strip(), name=name.strip(), unit=unit.strip(), min_stock=min_stock)
        return self.repository.add_product(product)

    def create_warehouse(self, *, name: str, code: str) -> Warehouse:
        warehouse = Warehouse(name=name.strip(), code=code.strip().upper())
        return self.repository.add_warehouse(warehouse)

    def receive_goods(
        self,
        *,
        product_id: str,
        warehouse_id: str,
        quantity: float,
        operator: str,
        document_number: str | None = None,
        comment: str | None = None,
    ) -> Movement:
        self._validate_positive_quantity(quantity)
        self.repository.get_product(product_id)
        self.repository.get_warehouse(warehouse_id)

        current_stock = self.repository.get_stock(product_id, warehouse_id)
        new_balance = current_stock + quantity
        self.repository.set_stock(product_id, warehouse_id, new_balance)

        movement = Movement(
            movement_type=MovementType.RECEIPT,
            product_id=product_id,
            quantity=quantity,
            operator=operator,
            target_warehouse_id=warehouse_id,
            document_number=document_number,
            comment=comment,
            resulting_balance=new_balance,
        )
        return self.repository.add_movement(movement)

    def issue_goods(
        self,
        *,
        product_id: str,
        warehouse_id: str,
        quantity: float,
        operator: str,
        document_number: str | None = None,
        comment: str | None = None,
    ) -> Movement:
        self._validate_positive_quantity(quantity)
        self.repository.get_product(product_id)
        self.repository.get_warehouse(warehouse_id)

        current_stock = self.repository.get_stock(product_id, warehouse_id)
        if current_stock < quantity:
            raise ValueError(
                f"Недостаточно товара на складе. Доступно: {current_stock}, запрошено: {quantity}"
            )

        new_balance = current_stock - quantity
        self.repository.set_stock(product_id, warehouse_id, new_balance)

        movement = Movement(
            movement_type=MovementType.ISSUE,
            product_id=product_id,
            quantity=quantity,
            operator=operator,
            source_warehouse_id=warehouse_id,
            document_number=document_number,
            comment=comment,
            resulting_balance=new_balance,
        )
        return self.repository.add_movement(movement)

    def transfer_goods(
        self,
        *,
        product_id: str,
        source_warehouse_id: str,
        target_warehouse_id: str,
        quantity: float,
        operator: str,
        document_number: str | None = None,
        comment: str | None = None,
    ) -> Movement:
        self._validate_positive_quantity(quantity)
        if source_warehouse_id == target_warehouse_id:
            raise ValueError("Склад-источник и склад-получатель не должны совпадать")

        self.repository.get_product(product_id)
        self.repository.get_warehouse(source_warehouse_id)
        self.repository.get_warehouse(target_warehouse_id)

        source_stock = self.repository.get_stock(product_id, source_warehouse_id)
        if source_stock < quantity:
            raise ValueError(
                f"Недостаточно товара для перемещения. Доступно: {source_stock}, требуется: {quantity}"
            )

        target_stock = self.repository.get_stock(product_id, target_warehouse_id)
        self.repository.set_stock(product_id, source_warehouse_id, source_stock - quantity)
        self.repository.set_stock(product_id, target_warehouse_id, target_stock + quantity)

        movement = Movement(
            movement_type=MovementType.TRANSFER,
            product_id=product_id,
            quantity=quantity,
            operator=operator,
            source_warehouse_id=source_warehouse_id,
            target_warehouse_id=target_warehouse_id,
            document_number=document_number,
            comment=comment,
            resulting_balance=target_stock + quantity,
        )
        return self.repository.add_movement(movement)

    def inventory_adjustment(
        self,
        *,
        product_id: str,
        warehouse_id: str,
        actual_quantity: float,
        operator: str,
        comment: str | None = None,
    ) -> Movement:
        if actual_quantity < 0:
            raise ValueError("Фактический остаток не может быть отрицательным")

        self.repository.get_product(product_id)
        self.repository.get_warehouse(warehouse_id)

        current_stock = self.repository.get_stock(product_id, warehouse_id)
        delta = actual_quantity - current_stock
        self.repository.set_stock(product_id, warehouse_id, actual_quantity)

        movement = Movement(
            movement_type=MovementType.INVENTORY_ADJUSTMENT,
            product_id=product_id,
            quantity=delta,
            operator=operator,
            target_warehouse_id=warehouse_id,
            comment=comment,
            resulting_balance=actual_quantity,
        )
        return self.repository.add_movement(movement)

    def get_stock_report(self) -> list[dict[str, object]]:
        return self.repository.list_stock()

    def get_low_stock_report(self) -> list[dict[str, object]]:
        low_stock_rows: list[dict[str, object]] = []
        for row in self.repository.list_stock():
            if float(row["quantity"]) <= float(row["min_stock"]):
                low_stock_rows.append(row)
        return low_stock_rows

    def get_movements(self) -> list[dict[str, object]]:
        return [asdict(movement) for movement in self.repository.list_movements()]

    @staticmethod
    def _validate_positive_quantity(quantity: float) -> None:
        if quantity <= 0:
            raise ValueError("Количество должно быть больше нуля")
