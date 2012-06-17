from cStringIO import StringIO
from difflib import Differ
import sys
from pyclap import annotations, call, Positional as Pos, Option as Opt, wizard_call, Flag
from nose.tools import *


def eq_text(text1, text2):
    if text1 != text2:
        d = Differ()
        output = list(d.compare(text1.splitlines(1), text2.splitlines(1)))
        raise AssertionError("do not match:\n" + ''.join(output))



def exits(exit_code=None):

    def decorate(func):
        name = func.__name__
        def new_func(*arg, **kw):
            try:
                func(*arg, **kw)
            except SystemExit as e:
                if exit_code is not None and exit_code != e.code:
                    raise AssertionError("{0}() exited with code {2} (expected {3})".format(name, e.code, exit_code))
            else:
                message = "%s() did not exits" % name
                raise AssertionError(message)
        return make_decorator(func)(new_func)
    return decorate


def outputs(stdout=None, stderr=None):
    """Test must raise SystemExit with expected error if given.

    Example use::

      @exits()
      def test_raises_type_error():
          sys.exit()

      @raises('text')
      def test_that_fails_by_passing():
          pass

    If you want to test many assertions about exceptions in a single test,
    you may want to use `assert_raises` instead.
    """
    def redirect():
        old_stdout = None
        old_stderr = None
        if stdout is not None:
            old_stdout, sys.stdout = sys.stdout, StringIO()
        if stderr is not None:
            old_stderr, sys.stderr = sys.stderr, StringIO()
        return old_stdout, old_stderr


    def restore(old_stdout, old_stderr):
        if old_stdout is not None:
            sys.stdout, old_stdout = old_stdout, sys.stdout
        if old_stderr is not None:
            sys.stderr, old_stderr = old_stderr, sys.stderr

        err, out = None, None
        if stdout is not None:
            out = old_stdout.getvalue()
            old_stdout.close()
        if stderr is not None:
            err = old_stderr.getvalue()
            old_stderr.close()

        if out is not None:
            if isinstance(stdout, basestring):
                eq_text(stdout, out)
            else:
                ok_(stdout.match(out), "'\n{0}'\n do not match\n'{1}'".format(out, stdout.pattern))
        if err is not None:
            if isinstance(stderr, basestring):
                eq_text(err, stderr)
            else:
                ok_(stderr.match(err), "'\n{0}'\n do not match\n'{1}'".format(err, stderr.pattern))


    def decorate(func):
        def new_func(*arg, **kw):
            old_stdout, old_stderr = redirect()
            try:
                func(*arg, **kw)
            except:
                raise
            restore(old_stdout, old_stderr)
        return make_decorator(func)(new_func)
    return decorate



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



@raises(AssertionError)
def test_pos_2():
    @annotations(test_code=Pos("Test code (default {default})", 't'))
    def func(test_code='1234'):
        for i in (1,2,3):
           yield test_code

    call(func, arg_list=[])



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
