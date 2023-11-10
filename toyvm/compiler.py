import ast
import textwrap
import symtable
from collections import Counter
from toyvm.opcode import CodeObject, OpCode
from toyvm.objects import W_Int, W_Str, W_Function, w_None, W_Module

try:
    # add .pp() (pretty print) to all AST classes
    import spy.ast
except ImportError:
    pass


def toy_compile(src, filename='<unknown>'):
    src = textwrap.dedent(src)
    comp = ModuleCompiler(src, filename)
    return comp.compile()

class ModuleCompiler:

    def __init__(self, src, filename):
        self.root = ast.parse(src, filename)
        self.w_mod = W_Module(globals_w={})
        self.w_mod.green_funcs = set()
        self.funcdefs = []
        for funcdef in self.root.body:
            assert isinstance(funcdef, ast.FunctionDef)
            self.funcdefs.append(funcdef)
        self.init_funcdefs()

    def init_funcdefs(self):
        for funcdef in self.funcdefs:
            if self.is_green(funcdef):
                self.w_mod.green_funcs.add(funcdef.name)

    def is_green(self, funcdef):
        for deco in funcdef.decorator_list:
            if isinstance(deco, ast.Name) and deco.id == 'green':
                return True
        return False

    def compile(self):
        for funcdef in self.funcdefs:
            comp = FuncDefCompiler(funcdef, self.w_mod)
            w_func = comp.compile()
            if w_func.name in self.w_mod.green_funcs:
                w_func.is_green = True
            self.w_mod.globals_w[w_func.name] = w_func
        return self.w_mod


