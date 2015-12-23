from c3speakers import *


def test_helloworld():
    x = hello_world()
    assert x == 'Hello, world!'


help(hello_world())
