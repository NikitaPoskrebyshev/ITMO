import sys
import math
from typing import Any

PROMPT = '>>> '


def run_calc(context: dict[str, Any] | None = None) -> None:
    """Run interactive calculator session in specified namespace"""
    if context is None:
        context = {}
    context["__builtins__"] = {}
    sys.stdout.write(PROMPT)
    while (expr := sys.stdin.readline()) != '':
        print(eval(expr, context))
        sys.stdout.write(PROMPT)
    print()


if __name__ == '__main__':
    context = {'math': math}
    run_calc(context)
