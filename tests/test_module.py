from pyclap import annotations, call, Positional as Pos, Option as Opt, Flag, wizard_call
import sys
from nose_tools import exits, outputs
from nose.tools import *

commands = ['command1', 'command2']

@annotations(positional_arg=Pos("Positional argument"),
             optional_arg=Opt("Optional argument {default}"))
def command1(positional_arg, optional_arg='test'):
    """
    test command 1
    """
    return positional_arg, optional_arg


@annotations(positional_arg=Pos("Positional argument"),
             optional_arg=Opt("Optional argument {default}"),
             flag_arg=Flag("Flag argument"))
def command2(positional_arg, optional_arg='test', flag_arg=False):
    """
    test command 2
    """
    return positional_arg, optional_arg, flag_arg

######################################################################################################
@outputs(stderr=
"""usage: noserunner.py [-h] {command1,command2} ...
noserunner.py: error: too few arguments
""")
@exits(2)
def test_doc_1():
    call(arg_list=[])



######################################################################################################
@outputs(stdout=
"""usage: noserunner.py [-h] {command1,command2} ...

optional arguments:
  -h, --help           show this help message and exit

subcommands:
  {command1,command2}
    command1
    command2
""")
@exits()
def test_doc_2():
    call(arg_list=['-h'])


######################################################################################################
def test_arg_1():
    ns, output = call(arg_list=['command1','1234'])
    eq_(ns['_cmd_name_'], 'command1')
    eq_(ns['positional_arg'], '1234')
    eq_(ns['optional_arg'], 'test')
