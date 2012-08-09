from cStringIO import StringIO
from difflib import Differ
import sys
from nose.tools import *


__author__ = 'Oleg'



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

