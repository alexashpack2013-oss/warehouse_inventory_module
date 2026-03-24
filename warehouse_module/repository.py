from __future__ import annotations

from collections.abc import Iterable
from threading import RLock

from .models import Movement, Product, Warehouse


class InMemoryInventoryRepository:
    """Простейшее хранилище данных в памяти.

    Используется в курсовом проекте как демонстрационная реализация.
    При необходимости его легко заменить на репозиторий для PostgreSQL/MySQL.
    """

    def __init__(self) -> None:
        self._products: dict[str, Product] = {}
        self._warehouses: dict[str, Warehouse] = {}
        self._stock: dict[tuple[str, str], float] = {}
        self._movements: list[Movement] = []
        self._lock = RLock()

    def add_product(self, product: Product) -> Product:
        with self._lock:
            if any(item.sku == product.sku for item in self._products.values()):
                raise ValueError(f"Товар с артикулом {product.sku} уже существует")
            self._products[product.id] = product
            return product

    def get_product(self, product_id: str) -> Product:
        try:
            return self._products[product_id]
        except KeyError as exc:
            raise ValueError("Товар не найден") from exc

    def list_products(self) -> list[Product]:
        return list(self._products.values())

    def add_warehouse(self, warehouse: Warehouse) -> Warehouse:
        with self._lock:
            if any(item.code == warehouse.code for item in self._warehouses.values()):
                raise ValueError(f"Склад с кодом {warehouse.code} уже существует")
            self._warehouses[warehouse.id] = warehouse
            return warehouse

    def get_warehouse(self, warehouse_id: str) -> Warehouse:
        try:
            return self._warehouses[warehouse_id]
        except KeyError as exc:
            raise ValueError("Склад не найден") from exc

    def list_warehouses(self) -> list[Warehouse]:
        return list(self._warehouses.values())

    def get_stock(self, product_id: str, warehouse_id: str) -> float:
        return self._stock.get((product_id, warehouse_id), 0.0)

    def set_stock(self, product_id: str, warehouse_id: str, quantity: float) -> None:
        with self._lock:
            self._stock[(product_id, warehouse_id)] = quantity

    def list_stock(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for (product_id, warehouse_id), quantity in self._stock.items():
            product = self._products.get(product_id)
            warehouse = self._warehouses.get(warehouse_id)
            rows.append(
                {
                    "product_id": product_id,
                    "product_name": product.name if product else "Неизвестный товар",
                    "warehouse_id": warehouse_id,
                    "warehouse_name": warehouse.name if warehouse else "Неизвестный склад",
                    "quantity": quantity,
                    "unit": product.unit if product else "шт",
                    "min_stock": product.min_stock if product else 0,
                }
            )
        return rows

    def add_movement(self, movement: Movement) -> Movement:
        with self._lock:
            self._movements.append(movement)
            return movement

    def list_movements(self) -> list[Movement]:
        return list(self._movements)

    def extend_seed(self, *, products: Iterable[Product], warehouses: Iterable[Warehouse]) -> None:
        for product in products:
            self.add_product(product)
        for warehouse in warehouses:
            self.add_warehouse(warehouse)
