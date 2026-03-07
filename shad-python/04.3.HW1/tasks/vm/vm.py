"""
Simplified VM code which works for some cases.
You need extend/rewrite code to pass all cases.
"""

import builtins
import dis
import operator
import types
import typing as tp


class Frame:
    """
    Frame header in cpython with description
        https://github.com/python/cpython/blob/3.12/Include/internal/pycore_frame.h

    Text description of frame parameters
        https://docs.python.org/3/library/inspect.html?highlight=frame#types-and-members
    """
    def __init__(self,
                 frame_code: types.CodeType,
                 frame_builtins: dict[str, tp.Any],
                 frame_globals: dict[str, tp.Any],
                 frame_locals: dict[str, tp.Any]) -> None:
        self.code = frame_code
        self.builtins = frame_builtins
        self.globals = frame_globals
        self.locals = frame_locals
        self.data_stack: tp.Any = []
        self.return_value = None

        self.has_return_value = False
        self.instructions: list[dis.Instruction] = list(dis.get_instructions(self.code))
        self._offset_to_pos = {
            instruction.offset: pos
            for pos, instruction in enumerate(self.instructions)
            if instruction.is_jump_target
        }
        self.pointer: int = 0

    def top(self) -> tp.Any:
        return self.data_stack[-1]

    def pop(self) -> tp.Any:
        return self.data_stack.pop()

    def push(self, *values: tp.Any) -> None:
        self.data_stack.extend(values)

    def popn(self, n: int) -> tp.Any:
        """
        Pop a number of values from the value stack.
        A list of n values is returned, the deepest value first.
        """
        if n > 0:
            returned = self.data_stack[-n:]
            self.data_stack[-n:] = []
            return returned
        else:
            return []

    def run(self) -> tp.Any:
        while not self.has_return_value:
            instruction = self.instructions[self.pointer]
            pointer_save = self.pointer
            getattr(self, instruction.opname.lower() + "_op")(instruction.argval)
            if pointer_save == self.pointer:
                self.pointer += 1
        return self.return_value

    def resume_op(self, arg: int) -> tp.Any:
        pass

    def push_null_op(self, arg: int) -> tp.Any:
        self.push(None)

    def precall_op(self, arg: int) -> tp.Any:
        pass

    def call_op(self, arg: int) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.12.5/library/dis.html#opcode-CALL
        """
        arguments = self.popn(arg)
        if self.top() is None:
            self.pop()
        f = self.pop()
        self.push(f(*arguments))

    def swap_op(self, i: int) -> None:
        self.data_stack[-1], self.data_stack[-i] = self.data_stack[-i], self.data_stack[-1]

    def is_op_op(self, invert: bool) -> None:
        rhs = self.pop()
        lhs = self.pop()
        if invert:
            self.push((lhs is not rhs))
        else:
            self.push((lhs is rhs))

    def contains_op_op(self, invert: bool) -> None:
        rhs = self.pop()
        lhs = self.pop()
        if invert:
            self.push((lhs not in rhs))
        else:
            self.push((lhs in rhs))

    def load_name_op(self, arg: str) -> None:
        """
        Partial realization

        Operation description:
            https://docs.python.org/release/3.12.5/library/dis.html#opcode-LOAD_NAME
        """
        if arg in self.locals:
            self.push(self.locals[arg])
        elif arg in self.globals:
            self.push(self.globals[arg])
        elif arg in self.builtins:
            self.push(self.builtins[arg])
        else:
            raise NameError(f"name '{arg}' is not defined")

    def delete_name_op(self, arg: str) -> None:
        del self.locals[arg]

    def load_global_op(self, arg: str) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.12.5/library/dis.html#opcode-LOAD_GLOBAL
        """
        if arg in self.globals:
            self.push(self.globals[arg])
        elif arg in self.builtins:
            self.push(self.builtins[arg])
        else:
            raise NameError(f"name '{arg}' is not defined")

    def delete_global_op(self, arg: str) -> None:
        del self.globals[arg]

    def load_const_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.12.5/library/dis.html#opcode-LOAD_CONST
        """
        self.push(arg)

    def load_fast_op(self, arg: str) -> None:
        if arg in self.locals:
            self.push(self.locals[arg])

    def load_fast_check_op(self, arg: str) -> None:
        if arg in self.locals:
            self.push(self.locals[arg])
        else:
            raise UnboundLocalError(f"name '{arg}' is not defined")

    def load_fast_abd_clear_op(self, arg: str) -> None:
        if arg in self.locals:
            self.push(self.locals[arg])
        else:
            self.push(None)
            self.locals[arg] = None

    def load_attr_op(self, namei: str) -> None:
        self.push(getattr(self.pop(), namei))

    def return_value_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.12.5/library/dis.html#opcode-RETURN_VALUE
        """
        self.has_return_value = True
        self.return_value = self.pop()

    def return_const_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.12.5/library/dis.html#opcode-RETURN_VALUE
        """
        self.has_return_value = True
        self.return_value = arg

    def get_iter_op(self, arg: tp.Any) -> None:
        self.push(iter(self.pop()))

    def get_len_op(self, arg: tp.Any) -> None:
        self.push(len(self.top()))

    def for_iter_op(self, delta: int) -> None:
        try:
            nxt = self.top().__next__()
            self.push(nxt)
        except StopIteration:
            self._jump(delta)

    def end_for_op(self, arg: tp.Any) -> None:
        self.popn(2)

    def copy_op(self, i: int) -> None:
        self.push(self.data_stack[-i])

    def pop_top_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.12.5/library/dis.html#opcode-POP_TOP
        """
        self.pop()

    def pop_except_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.12.5/library/dis.html#opcode-POP_TOP
        """
        self.pop()

    def make_function_op(self, arg: int) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.12.5/library/dis.html#opcode-MAKE_FUNCTION
        """
        code = self.pop()  # the code associated with the function (at TOS1)

        # TODO: use arg to parse function defaults

        def f(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
            # TODO: parse input arguments using code attributes such as co_argcount

            parsed_args: dict[str, tp.Any] = {}
            f_locals = dict(self.locals)
            f_locals.update(parsed_args)

            frame = Frame(code, self.builtins, self.globals, f_locals)  # Run code in prepared environment
            return frame.run()

        self.push(f)

    def binary_subscr_op(self, arg: tp.Any) -> None:
        key = self.pop()
        container = self.pop()
        self.push(container[key])

    def binary_slice_op(self, arg: tp.Any) -> None:
        end = self.pop()
        start = self.pop()
        container = self.pop()
        self.push(container[start:end])

    def build_tuple_op(self, count: int) -> None:
        self.push(tuple(self.popn(count)))

    def build_list_op(self, count: int) -> None:
        self.push(self.popn(count))

    def list_append_op(self, i: int) -> None:
        value = self.pop()
        list.append(self.data_stack[-i], value)

    def build_slice_op(self, argc: int) -> None:
        if argc == 2:
            end = self.pop()
            start = self.pop()
            self.push(slice(start, end))
        elif argc == 3:
            step = self.pop()
            end = self.pop()
            start = self.pop()
            self.push(slice(start, end, step))
        else:
            raise ValueError(f"slice takes 2 or 3 arguments, {argc} given")

    def build_const_key_map_op(self, count: int) -> None:
        keys = self.pop()
        values = self.popn(count)
        self.push(dict(zip(keys, values)))

    def build_map_op(self, count: int) -> None:
        mp = dict()
        for _ in range(count):
            value = self.pop()
            key = self.pop()
            mp[key] = value
        self.push(mp)

    def map_add_op(self, i: int) -> None:
        value = self.pop()
        key = self.pop()
        dict.__setitem__(self.data_stack[-i], key, value)

    def build_set_op(self, count: int) -> None:
        self.push(set(self.popn(count)))

    def set_update_op(self, i: int) -> None:
        seq = self.pop()
        set.update(self.data_stack[-i], seq)

    def set_add_op(self, i: int) -> None:
        value = self.pop()
        set.add(self.data_stack[-i], value)

    def dict_update_op(self, i: int) -> None:
        seq = self.pop()
        set.update(self.data_stack[-i], seq)

    def dict_merge_op(self, i: int) -> None:
        seq1 = self.top()
        seq2 = self.data_stack[-i]
        if seq1.keys() & seq2.keys():
            raise Exception
        self.dict_update_op(i)

    def list_extend_op(self, i: int) -> None:
        seq = self.popn(i)
        self.top().extend(*seq)

    def unpack_sequence_op(self, count: int) -> None:
        seq = self.pop()
        for i in range(count):
            self.push(seq[-i-1])

    def store_name_op(self, arg: str) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.12.5/library/dis.html#opcode-STORE_NAME
        """
        const = self.pop()
        self.locals[arg] = const

    def store_global_op(self, arg: str) -> None:
        val = self.pop()
        self.globals[arg] = val

    def store_fast_op(self, arg: str) -> None:
        self.locals[arg] = self.pop()

    def store_attr_op(self, name: str) -> None:
        setattr(self.pop(), name, self.pop())

    def delete_fast_op(self, arg: str) -> None:
        del self.locals[arg]

    def delete_attr_op(self, name: str) -> None:
        delattr(self.top(), name)

    def store_slice_op(self, arg: str) -> None:
        end = self.pop()
        start = self.pop()
        container = self.pop()
        value = self.pop()
        container[start:end] = value

    def delete_subscr_op(self, arg: tp.Any) -> None:
        key = self.pop()
        container = self.pop()
        del container[key]

    def unary_negative_op(self, arg: tp.Any) -> None:
        self.push(-self.pop())

    def unary_not_op(self, arg: tp.Any) -> None:
        self.push(not self.pop())

    def unary_invert_op(self, arg: tp.Any) -> None:
        self.push(~self.pop())

    def binary_op_op(self, op: int) -> None:
        lhs, rhs = self.popn(2)
        if 0 <= op < len(self._BINARY_OPERATORS):
            self.push(self._BINARY_OPERATORS[op](lhs, rhs))

    def compare_op_op(self, op: str) -> None:
        lhs, rhs = self.popn(2)
        if op in self._COMPARE_OPERATORS:
            self.push(self._COMPARE_OPERATORS[op](lhs, rhs))

    def pop_jump_if_true_op(self, delta: int) -> None:
        if self.pop():
            self._jump(delta)

    def pop_jump_if_false_op(self, delta: int) -> None:
        if not self.pop():
            self._jump(delta)

    def pop_jump_if_none_op(self, delta: int) -> None:
        if self.pop() is None:
            self._jump(delta)

    def pop_jump_if_not_none_op(self, delta: int) -> None:
        if self.pop() is not None:
            self._jump(delta)

    def jump_backward_no_interrupt_op(self, delta: int) -> None:
        self._jump(delta)

    def jump_backward_op(self, delta: int) -> None:
        self._jump(delta)

    def jump_forward_op(self, delta: int) -> None:
        self._jump(delta)

    def _jump(self, delta: int) -> None:
        self.pointer = self._offset_to_pos[delta]

    def load_assertion_error_op(self, arg: tp.Any) -> None:
        self.push(AssertionError)

    def raise_varargs_op(self, argc: int) -> None:
        pass

    def reraise_op(self, argc: int) -> None:
        ex = self.pop()
        if ex.arg:
            self.pop()

    def extended_arg_op(self, ext: tp.Any) -> None:
        pass

    def nop_op(self, arg: tp.Any) -> None:
        pass

    _BINARY_OPERATORS: list[tp.Callable[[tp.Any, tp.Any], tp.Any]] = [
        operator.add,
        operator.and_,
        operator.floordiv,
        operator.lshift,
        operator.matmul,
        operator.mul,
        operator.mod,
        operator.or_,
        operator.pow,
        operator.rshift,
        operator.sub,
        operator.truediv,
        operator.xor,
        operator.iadd,
        operator.iand,
        operator.ifloordiv,
        operator.ilshift,
        operator.imatmul,
        operator.imul,
        operator.imod,
        operator.ior,
        operator.ipow,
        operator.irshift,
        operator.isub,
        operator.itruediv,
        operator.ixor
    ]

    _COMPARE_OPERATORS: dict[str, tp.Callable[[tp.Any, tp.Any], bool]] = {
        "<": operator.lt,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        ">=": operator.ge
    }


class VirtualMachine:
    def run(self, code_obj: types.CodeType) -> None:
        """
        :param code_obj: code for interpreting
        """
        globals_context: dict[str, tp.Any] = {}
        frame = Frame(code_obj, builtins.globals()['__builtins__'], globals_context, globals_context)
        return frame.run()
