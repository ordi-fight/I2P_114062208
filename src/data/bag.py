import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item


class Bag:
    _monsters_data: list[Monster]
    _items_data: list[Item]

    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []
        # define the monster data's name in object bag is _monsters_data and has a form of list
        # define the item data's name in object bag is _item_data and has a form of list
    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        pass

    def add_monster(self, monster: dict):
        self._monsters_data.append(monster)

    def to_dict(self) -> dict[str, object]:
        return {
            "monsters": list(self._monsters_data),
            "items": list(self._items_data)
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        monsters = data.get("monsters") or []
        items = data.get("items") or []
        bag = cls(monsters, items)
        return bag
    def add_item(self, name: str, amount: int = 1):
   
        # 找同名物品 → 增加數量
        for item in self._items_data:
            if item["name"] == name:
                item["count"] += amount
            return
        # 如果沒有就新增
        self._items_data.append({"name": name, "amount": amount})