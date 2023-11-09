import pytest
from toyvm.compiler import toy_compile
from toyvm.rainbow import peval
from toyvm.objects import W_Int, W_Tuple, w_None, W_Function

COMPILATION_MODES = [
    pytest.param('interp', marks=[pytest.mark.interp]),
    pytest.param('rainbow', marks=[pytest.mark.rainbow]),
]

class TestCompiler:

    @pytest.fixture(autouse=True, params=COMPILATION_MODES)
    def compilation_mode(self, request):
        self.mode = request.param

    def compile(self, src):
        self.w_mod = toy_compile(src)
        w_func = list(self.w_mod.globals_w.values())[0] # the first func
        self.w_func = w_func
        if self.mode == 'rainbow':
            self.w_func2 = peval(self.w_func)
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
        load_const W_Int(42)
        return
        load_const w_None
        return
        """)
        assert w_func.call() == W_Int(42)

    def test_add_mul(self):
        w_func = self.compile("""
        def foo():
            return 1 + 2 * 3
        """)
        if self.mode == 'interp':
            assert w_func.code.equals("""
            load_const W_Int(1)
            load_const W_Int(2)
            load_const W_Int(3)
            mul
            add
            return
            load_const w_None
            return
            """)
        else:
            assert w_func.code.equals("""
            load_const W_Int(7)
            return
            load_const w_None
            return
            """)
        assert w_func.call() == W_Int(7)

    def test_locals(self):
        w_func = self.compile("""
        def foo():
            a = 4
            return a
        """)
        assert w_func.code.equals("""
        load_const W_Int(4)
        store_local a
        load_local a
        return
        load_const w_None
        return
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
            load_const W_Int(4)
            store_local_green A
            load_local_green A
            return
            load_const w_None
            return
            """)
        else:
            assert w_func.code.equals("""
            load_const W_Int(4)
            return
            load_const w_None
            return
            """)
        assert w_func.call() == W_Int(4)

    def test_func_params(self):
        w_func = self.compile("""
        def foo(a, b):
            return a + b
        """)
        assert w_func.code.equals("""
        load_local a
        load_local b
        add
        return
        load_const w_None
        return
        """)
        assert w_func.call(W_Int(10), W_Int(20)) == W_Int(30)

    def test_if_then(self):
        w_func = self.compile("""
        def foo(a):
            if a:
                a = 42
            return a
        """)
        assert w_func.code.equals("""
          load_local a
          br_if then_0 endif_0 endif_0
        then_0:
          load_const W_Int(42)
          store_local a
        endif_0:
          load_local a
          return
          load_const w_None
          return
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
          load_local a
          br_if then_0 else_0 endif_0
        then_0:
          load_const W_Int(10)
          store_local b
          br endif_0
        else_0:
          load_const W_Int(20)
          store_local b
        endif_0:
          load_local b
          return
          load_const w_None
          return
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
           load_local tup
           get_iter @iter_0
         for_0:
           for_iter @iter_0 x endfor_0
           load_local x
           print 1
           pop
           br for_0
         endfor_0:
           load_const w_None
           return
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

    def test_nested_for_unroll(self):
        w_func = self.compile(r"""
        def foo():
            COLS = ("a", "b")
            ROWS = ("1", "2", "3")
            OUT = ""
            for R in UNROLL(ROWS):
                for C in UNROLL(COLS):
                    OUT = OUT + C + R + " "
                OUT = OUT + "-- "
            return OUT
        """)
        w_res = w_func.call()
        assert w_res.value == "a1 b1 -- a2 b2 -- a3 b3 -- "
        if self.mode == 'rainbow':
            assert w_func.code.equals("""
            for_0:
            for_1#0:
            for_1#3:
            for_1#6:
              load_const W_Str('a1 b1 -- a2 b2 -- a3 b3 -- ')
              return
              load_const w_None
              return
            """)

    def test_nested_for_unroll_with_if(self):
        w_func = self.compile(r"""
        def foo(flag):
            COLS = ("a", "b")
            ROWS = ("1", "2")
            out = ""
            for R in UNROLL(ROWS):
                out = out + R
                if flag:
                    for C in UNROLL(COLS):
                        out = out + C
                else:
                    out = out + "-"
            return out
        """)
        w_res = w_func.call(W_Int(1))
        assert w_res.value == "1ab2ab"
        #
        w_res = w_func.call(W_Int(0))
        assert w_res.value == "1-2-"

    def test_function_calls(self):
        w_foo = self.compile("""
        def foo(x, y):
            return inc(x) * inc(y)

        def inc(x):
            return x + 1
        """)
        assert w_foo.name == 'foo'
        w_inc = self.w_mod.globals_w['inc']
        assert w_inc.call(W_Int(2)) == W_Int(3)
        assert w_foo.call(W_Int(2), W_Int(9)) == W_Int(30)
