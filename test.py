#! /usr/bin/env python3 

class A(object):
    def __init__(self, value):
        self.a = value
        return
    
    def __eq__(self, __o: object) -> bool:
        print("__eq__")
        if (isinstance(__o, A) == True):
            if (self.a == __o.a):
                return True
        return False


if __name__ == "__main__":
    a1 = A(1)
    a2 = A(2)
    a3 = A(3)
    a4 = A(4)

    aList = [a1, a2, a4]

    print(a3 in aList)
    print(a2 in aList)
    print(a1 != a1)