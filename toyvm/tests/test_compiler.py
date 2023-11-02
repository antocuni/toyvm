from toyvm.compiler import toy_compile
from toyvm.objects import W_Int, W_Tuple, w_None

class TestCompiler:

    def test_simple(self):
        w_func = toy_compile("""
        def foo():
            return 42
        """)
        assert w_func.name == 'foo'
        assert w_func.code.name == 'foo'
        assert w_func.code.equals("""
        0: load_const W_Int(42)
        1: return
        2: load_const w_None
        3: return
        """)
        assert w_func.call() == W_Int(42)

    def test_add_mul(self):
        w_func = toy_compile("""
        def foo():
            return 1 + 2 * 3
        """)
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
        assert w_func.call() == W_Int(7)

    def test_locals(self):
        w_func = toy_compile("""
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


    def test_func_params(self):
        w_func = toy_compile("""
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
        w_func = toy_compile("""
        def foo(a):
            if a:
                a = 42
            return a
        """)
        assert w_func.code.equals("""
        0: load_local a
        1: br_if 2 5 5
        2: load_const W_Int(42)
        3: store_local a
        4: br 5
        5: load_local a
        6: return
        7: load_const w_None
        8: return
        """)
        assert w_func.call(W_Int(0)) == W_Int(0)
        assert w_func.call(W_Int(1)) == W_Int(42)


    def test_if_else(self):
        w_func = toy_compile("""
        def foo(a):
            if a:
                b = 10
            else:
                b = 20
            return b
        """)
        assert w_func.code.equals("""\n
         0: load_local a
         1: br_if 2 5 7
         2: load_const W_Int(10)
         3: store_local b
         4: br 7
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
        w_func = toy_compile("""
        def foo():
            return (1, 2, 3)
        """)
        w_res = w_func.call()
        assert w_res == W_Tuple([W_Int(1), W_Int(2), W_Int(3)])


    def test_None(self):
        w_func = toy_compile("""
        def foo():
            pass
        """)
        w_res = w_func.call()
        assert w_res is w_None

    def test_print(self, capsys):
        w_func = toy_compile("""
        def foo():
            print('hello', 42)
        """)
        w_func.call()
        out, err = capsys.readouterr()
        assert out == 'hello 42\n'