class FuncDefCompiler:

    def __init__(self, funcdef, w_mod):
        self.funcdef = funcdef
        self.w_mod = w_mod
        self.code = CodeObject(funcdef.name, [])
        self.label_counter = 0
        self.argnames = [a.arg for a in funcdef.args.args]
        self.compute_local_vars()

    def compute_local_vars(self):
        self.local_vars = set()
        self.local_vars.update(set(self.argnames))
        for node in ast.walk(self.funcdef):
            if isinstance(node, ast.Assign):
                assert len(node.targets) == 1
                varname = self.get_Name(node.targets[0])
                self.local_vars.add(varname)
            elif isinstance(node, ast.For):
                varname = self.get_Name(node.target)
                self.local_vars.add(varname)

    def new_label(self, stem):
        n = self.label_counter
        self.label_counter += 1
        return f'{stem}_{n}'

    def new_labels(self, *stems):
        n = self.label_counter
        self.label_counter += 1
        return [f'{stem}_{n}' for stem in stems]

    def emit(self, opname, *args):
        op = OpCode(opname, *args)
        self.code.emit(op)
        return op

    def pc(self):
        return len(self.code.body)

    def compile(self):
        self.compile_many_stmts(self.funcdef.body)
        self.emit('load_const', w_None)
        self.emit('return')
        return W_Function(self.funcdef.name, self.argnames, self.code,
                          self.w_mod.globals_w)

    def compile_many_stmts(self, stmts):
        for stmt in stmts:
            self.compile_stmt(stmt)

    def unknown_stmt(self, stmt):
        raise NotImplementedError(f"stmt_{stmt.__class__.__name__}")

    def unknown_expr(self, expr):
        raise NotImplementedError(f"expr_{expr.__class__.__name__}")

    def compile_stmt(self, stmt):
        name = stmt.__class__.__name__
        meth = getattr(self, f'stmt_{name}', self.unknown_stmt)
        meth(stmt)

    def compile_expr(self, expr):
        name = expr.__class__.__name__
        meth = getattr(self, f'expr_{name}', self.unknown_expr)
        meth(expr)

    def stmt_Pass(self, stmt):
        pass

    def stmt_Return(self, ret):
        self.compile_expr(ret.value)
        self.emit('return')

    def stmt_Assign(self, stmt):
        assert len(stmt.targets) == 1
        name = self.get_Name(stmt.targets[0])
        assert name in self.local_vars
        self.compile_expr(stmt.value)
        if name.isupper():
            self.emit('store_local_green', name)
        else:
            self.emit('store_local', name)

    def stmt_If(self, stmt):
        if stmt.orelse:
            self._stmt_If_then_else(stmt)
        else:
            self._stmt_If_then(stmt)

    def _stmt_If_then(self, stmt):
        then, endif = self.new_labels('then', 'endif')
        self.compile_expr(stmt.test)
        br_if = self.emit('br_if', then, endif, endif)
        self.emit('label', then)
        self.compile_many_stmts(stmt.body)
        self.emit('label', endif)

    def _stmt_If_then_else(self, stmt):
        then, else_, endif = self.new_labels('then', 'else', 'endif')
        self.compile_expr(stmt.test)
        br_if = self.emit('br_if', then, else_, endif)
        self.emit('label', then)
        self.compile_many_stmts(stmt.body)
        br = self.emit('br', endif)
        self.emit('label', else_)
        self.compile_many_stmts(stmt.orelse)
        self.emit('label', endif)

    def stmt_Expr(self, stmt):
        self.compile_expr(stmt.value)
        self.emit('pop')

    def stmt_For(self, stmt):
        for_, itername, endfor = self.new_labels('for', '@iter', 'endfor')
        target = self.get_Name(stmt.target)
        self.compile_expr(stmt.iter)
        self.emit('get_iter', itername)
        self.emit('label', for_)
        self.emit('for_iter', itername, target, endfor)
        self.compile_many_stmts(stmt.body)
        self.emit('br', for_)
        self.emit('label', endfor)

    def get_w_const(self, expr):
        assert isinstance(expr, ast.Constant)
        if isinstance(expr.value, int):
            return W_Int(expr.value)
        elif isinstance(expr.value, str):
            return W_Str(expr.value)
        else:
            assert False

    def get_Name(self, expr):
        assert isinstance(expr, ast.Name)
        return expr.id

    def expr_Constant(self, expr):
        w_const = self.get_w_const(expr)
        self.emit('load_const', w_const)

    def expr_BinOp(self, expr):
        self.compile_expr(expr.left)
        self.compile_expr(expr.right)
        op = expr.op.__class__.__name__
        if op == 'Add':
            self.emit('add')
        elif op == 'Mult':
            self.emit('mul')
        else:
            self.unknown(expr.op)

    def expr_Compare(self, expr):
        assert len(expr.ops) == 1
        assert len(expr.comparators) == 1
        self.compile_expr(expr.left)
        self.compile_expr(expr.comparators[0])
        op = expr.ops[0].__class__.__name__
        self.emit(op.lower()) # e.g. 'lt'

    def expr_Name(self, expr):
        name = expr.id
        if name in self.local_vars:
            if name.isupper():
                self.emit('load_local_green', name)
            else:
                self.emit('load_local', name)
        else:
            if name in self.w_mod.green_funcs:
                self.emit('load_nonlocal_green', name)
            else:
                self.emit('load_nonlocal', name)

    def expr_Tuple(self, expr):
        for item in expr.elts:
            self.compile_expr(item)
        self.emit('make_tuple', len(expr.elts))

    def expr_Call(self, expr):
        if (isinstance(expr.func, ast.Name) and
            expr.func.id in ('print', 'UNROLL')):
            self.expr_Call_builtin(expr)
            return
        #
        self.compile_expr(expr.func)
        for arg in expr.args:
            self.compile_expr(arg)
        self.emit('call', len(expr.args))

    def expr_Call_builtin(self, expr):
        funcname = self.get_Name(expr.func)
        for arg in expr.args:
            self.compile_expr(arg)
        if funcname == 'print':
            self.emit('print', len(expr.args))
        elif funcname == 'UNROLL':
            assert len(expr.args) == 1
            self.emit('unroll')
        else:
            assert False, f'unsupported function: {funcname}'
