from collections import UserList
import typing as tp


class ListTwist(UserList[tp.Any]):
    """
    List-like class with additional attributes:
        * reversed, R - return reversed list
        * first, F - insert or retrieve first element;
                     Undefined for empty list
        * last, L -  insert or retrieve last element;
                     Undefined for empty list
        * size, S -  set or retrieve size of list;
                     If size less than list length - truncate to size;
                     If size greater than list length - pad with Nones
    """
    reverse_cmd: list[str] = ['R', 'reversed']
    first_cmd: list[str] = ['F', 'first']
    last_cmd: list[str] = ['L', 'last']
    size_cmd: list[str] = ['S', 'size']

    def __getattr__(self, item: str) -> tp.Any:
        if item in self.reverse_cmd:
            return list(reversed(self.data))
        elif item in self.first_cmd:
            return self.data[0]
        elif item in self.last_cmd:
            return self.data[-1]
        elif item in self.size_cmd:
            return len(self.data)
        else:
            return super().__getattribute__(item)

    def __setattr__(self, key: str, value: tp.Any) -> None:
        if key in self.first_cmd:
            self.data[0] = value
        elif key in self.last_cmd:
            self.data[-1] = value
        elif key in self.size_cmd:
            self.data = self.data[:value]
            if value > len(self.data):
                self.data += [None for i in range(value - len(self.data))]
        else:
            return super().__setattr__(key, value)
