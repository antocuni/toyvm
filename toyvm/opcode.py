from dataclasses import dataclass

STACK_EFFECT = {
    # opname: (num_pops, num_pushes)
    'load_const': (0, 1),
    'load_local': (0, 1),
    'store_local': (1, 0),
    'return': (1, 0),
    'abort': (0, 0),
    'add': (2, 1),
    'mul': (2, 1),
    'gt': (2, 1),
    'br_if': (1, 0),
}

PURE_OPS = set([
    'load_const',
    'add',
    'mul'
])

@dataclass
class OpCode:
    name: str
    args: tuple

    def __init__(self, name: str, *args):
        assert name in STACK_EFFECT
        self.name = name
        self.args = args

    def __repr__(self):
        if self.args:
            return f'<OpCode {self.name} {list(self.args)}>'
        else:
            return f'<OpCode {self.name}>'

    def is_pure(self):
        return self.name in PURE_OPS

    def num_pops(self):
        return STACK_EFFECT[self.name][0]

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

    def print(self):
        for op in self.body:
            parts = [op.name] + list(map(str, op.args))
            print(' '.join(parts))
