import ast
import textwrap
from toyvm.opcode import CodeObject, OpCode
from toyvm.objects import W_Int, W_Str, W_Function

try:
    # add .pp() (pretty print) to all AST classes
    import spy.ast
except ImportError:
    pass


def toy_compile(src, filename='<unknown>'):
    src = textwrap.dedent(src)
    root = ast.parse(src, filename)
    assert len(root.body) == 1
    funcdef = root.body[0]
    assert isinstance(funcdef, ast.FunctionDef)
    comp = FuncDefCompiler(funcdef)
    return comp.compile()

class FuncDefCompiler:

    def __init__(self, funcdef):
        self.funcdef = funcdef
        self.code = CodeObject('fn', [])

    def compile(self):
        for stmt in self.funcdef.body:
            self.compile_stmt(stmt)
        return W_Function(self.funcdef.name, self.code)

    def emit(self, opname, *args):
        self.code.emit(OpCode(opname, *args))

    def unknown(self, node):
        raise Exception("Unknown node: {node.__class__.__name__}")

    def compile_stmt(self, stmt):
        name = stmt.__class__.__name__
        meth = getattr(self, f'stmt_{name}', self.unknown)
        meth(stmt)

    def compile_expr(self, expr):
        name = expr.__class__.__name__
        meth = getattr(self, f'expr_{name}', self.unknown)
        meth(expr)

    def stmt_Return(self, ret):
        self.compile_expr(ret.value)
        self.emit('return')

    def expr_Constant(self, expr):
        if isinstance(expr.value, int):
            w_value = W_Int(expr.value)
        elif isinstance(expr.value, str):
            w_value = W_Str(expr.value)
        else:
            assert False
        self.emit('load_const', w_value)
