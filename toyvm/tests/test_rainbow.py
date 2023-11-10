import pytest
from toyvm.rainbow import RainbowInterpreter
from toyvm.opcode import OpCode, CodeObject
from toyvm.objects import W_Int, W_Str, W_Function, W_Tuple, w_None
from toyvm.compiler import toy_compile

class TestRainbow:

    def peval(self, code):
        w_func = W_Function(code.name, code, {})
        self.interp = RainbowInterpreter(w_func)
        self.interp.run()
        return self.interp.out

    def test_simple(self):
        code = CodeObject('fn', [], [
            OpCode('load_local', 'a'),
            OpCode('load_local', 'b'),
            OpCode('add'),
            OpCode('return'),
        ])
        code2 = self.peval(code)
        assert code2.body == code.body

    def test_green_op(self):
        code = CodeObject('fn', [], [
            OpCode('load_const', W_Int(1)),
            OpCode('load_const', W_Int(2)),
            OpCode('add'),
            OpCode('return'),
        ])
        code2 = self.peval(code)
        assert code2.body == [
            OpCode('load_const', W_Int(3)),
            OpCode('return'),
        ]

    def test_red_green_green(self):
        code = CodeObject('fn', [], [
            OpCode('load_local', 'a'),
            OpCode('load_const', W_Int(2)),
            OpCode('load_const', W_Int(3)),
            OpCode('mul'),
            OpCode('add'),
            OpCode('return'),
        ])
        code2 = self.peval(code)
        assert code2.body == [
            OpCode('load_local', 'a'),
            OpCode('load_const', W_Int(6)),
            OpCode('add'),
            OpCode('return'),
        ]

    def test_green_red_op(self):
        code = CodeObject('fn', [], [
            OpCode('load_const', W_Int(1)),
            OpCode('load_local', 'a'),
            OpCode('add'),
            OpCode('load_const', W_Int(2)),
            OpCode('mul'),
            OpCode('return'),
        ])
        code2 = self.peval(code)
        assert code2.body == code.body

    def test_green_br_if(self):
        code = CodeObject('fn', [], [
            OpCode('load_const', W_Int(1)),
            OpCode('br_if', 'then_0', 'else_0', 'endif_0'),
            OpCode('label', 'then_0'),
            OpCode('load_const', W_Int(2)),
            OpCode('return'),
            OpCode('label', 'else_0'),
            OpCode('load_const', W_Int(3)),
            OpCode('return'),
            OpCode('label', 'endif_0'),
            OpCode('abort', 'unreachable')
        ])
        code2 = self.peval(code)
        assert code2.body == [
            OpCode('label', 'then_0'),
            OpCode('load_const', W_Int(2)),
            OpCode('return'),
            OpCode('label', 'endif_0'),
            OpCode('abort', 'unreachable'),
        ]

    def test_red_br_if(self):
        code = CodeObject('fn', [], [
            OpCode('load_local', 'a'),
            OpCode('br_if', 'then_0', 'else_0', 'endif_0'),
            OpCode('label', 'then_0'),
            OpCode('load_const', W_Int(2)),
            OpCode('return'),
            OpCode('label', 'else_0'),
            OpCode('load_const', W_Int(3)),
            OpCode('return'),
            OpCode('label', 'endif_0'),
            OpCode('abort', 'unreachable')
        ])
        code2 = self.peval(code)
        assert code2.body == code.body

    def test_br_if_with_green_ops(self):
        code = CodeObject('fn', ['a'], [
            OpCode('load_local', 'a'),
            OpCode('br_if', 'then_0', 'else_0', 'endif_0'),
            OpCode('label', 'then_0'),
            OpCode('load_const', W_Int(2)),
            OpCode('load_const', W_Int(3)),
            OpCode('add'),
            OpCode('return'),
            OpCode('label', 'else_0'),
            OpCode('load_const', W_Int(6)),
            OpCode('return'),
            OpCode('label', 'endif_0'),
            OpCode('abort', 'unreachable')
        ])
        code2 = self.peval(code)
        assert code2.body == [
            OpCode('load_local', 'a'),
            OpCode('br_if', 'then_0', 'else_0', 'endif_0'),
            OpCode('label', 'then_0'),
            OpCode('load_const', W_Int(5)),
            OpCode('return'),
            OpCode('label', 'else_0'),
            OpCode('load_const', W_Int(6)),
            OpCode('return'),
            OpCode('label', 'endif_0'),
            OpCode('abort', 'unreachable')
        ]
        #
        w_f1 = W_Function('f1', code, {})
        w_f2 = W_Function('f2', code2, {})
        assert w_f1.call(W_Int(0)) == W_Int(6)
        assert w_f1.call(W_Int(1)) == W_Int(5)
        assert w_f2.call(W_Int(0)) == W_Int(6)
        assert w_f2.call(W_Int(1)) == W_Int(5)

    def test_green_locals(self):
        code = CodeObject('fn', [], [
            OpCode('load_const', W_Int(42)),
            OpCode('store_local_green', 'A'),
            OpCode('load_local_green', 'A'),
            OpCode('return'),
        ])
        code2 = self.peval(code)
        assert code2.body == [
            OpCode('load_const', W_Int(42)),
            OpCode('return'),
        ]

    def test_green_locals_sanity_check(self):
        code = CodeObject('fn', [], [
            OpCode('load_local', 'a'),
            OpCode('store_local_green', 'B'),
        ])
        with pytest.raises(AssertionError,
                           match='store_local_green called on a red'):
            self.peval(code)

    def test_unroll(self):
        w_tup = W_Tuple([W_Int(2), W_Int(3)])
        code = CodeObject('fn', [], [
            OpCode('load_const', W_Int(0)),
            OpCode('store_local', 'a'),
            OpCode('load_const', w_tup),
            OpCode('unroll'),
            OpCode('get_iter', '@iter0'),
            OpCode('label', 'for_0'),
            OpCode('for_iter', '@iter0', 'X', 'endfor_0'),
            OpCode('load_local', 'a'),
            OpCode('load_local_green', 'X'),
            OpCode('add'),
            OpCode('store_local', 'a'),
            OpCode('br', 'for_0'),
            OpCode('label', 'endfor_0'),
            OpCode('load_local', 'a'),
            OpCode('return'),
        ])
        code2 = self.peval(code)
        assert code2.body == [
            OpCode('load_const', W_Int(0)),
            OpCode('store_local', 'a'),
            OpCode('label', 'for_0'),

            # unrolled iteration 1
            OpCode('load_local', 'a'),
            OpCode('load_const', W_Int(2)),
            OpCode('add'),
            OpCode('store_local', 'a'),

            # unrolled iteration 2
            OpCode('load_local', 'a'),
            OpCode('load_const', W_Int(3)),
            OpCode('add'),
            OpCode('store_local', 'a'),

            OpCode('load_local', 'a'),
            OpCode('return')
        ]
