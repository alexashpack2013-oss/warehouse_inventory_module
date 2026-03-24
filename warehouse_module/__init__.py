"""Модуль учета движения товара для информационной системы складского учета."""

from .service import InventoryService
from .repository import InMemoryInventoryRepository

__all__ = ["InventoryService", "InMemoryInventoryRepository"]
