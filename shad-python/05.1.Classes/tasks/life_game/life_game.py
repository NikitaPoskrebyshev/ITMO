import typing
from abc import abstractmethod


class LifeGame(object):
    """
    Class for Game life
    """

    def __init__(self, lst: list[list[int]]):
        LifeGame._height = len(lst)
        LifeGame._width = len(lst[0]) if len(lst) != 0 else 0
        LifeGame._ocean = [[LifeGame._Empty() for j in range(LifeGame._width)] for i in range(LifeGame._height)]
        for i in range(LifeGame._height):
            for j in range(LifeGame._width):
                LifeGame._ocean[i][j] = LifeGame._id_to_class[lst[i][j]]()

    class _Essence:
        @abstractmethod
        def _update(self, i: int, j: int) -> object:
            """Updates condition of an essence"""

        @staticmethod
        def _get_neighbours(i: int, j: int) -> dict[object, int]:
            """Returns dict where key is an essence type and
            value is its occurrence rate in neighbouring cells"""
            result: dict[object, int] = dict.fromkeys(LifeGame._class_to_id.keys(), 0)
            for di in range(-1, 2):
                for dj in range(-1, 2):
                    if 0 == di == dj:
                        continue
                    ii: int = i + di
                    jj: int = j + dj
                    if not (0 <= ii < LifeGame._height and 0 <= jj < LifeGame._width):
                        continue
                    result[LifeGame._ocean[i + di][j + dj].__class__] += 1
            return result

    class _Empty(_Essence):
        def _update(self, i: int, j: int) -> object:
            nb: dict[object, int] = self._get_neighbours(i, j)
            if nb[LifeGame._Fish] == 3:
                return LifeGame._Fish
            if nb[LifeGame._Shrimp] == 3:
                return LifeGame._Shrimp
            return LifeGame._Empty

    class _Creature(_Essence):
        def _update(self, i: int, j: int) -> object:
            nb: dict[object, int] = self._get_neighbours(i, j)
            if nb[self.__class__] >= 4 or nb[self.__class__] <= 1:
                return LifeGame._Empty
            return self.__class__

    class _Rock(_Essence):
        def _update(self, i: int, j: int) -> object:
            return LifeGame._Rock

    class _Fish(_Creature):
        pass

    class _Shrimp(_Creature):
        pass

    _id_to_class: dict[int, typing.Any] = {
        0: _Empty,
        1: _Rock,
        2: _Fish,
        3: _Shrimp
    }

    _class_to_id: dict[object, int] = {
        _Empty: 0,
        _Rock: 1,
        _Fish: 2,
        _Shrimp: 3
    }

    _height: int = 0
    _width: int = 0
    _ocean: list[list[_Essence]] = []

    def get_next_generation(self) -> list[list[int]]:
        return self._update()

    def _update(self) -> list[list[int]]:
        result: list[list[int]] = [[0 for j in range(LifeGame._width)] for i in range(LifeGame._height)]
        for i in range(LifeGame._height):
            for j in range(LifeGame._width):
                result[i][j] = LifeGame._class_to_id[LifeGame._ocean[i][j]._update(i, j)]
        LifeGame._ocean = \
            [[LifeGame._id_to_class[result[i][j]]() for j in range(LifeGame._width)] for i in range(LifeGame._height)]
        return result
