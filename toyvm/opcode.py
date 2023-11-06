import textwrap
from dataclasses import dataclass

STACK_EFFECT = {
    # opname: (num_pops, num_pushes)
    'load_const': (0, 1),
    'load_local': (0, 1),
    'store_local': (1, 0),
    'load_local_green': (0, 1),
    'store_local_green': (1, 0),
    'return': (1, 0),
    'abort': (0, 0),
    'add': (2, 1),
    'mul': (2, 1),
    'gt': (2, 1),
    'br_if': (1, 0),
    'br': (0, 0),
    'make_tuple': ('ARG', 1), # special, num_pops depends on the arg
    'print': ('ARG', 1),
    'pop': (1, 0),
    'get_iter': (1, 0),
    'for_iter': (0, 0),
    'unroll': (1, 1),
}

PURE_OPS = set([
    'load_const',
    'add',
    'mul',
    'make_tuple',
    'unroll',
])

@dataclass
class OpCode:
    name: str
    args: tuple

    def __init__(self, name: str, *args):
        assert name in STACK_EFFECT, name
        self.name = name
        self.args = args

    def __repr__(self):
        if self.args:
            return f'<OpCode {self.name} {list(self.args)}>'
        else:
            return f'<OpCode {self.name}>'

    def str(self):
        parts = [self.name] + list(map(str, self.args))
        return ' '.join(parts)

    def copy(self):
        return OpCode(self.name, *self.args)

    def is_pure(self):
        return self.name in PURE_OPS

    def replace_args(self, *args):
        assert len(args) == len(self.args)
        self.args = args

    def num_pops(self):
        pops = STACK_EFFECT[self.name][0]
        if pops == 'ARG':
            return self.args[0]
        return pops

    def num_pushes(self):
        return STACK_EFFECT[self.name][1]

    def stack_effect(self):
        pops, pushes = STACK_EFFECT[self.name]
        return pushes - pops


class CodeObject:

    def __init__(self, name, body):
        self.name = name
        self.body = body

    def emit(self, op):
        self.body.append(op)

    def dump(self):
        lines = []
        for pc, op in enumerate(self.body):
            lines.append(f'{pc:2d}: {op.str()}')
        return '\n'.join(lines)

    def pp(self):
        print(self.dump())

    def equals(self, expected):
        dumped = textwrap.dedent(self.dump())
        expected = textwrap.dedent(expected).strip('\n')
        if dumped != expected:
            print('got')
            print(dumped)
            print()
            print('expected')
            print(expected)
        return dumped == expected
