import textwrap
import difflib
from dataclasses import dataclass
from toyvm.utils import Color, print_diff

STACK_EFFECT = {
    # opname: (num_pops, num_pushes)
    'load_const': (0, 1),
    'load_local': (0, 1),
    'store_local': (1, 0),
    'load_local_green': (0, 1),
    'store_local_green': (1, 0),
    'load_nonlocal': (0, 1),
    'load_nonlocal_green': (0, 1),
    'return': (1, 0),
    'abort': (0, 0),
    'add': (2, 1),
    'mul': (2, 1),
    'lt': (2, 1),
    'gt': (2, 1),
    'i32_add': (2, 1),
    'label': (0, 0),
    'br_if': (1, 0),
    'br': (0, 0),
    'make_tuple': ('ARG', 1), # special, num_pops depends on the arg
    'print': ('ARG', 1),
    'call': ('ARG', 1),
    'pop': (1, 0),
    'get_iter': (1, 0),
    'for_iter': (0, 0),
    'unroll': (1, 1),
    'make_function': (0, 1),
}

PURE_OPS = set([
    'load_const',
    'add',
    'mul',
    'i32_add',
    'make_tuple',
    'unroll',
    'load_nonlocal_green',
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
        return f'<OpCode "{self.str()}">'

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

    def relabel(self, label_map):
        if self.name in ('br', 'br_if', 'label'):
            args = tuple(map(label_map.__getitem__, self.args))
        elif self.name == 'for_iter':
            itername, targetname, endfor = self.args
            endfor = label_map[endfor]
            args = itername, targetname, endfor
        else:
            args = self.args
        return OpCode(self.name, *args)

class CodeObject:

    def __init__(self, name, argnames, body):
        self.name = name
        self.argnames = argnames
        self.body = body

    def __repr__(self):
        return f'<CodeObject {self.name!r}>'

    def emit(self, op):
        self.body.append(op)

    def dump(self, *, show_pc=False, use_colors=False):
        lines = []
        for pc, op in enumerate(self.body):
            if op.name == 'label':
                label = op.args[0]
                if use_colors:
                    if '#' in label:
                        label, at = label.rsplit('#', 1)
                        at = '#' + at
                    else:
                        at = ''
                    line = (Color.set('yellow', label) +
                            Color.set('blue', at))
                else:
                    line = f'{label}:'

                lines.append(line)
            else:
                lines.append(f'  {op.str()}')
            if show_pc:
                lines[-1] = f'{pc:3d}: {lines[-1]}'
        return '\n'.join(lines)

    def pp(self, *, show_pc=True, use_colors=True):
        print(self.dump(show_pc=show_pc, use_colors=use_colors))

    def equals(self, expected):
        expected = textwrap.dedent(expected).strip('\n')
        got = textwrap.dedent(self.dump())
        if expected == got:
            return True
        else:
            print_diff(expected, got, 'expected', 'got')
            return False
