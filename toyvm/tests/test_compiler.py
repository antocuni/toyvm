import pytest
from toyvm.compiler import toy_compile
from toyvm.rainbow import peval
from toyvm.objects import W_Int, W_Tuple, w_None, W_Function

class TestCompiler:

    @pytest.fixture(autouse=True, params=['interp', 'rainbow'])
    def compilation_mode(self, request):
        self.mode = request.param

    def compile(self, src):
        self.w_func = toy_compile(src)
        if self.mode == 'rainbow':
            code2 = peval(self.w_func.code)
            self.w_func2 = W_Function(
                self.w_func.name,
                self.w_func.argnames,
                code2)
            return self.w_func2
        else:
            return self.w_func

    def test_simple(self):
        w_func = self.compile("""
        def foo():
            return 42
        """)
        assert w_func.name == 'foo'
        assert w_func.code.name in ('foo', 'foo<peval>')
        assert w_func.code.equals("""
        0: load_const W_Int(42)
        1: return
        2: load_const w_None
        3: return
        """)
        assert w_func.call() == W_Int(42)

    def test_add_mul(self):
        w_func = self.compile("""
        def foo():
            return 1 + 2 * 3
        """)
        if self.mode == 'interp':
            assert w_func.code.equals("""
            0: load_const W_Int(1)
            1: load_const W_Int(2)
            2: load_const W_Int(3)
            3: mul
            4: add
            5: return
            6: load_const w_None
            7: return
            """)
        else:
            assert w_func.code.equals("""
            0: load_const W_Int(7)
            1: return
            2: load_const w_None
            3: return
            """)
        assert w_func.call() == W_Int(7)

    def test_locals(self):
        w_func = self.compile("""
        def foo():
            a = 4
            return a
        """)
        assert w_func.code.equals("""
        0: load_const W_Int(4)
        1: store_local a
        2: load_local a
        3: return
        4: load_const w_None
        5: return
        """)
        assert w_func.call() == W_Int(4)

    def test_locals_green(self):
        w_func = self.compile("""
        def foo():
            A = 4
            return A
        """)
        if self.mode == 'interp':
            assert w_func.code.equals("""
            0: load_const W_Int(4)
            1: store_local_green A
            2: load_local_green A
            3: return
            4: load_const w_None
            5: return
            """)
        else:
            assert w_func.code.equals("""
            0: load_const W_Int(4)
            1: return
            2: load_const w_None
            3: return
            """)
        assert w_func.call() == W_Int(4)

    def test_func_params(self):
        w_func = self.compile("""
        def foo(a, b):
            return a + b
        """)
        assert w_func.code.equals("""
        0: load_local a
        1: load_local b
        2: add
        3: return
        4: load_const w_None
        5: return
        """)
        assert w_func.call(W_Int(10), W_Int(20)) == W_Int(30)

    def test_if_then(self):
        w_func = self.compile("""
        def foo(a):
            if a:
                a = 42
            return a
        """)
        print()
        w_func.code.pp()
        import pdb;pdb.set_trace()
        assert w_func.code.equals("""
         0: load_local a
         1: br_if then_0 else_0 endif_0
         2: label then_0
         3: load_const W_Int(42)
         4: store_local a
         5: label else_0
         6: label endif_0
         7: load_local a
         8: return
         9: load_const w_None
        10: return
        """)
        assert w_func.call(W_Int(0)) == W_Int(0)
        assert w_func.call(W_Int(1)) == W_Int(42)

    def test_if_else(self):
        w_func = self.compile("""
        def foo(a):
            if a:
                b = 10
            else:
                b = 20
            return b
        """)
        assert w_func.code.equals("""\n
         0: load_local a
         1: br_if then_0 else_0 endif_0
         2: label then_0
         2: load_const W_Int(10)
         3: store_local b
         4: br endif_0
         0: label else_0
         5: load_const W_Int(20)
         6: store_local b
         7: load_local b
         8: return
         9: load_const w_None
        10: return
        """)
        assert w_func.call(W_Int(0)) == W_Int(20)
        assert w_func.call(W_Int(1)) == W_Int(10)

    def test_tuple(self):
        w_func = self.compile("""
        def foo():
            return (1, 2, 3)
        """)
        w_res = w_func.call()
        assert w_res == W_Tuple([W_Int(1), W_Int(2), W_Int(3)])

    def test_compare(self):
        w_func = self.compile("""
        def foo(a, b):
            return a < b
        """)
        w_res = w_func.call(W_Int(2), W_Int(3))
        assert w_res.value

    def test_None(self):
        w_func = self.compile("""
        def foo():
            pass
        """)
        w_res = w_func.call()
        assert w_res is w_None

    def test_print(self, capsys):
        w_func = self.compile("""
        def foo():
            print('hello', 42)
        """)
        w_func.call()
        out, err = capsys.readouterr()
        assert out == 'hello 42\n'

    def test_for(self, capsys):
        w_func = self.compile("""
        def foo(tup):
            for x in tup:
                print(x)
        """)
        assert w_func.code.equals("""
         0: load_local tup
         1: get_iter @iter0
         2: for_iter @iter0 x 7
         3: load_local x
         4: print 1
         5: pop
         6: br 2
         7: load_const w_None
         8: return
        """)
        w_tup = W_Tuple([W_Int(1), W_Int(2), W_Int(3)])
        w_func.call(w_tup)
        out, err = capsys.readouterr()
        assert out == '1\n2\n3\n'

    def test_for_unroll(self):
        w_func = self.compile("""
        def foo():
            TUP = (1, 2, 3)
            a = 0
            for X in UNROLL(TUP):
                a = a + X
            return a
        """)
        w_res = w_func.call()
        assert w_res == W_Int(6)

    @pytest.mark.skip("WIP")
    def test_red_if_inside_for_unroll(self):
        w_func = self.compile("""
        def foo():
            TUP = (5, 7, 1000)
            a = 0
            for X in UNROLL(TUP):
                if a < 10:
                    a = a + X
            return a
        """)
        w_res = w_func.call()
        assert w_res == W_Int(12)
