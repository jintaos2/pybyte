from byterun import * 


what_to_execute = {
    "instructions": [("LOAD_VALUE", 0),
                     ("STORE_NAME", 0),
                     ("LOAD_VALUE", 1),
                     ("STORE_NAME", 1),
                     ("LOAD_NAME", 0),
                     ("LOAD_NAME", 1),
                     ("ADD_TWO_VALUES", None),
                     ("PRINT_ANSWER", None)],
    "numbers": [1, 2],
    "names":   ["a", "b"] }


interpreter = Interpreter()

interpreter.execute(what_to_execute)


def cond():
        x = 3
        if x < 5:
            return 'yes'
        else:
            return 'no'
        
        
a = cond.__code__.co_code 

print(list(a))

import dis 

print(dis.dis(cond))