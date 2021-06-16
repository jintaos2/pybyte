

class Interpreter:

    def __init__(self):
        self.stack = []
        self.environment = {}
        
    def STORE_NAME(self, name):
        value = self.stack.pop()
        self.environment[name] = value 
    def LOAD_NAME(self, name):
        value = self.environment[name]
        self.stack.append(value)

    def LOAD_VALUE(self, number):
        self.stack.append(number)

    def ADD_TWO_VALUES(self):
        first_num = self.stack.pop()
        second_num = self.stack.pop()
        total = first_num + second_num
        self.stack.append(total)

    def PRINT_ANSWER(self):
        answer = self.stack.pop()
        print(answer)
        
    def parse_argument(self, instruction, argument, what_to_execute):
        numbers = ['LOAD_VALUE'] 
        names = ['LOAD_NAME', 'STORE_NAME']
        if instruction in numbers:
            argument = what_to_execute['numbers'][argument]
        if instruction in names:
            argument = what_to_execute['names'][argument]
        return argument

    def execute(self, what_to_execute):
        instructions = what_to_execute["instructions"]
        for each_step in instructions:
            instruction, argument = each_step
            argument = self.parse_argument(instruction, argument, what_to_execute)
            bytecode_method = getattr(self, instruction)
            if argument is None:
                bytecode_method()
            else:
                bytecode_method(argument)