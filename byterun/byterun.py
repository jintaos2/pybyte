import collections
import operator
import dis
import sys
import types
import inspect 


class VirtualMachineError(Exception):
    pass


class VirtualMachine(object):
    def __init__(self):
        # 调用栈
        self.frames = []
        # 当前运行的帧            
        self.frame = None
        # frame 返回时的返回值           
        self.return_value = None    
        self.last_exception = None

    def run_code(self, code, global_names=None, local_names=None):
        """ 运行 Python 程序的入口，程序编译后生成 code_obj
        这里 code_obj 在参数 code 中
        run_code 根据输入的 code_obj 新建一个 frame 并开始运行
        """
        frame = self.make_frame(code, global_names=global_names, 
                local_names=local_names)
        self.run_frame(frame)
        
    # 新建一个帧，code 为 code_obj ；callargs 为函数调用时的参数
    def make_frame(self, code, callargs={}, global_names=None, local_names=None):
        if global_names is not None:
            global_names = global_names
            if local_names is None:
                local_names = global_names
        elif self.frames:
            global_names = self.frame.global_names
            local_names = {}
        else:
            global_names = local_names = {
                '__builtins__':__builtins__,
                '__name__': '__main__',
                '__doc__': None,
                '__package__':None,
            }
        # 将函数调用时的参数更新到局部变量空间中
        local_names.update(callargs)
        frame = Frame(code, global_names, local_names, self.frame)
        return frame
    
    # 调用栈压入 frame
    def push_frame(self, frame):
        self.frames.append(frame)
        self.frame = frame
    
    # 调用栈弹出 frame
    def pop_frame(self):
        self.frames.pop()
        if self.frames:
            self.frame = self.frames[-1]
        else:
            self.frame = None
    # 运行 frame
    def run_frame(self, frame):
            """运行帧直至它返回"""
            self.push_frame(frame)
            while True:
                byte_name, arguments = self.parse_byte_and_args()

                why = self.dispatch(byte_name, arguments)

                while why and frame.block_stack:
                    why = self.manage_block_stack(why)

                if why:
                    break

            self.pop_frame()

            if why == 'exception':
                exc, val, tb = self.last_exception
                e = exc(val)
                e.__traceback__ = tb
                raise e

            return self.return_value
    # 数据栈操作
    def top(self):
        return self.frame.stack[-1]

    def pop(self):
        return self.frame.stack.pop()

    def push(self, *vals):
        self.frame.stack.extend(vals)

    def popn(self, n):
        """弹出多个值"""
        if n:
            ret = self.frame.stack[-n:]
            self.frame.stack[-n:] = []
            return ret
        else:
            return []
    def parse_byte_and_args(self):
        f = self.frame
        opoffset = f.last_instruction
        # 取得要运行的指令
        byteCode = ord(f.code_obj.co_code[opoffset])
        f.last_instruction += 1
        # 指令名称
        byte_name = dis.opname[byteCode]
        # 指令码 <dis.HAVE_ARGUMENT 的都是无参数指令，其它则是有参数指令
        if byteCode >= dis.HAVE_ARGUMENT:
            # 取得后两字节的参数
            arg = f.code_obj.co_code[f.last_instruction:f.last_instruction+2] 
            f.last_instruction += 2
            # 参数第一个字节为参数实际低位，第二个字节为参数实际高位
            arg_val = ord(arg[0]) + (ord(arg[1]) * 256)
            if byteCode in dis.hasconst:   # 查找常量
                arg = f.code_obj.co_consts[arg_val]
            elif byteCode in dis.hasname:  # 查找变量名
                arg = f.code_obj.co_names[arg_val]
            elif byteCode in dis.haslocal: # 查找局部变量名
                arg = f.code_obj.co_varnames[arg_val]
            elif byteCode in dis.hasjrel:  # 计算跳转位置
                arg = f.last_instruction + arg_val
            else:
                arg = arg_val
            argument = [arg]
        else:
            argument = []

        return byte_name, argument
    def dispatch(self, byte_name, argument):
        why = None
        try:
            # 通过指令名得到对应的方法函数
            bytecode_fn = getattr(self, 'byte_%s' % byte_name, None)
            if bytecode_fn is None:
                # 这里对一元操作、二元操作和其它操作做了区分
                if byte_name.startswith('UNARY_'):
                    self.unaryOperator(byte_name[6:])
                elif byte_name.startswith('BINARY_'):
                    self.binaryOperator(byte_name[7:])
                else:
                    raise VirtualMachineError(
                        "unsupported bytecode type: %s" % byte_name
                    )
            else:
                why = bytecode_fn(*argument)
        except:
            # 存储运行指令时的异常信息
            self.last_exception = sys.exc_info()[:2] + (None,)
            why = 'exception'

        return why
    
