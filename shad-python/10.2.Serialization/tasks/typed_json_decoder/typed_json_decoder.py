import typing as tp
import json

from decimal import Decimal


def decode_typed_json(json_value: str) -> tp.Any:
    """
    Returns deserialized object from json string.
    Checks __custom_key_type__ in object's keys to choose appropriate type.

    :param json_value: serialized object in json format
    :return: deserialized object
    """
    conv: dict[str, tp.Callable[[str], tp.Any]] = {
        'int': int,
        'float': float,
        'decimal': Decimal
    }

    def custom_key(dct: dict[tp.Any, tp.Any]) -> tp.Any:
        val = dct.get('__custom_key_type__')
        if val is not None:
            dct.pop('__custom_key_type__')
            return {conv[val](key): value for key, value in dct.items()}
        return dct

    return json.loads(json_value, object_hook=custom_key)
