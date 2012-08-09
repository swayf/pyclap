
from pyclap import annotations, call, Positional as Pos, Option as Opt, Flag, wizard_call
from nose_tools import outputs, exits
from nose.tools import *

########################################################################################################################

def test_pos_1():
    @annotations(test_code=Pos("Test code (default {default})"))
    def func(test_code='1234'):
        for i in (1,2,3):
           yield test_code

    ns, output = call(func, arg_list=[])
    eq_(ns['test_code'], '1234')
    eq_(output, ['1234','1234','1234'])

    ns, output = call(func, arg_list=['4321'])
    eq_(ns['test_code'], '4321')
    eq_(output, ['4321','4321','4321'])


########################################################################################################################

@raises(AssertionError)
def test_pos_2():
    @annotations(test_code=Pos("Test code (default {default})", 't'))
    def func(test_code='1234'):
        for i in (1,2,3):
           yield test_code

    call(func, arg_list=[])


########################################################################################################################

@outputs(stderr=
"""usage: noserunner.py [-h] [-t TEST_OPT_1] [--test-opt-2] test_pos
noserunner.py: error: too few arguments
""")
@exits(exit_code=2)
def test_output_1():
    @annotations(test_pos=Pos("test2 help message"),
                 test_opt_1=Opt("Test help (default {default})", 't'),
                 test_opt_2=Flag("Test help 2"))
    def func(test_pos, test_opt_1='1234', test_opt_2=False):
        pass

    call(func, arg_list=[])


########################################################################################################################

@outputs(stdout=
"""usage: noserunner.py [-h] [-t TEST_OPT_1] [--test-opt-2] test_pos

positional arguments:
  test_pos              test2 help message

optional arguments:
  -h, --help            show this help message and exit
  -t TEST_OPT_1, --test-opt-1 TEST_OPT_1
                        Test help (default 1234)
  --test-opt-2          Test help 2
""")
@exits()
def test_output_2():
    @annotations(test_pos=Pos("test2 help message"),
                 test_opt_1=Opt("Test help (default {default})", 't'),
                 test_opt_2=Flag("Test help 2"))
    def func(test_pos, test_opt_1='1234', test_opt_2=False):
        pass

    call(func, arg_list=['-h'])

########################################################################################################################

@exits(exit_code=2)
@outputs(stderr=
"""usage: noserunner.py [-h] [-t TEST2_CODE] {test_1,test_2,test_3}
noserunner.py: error: too few arguments
""")
def test_output_3():
    @annotations(test2_arg=Pos("test2 help message", choices=('test_1','test_2','test_3')),
                 test2_code=Opt("Test code (default {default})", 't'))
    def func(test2_arg, test2_code='1234'):
        return test2_arg, test2_code

    call(func, arg_list=[])

########################################################################################################################
@exits(exit_code=2)
@outputs(stderr=
"""usage: noserunner.py [-h] [-t {test_1,test_2,test_3}] test2_arg
noserunner.py: error: too few arguments
""")
def test_output_4():
    @annotations(test2_arg=Pos("test2 help message"),
                 test2_code=Opt("Test code (default {default})", 't', choices=('test_1','test_2','test_3')))
    def func(test2_arg, test2_code='test_1'):
        return test2_arg, test2_code

    call(func, arg_list=[])


########################################################################################################################
@outputs(stdout=
"""usage: noserunner.py [-h] [-t TEST_OPT_1] [--test-opt-2] test_pos

positional arguments:
  test_pos

optional arguments:
  -h, --help            show this help message and exit
  -t TEST_OPT_1, --test-opt-1 TEST_OPT_1
                        [1234]
  --test-opt-2
""")
@exits()
def test_output_5():
    @annotations(test_pos=Pos(),
                 test_opt_1=Opt(abbrev='t'),
                 test_opt_2=Flag())
    def func(test_pos, test_opt_1='1234', test_opt_2=False):
        pass

    call(func, arg_list=['-h'])


########################################################################################################################

def test_interface_1():
    class Interface(object):
        commands=['search']
        def __init__(self):
            self.result = ' 5555 '

        @annotations(regex=Pos("Regular Expression"))
        def search(self, regex):
            return self.result + regex

    ns, output = call(Interface, arg_list=['search', 'test'])
    eq_(output[0], ' 5555 test')


########################################################################################################################
@outputs(stderr=
"""usage: noserunner.py search [-h] [-f] regex
noserunner.py search: error: too few arguments
""")
@exits(2)
def test_interface_2():

    class Interface(object):
        commands=['search']
        def __init__(self):
            self.result = ' 5555 '

        @annotations(regex=Pos("Regular Expression"),
                     test_flag=Flag("Flag","f"))
        def search(self, regex, test_flag=False):
            return self.result + regex, test_flag


    call(Interface, arg_list=['search', '-f'])

########################################################################################################################
def test_obj_interface_1():
    class Interface(object):
        commands=['search']
        def __init__(self):
            self.result = ' 5555 '

        @annotations(regex=Pos("Regular Expression"))
        def search(self, regex):
            return self.result + regex

    ns, output = call(Interface(), arg_list=['search', 'test'])
    eq_(output[0], ' 5555 test')


########################################################################################################################
@outputs(stderr=
"""usage: noserunner.py search [-h] [-f] regex
noserunner.py search: error: too few arguments
""")
@exits(2)
def test_interface_2():

    class Interface(object):
        commands=['search']
        def __init__(self):
            self.result = ' 5555 '

        @annotations(regex=Pos("Regular Expression"),
                     test_flag=Flag("Flag","f"))
        def search(self, regex, test_flag=False):
            return self.result + regex, test_flag


    call(Interface(), arg_list=['search', '-f'])


########################################################################################################################
def test_wizard_1():
    @annotations(test2_arg=Pos("test2 help message"),
                 test2_code=Opt("Test code (default {default})", 't', choices=('test_1','test_2','test_3')))
    def func(test2_arg, test2_code='1234'):
        return test2_arg, test2_code

    def wizard_callback(name, annotation, default):
        if name == 'test2_arg':
            return '7890'
        elif name == 'test2_code':
            return 'test_2'

    ns, output = wizard_call(func, wizard_callback, arg_list=[])
    eq_(ns['test2_arg'], '7890')
    eq_(ns['test2_code'], 'test_2')