BINARY_OPERATORS = {
    'POWER':    pow,
    'ADD':      operator.add,
    'SUBTRACT': operator.sub,
    'SUBSCR':   operator.getitem,
}
def binaryOperator(self, op):
    x, y = self.popn(2)
    self.push(self.BINARY_OPERATORS[op](x, y))
        
class Frame(object):
    def __init__(self, code_obj, global_names, local_names, prev_frame):
        self.code_obj = code_obj
        self.f_globals = global_names
        self.f_locals = local_names
        self.prev_frame = prev_frame
        # 数据栈
        self.stack = []
        # block 栈
        self.block_stack = []
        if prev_frame:
            self.builtin_names = prev_frame.builtin_names
        else:
            self.builtin_names = local_names['__builtins__']
            if hasattr(self.builtin_names, '__dict__'):
                self.builtin_names = self.builtin_names.__dict__
        # 最后运行的指令，初始为 0
        self.last_instruction = 0
        
        
class Function(object):
    # __slots__ 会固定对象的属性，无法再动态增加新的属性，这可以节省内存空间
    __slots__ = [
        'func_code', 'func_name', 'func_defaults', 'func_globals',
        'func_locals', 'func_dict', 'func_closure',
        '__name__', '__dict__', '__doc__',
        '_vm', '_func',
    ]

    def __init__(self, name, code, globs, defaults, closure, vm):
        """这部分不需要去深究，但是代码会尽量注释说明"""
        self._vm = vm
        # 这里的 code 即所调用函数的 code_obj
        self.func_code = code
        # 函数名会存在 code.co_name 中
        self.func_name = self.__name__ = name or code.co_name
        # 函数参数的默认值，如 func(a=5,b=3) ，则 func_defaults 为 (5,3)
        self.func_defaults = tuple(defaults)
        self.func_globals = globs
        self.func_locals = self._vm.frame.f_locals
        self.__dict__ = {}
        # 函数的闭包信息
        self.func_closure = closure
        self.__doc__ = code.co_consts[0] if code.co_consts else None

        # 有时我们需要用到真实 Python 的函数，下面的代码是为它准备的
        kw = {
            'argdefs': self.func_defaults,
        }
        # 为闭包创建 cell 对象
        if closure:
            kw['closure'] = tuple(make_cell(0) for _ in closure)
        self._func = types.FunctionType(code, globs, **kw)

    def __call__(self, *args, **kwargs):
        """每当调用一次函数，会创建一个新 frame 并运行"""
        # 通过 inspect 获得函数的参数
        callargs = inspect.getcallargs(self._func, *args, **kwargs)
        # 创建函数的帧
        frame = self._vm.make_frame(
            self.func_code, callargs, self.func_globals, {}
        )
        return self._vm.run_frame(frame)

def make_cell(value):
    """创建一个真实的 cell 对象"""
    # Thanks to Alex Gaynor for help with this bit of twistiness.
    fn = (lambda x: lambda: x)(value)
    return fn.__closure__[0]