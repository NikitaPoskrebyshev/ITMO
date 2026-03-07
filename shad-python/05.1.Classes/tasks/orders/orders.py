from dataclasses import dataclass, field, InitVar
from abc import ABC, abstractmethod


DISCOUNT_PERCENTS = 15


@dataclass(order=True, frozen=True)
class Item:
    # note: you might want to change the order of fields
    item_id: int = field(compare=False)
    title: str
    cost: int

    def __post_init__(self) -> None:
        assert self.title != '', 'Item\'s title should not be empty!'
        assert self.cost > 0, 'Item\'s cost should be a positive value!'


# You may set `# type: ignore` on this class
# It is [a really old issue](https://github.com/python/mypy/issues/5374)
# But seems to be solved
@dataclass
class Position(ABC):
    item: Item

    @property
    @abstractmethod
    def cost(self) -> int | float:
        pass


@dataclass
class CountedPosition(Position):
    count: int = 1

    @property
    def cost(self) -> int:
        return self.count * self.item.cost


@dataclass
class WeightedPosition(Position):
    weight: float = 1.0

    @property
    def cost(self) -> float:
        return self.weight * self.item.cost


@dataclass
class Order:
    order_id: int
    positions: list[Position] = field(default_factory=list[Position])
    cost: int = field(init=False)
    have_promo: InitVar[bool] = field(default=False)

    def __post_init__(self, have_promo: bool) -> None:
        self.cost = int(sum([p.cost for p in self.positions]))
        if have_promo:
            self.cost = int(self.cost * (100 - DISCOUNT_PERCENTS) / 100)
