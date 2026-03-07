def problem01() -> dict[int, str]:
    return {
        5: "Переменная a может быть наном, в этом случае упадет",
        7: "get может вернуть либо int либо None, т.е Optional[int]"
    }


def problem02() -> dict[int, str]:
    return {
        5: "a имеет тип list[object], поэтому для его элементов операция += не определена"
    }


def problem03() -> dict[int, str]:
    return {
        9: "set инвариантен, в foo подать можно только set[int], получили set[float]",
        13: "set инвариантен, в foo подать можно только set[int], получили set[bool]"
    }


def problem04() -> dict[int, str]:
    return {
        9: "AbstractSet ковариантен, int - подтип float, значит AbstractSet[float] не подтип AbstractSet[int]"
    }


def problem05() -> dict[int, str]:
    return {
        11: "На выходе ожидается B, а возвращается A, это плохо, потому что B - наследник класса A и может иметь"
            "собственные методы, отсутствующие в A"
    }


def problem06() -> dict[int, str]:
    return {
        15: "Повышение типа перезаписываемой переменной"
    }


def problem07() -> dict[int, str]:
    return {
        25: "Повышение типа возвращаемого объекта",
        27: "Повышение типа возвращаемого объекта + понижение типа аргумента передаваемого callable",
        28: "понижение типа аргумента передаваемого callable"
    }


def problem08() -> dict[int, str]:
    return {
        6: "У Iterable нет метода __len__()",
        18: "У класса A отсутствует метод __iter__(), значит он не Iterable",
        24: "Ожидаем итератор на str, имеем на int"
    }


def problem09() -> dict[int, str]:
    return {
        32: "Метода __contains()__ может не быть у Fooable",
        34: "[] не Fooable",
        37: "Класс С не Fooable",
        38: "Функция foo не Fooable"
    }


def problem10() -> dict[int, str]:
    return {
        18: "str не предок SupportsFloat",
        29: "float - предок int"
    }
