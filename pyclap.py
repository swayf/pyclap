__version__ = '0.1.0'

#TODO: add possibility to define defaults as function or class member of current instance
#TODO: add possibility to define substitutions context for help


__all__=['call', 'annotations', 'Annotation', 'Positional', 'Option', 'Flag', 'iterable']

import keyword
import re, sys, inspect, argparse

if sys.version >= '3':
    from inspect import getfullargspec
else:
    class getfullargspec(object):
        """A quick and dirty replacement for getfullargspec for Python 2.X"""
        def __init__(self, f):
            self.args, self.varargs, self.varkw, self.defaults = \
                inspect.getargspec(f)
            self.annotations = getattr(f, '__annotations__', {})


def annotations(**ann):
    """
    Returns a decorator annotating a function with the given annotations.
    This is a trick to support function annotations in Python 2.X.
    """
    def annotate(f):
        fas = getfullargspec(f)
        args = fas.args
        if fas.varargs:
            args.append(fas.varargs)
        if fas.varkw:
            args.append(fas.varkw)
        for argname in ann:
            if argname not in args:
                raise NameError('Annotating non-existing argument: {0}'.format(argname))
        f.__annotations__ = ann
        return f
    return annotate



class Annotation(object):
    def __init__(self, help=None, kind="positional", abbrev=None, type=None,
                 choices=None, metavar=None, default=None):
        assert kind in ('positional', 'option', 'flag'), kind
        if kind == "positional":
            assert abbrev is None, abbrev
        self.help = help
        self.kind = kind
        self.abbrev = abbrev
        self.type = type
        self.choices = choices
        self.metavar = metavar
        self.default = default


    @classmethod
    def from_(cls, obj):
        """Helper to convert an object into an annotation, if needed"""
        if Annotation.is_annotation(obj):
            return obj # do nothing
        elif isinstance(obj, dict):
            return cls(**obj)
        elif iterable(obj):
            return cls(*obj)
        return cls(obj)


    @staticmethod
    def is_annotation(obj):
        """
        An object is an annotation object if it has the attributes
        help, kind, abbrev, type, choices, metavar.
        """
        return (hasattr(obj, 'help') and hasattr(obj, 'kind') and
                hasattr(obj, 'abbrev') and hasattr(obj, 'type') and
                hasattr(obj, 'choices') and hasattr(obj, 'metavar') and
                hasattr(obj, 'default'))



class Positional(Annotation):
    def __init__(self, help=None, abbrev=None, type=None, choices=None, metavar=None):
        #noinspection PyArgumentEqualDefault
        super(Positional, self).__init__(help, 'positional', abbrev, type, choices, metavar)



class Option(Annotation):
    def __init__(self, help=None, abbrev=None, type=None, choices=None, metavar=None, default=None):
        super(Option, self).__init__(help, 'option', abbrev, type, choices, metavar, default)



class Flag(Annotation):
    def __init__(self, help=None, abbrev=None, type=None, choices=None, metavar=None):
        super(Flag, self).__init__(help, 'flag', abbrev, type, choices, metavar)



class DictType(object):
    def __init__(self, value_type=None):
        self.value_type = value_type or (lambda x:x)


    def __call__(self, string):
        match = re.match(r'([a-zA-Z_]\w*)=', string)
        if match:
            name = match.group(1)
            value = string[len(name)+1:]
            return name, (self.value_type(value) if self.value_type else value)
        else:
            msg = "{0!r} is not a key=value".format(string)
            raise argparse.ArgumentTypeError(msg)



class ArgsAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest,
                 nargs=None,
                 const=None,
                 default=None,
                 type=None,
                 choices=None,
                 required=False,
                 help=None,
                 metavar=None):
        argparse.Action.__init__(self,
                                 option_strings=option_strings,
                                 dest=dest,
                                 nargs=nargs,
                                 const=None,
                                 default=default,
                                 type=type,
                                 choices=choices,
                                 required=required,
                                 help=help,
                                 metavar=metavar,
                                 )
        self.varkw = const


    def __call__(self, parser, namespace, values, option_string=None):
        # Do some arbitrary processing of the input values
        dict_type = DictType()
        args = []
        kwargs = []
        for value in values:
            try:
                kwargs.append(dict_type(value))
            except argparse.ArgumentTypeError:
                args.append(value)

        # Save the results in the namespace using the destination
        # variable given to our constructor.
        setattr(namespace, self.dest, args)
        kwargs_values = getattr(namespace, self.varkw, {})
        kwargs_values.update(dict(kwargs))
        setattr(namespace, self.varkw, kwargs_values)



class KwargsAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest,
                 nargs=None,
                 const=None,
                 default=None,
                 type=None,
                 choices=None,
                 required=False,
                 help=None,
                 metavar=None):
        argparse.Action.__init__(self,
                                 option_strings=option_strings,
                                 dest=dest,
                                 nargs=nargs,
                                 const=const,
                                 default=default,
                                 type=type,
                                 choices=choices,
                                 required=required,
                                 help=help,
                                 metavar=metavar,
                                 )


    def __call__(self, parser, namespace, values, option_string=None):
        # Do some arbitrary processing of the input values
        if isinstance(values, list):
            values = dict(values)
        elif not isinstance(values, dict):
            values = dict([values])
        # Save the results in the namespace using the destination
        # variable given to our constructor.
        kwargs_values = getattr(namespace, self.dest, {})
        kwargs_values.update(values)
        setattr(namespace, self.dest, kwargs_values)



class CommandSpec(object):
    NONE = object()

    @classmethod
    def get_arg_spec(cls, callable_obj):
        """Given a callable return an object with attributes .args, .varargs,
        .varkw, .defaults. It tries to do the "right thing" with functions,
        methods, classes and generic callables."""
        if inspect.isfunction(callable_obj):
            arg_spec = getfullargspec(callable_obj)
        elif inspect.ismethod(callable_obj):
            arg_spec = getfullargspec(callable_obj)
            del arg_spec.args[0] # remove first argument
        elif inspect.isclass(callable_obj):
            if callable_obj.__init__ is object.__init__: # to avoid an error
                arg_spec = getfullargspec(lambda self: None)
            else:
                arg_spec = getfullargspec(callable_obj.__init__)
            del arg_spec.args[0] # remove first argument
        elif hasattr(callable_obj, '__call__'):
            arg_spec = getfullargspec(callable_obj.__call__)
            del arg_spec.args[0] # remove first argument
        else:
            raise TypeError('Could not determine the signature of ' + str(callable_obj))
        return arg_spec



class CallableCommandSpec(CommandSpec):

    def __init__(self, obj):
        self.arg_spec = self.get_arg_spec(obj)
        self.obj = obj

        defaults = self.arg_spec.defaults or ()
        n_args = len(self.arg_spec.args)
        n_defaults = len(defaults)

        self.defaults = (self.NONE,) * (n_args - n_defaults) + defaults
        self.vars = self.arg_spec.args
        self.varargs = self.arg_spec.varargs
        self.varkw = self.arg_spec.varkw
        self.annotations = dict()
        for key in self.vars + [self.varargs] + [self.varkw]:
            if key:
                self.annotations[key] = Annotation.from_(self.arg_spec.annotations.get(key, ()))


    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)


    def __getattr__(self, item):
        return getattr(self.obj, item)



class ClassCommandsSpec(CommandSpec):

    def __init__(self, klass, commands):
        self.commands = commands
        self.klass = klass
        self.instances_cache = {}
        self.command_spec_cache = {}
        self.arg_spec = self.get_arg_spec(klass)
        self.common_meta = CallableCommandSpec(klass.__init__)


    def _get_instance(self, constructor_args):
        if constructor_args not in self.instances_cache:
            obj = self.klass(*constructor_args)
            if not hasattr(obj, '__enter__'):
                self.klass.__enter__ = lambda s: None
                self.klass.__exit__ = lambda s, et, ex, tb: None
            self.instances_cache[constructor_args] = obj
        return self.instances_cache[constructor_args]


    def _get_command_spec(self, command):
        if command not in self.command_spec_cache:
            self.command_spec_cache[command] = CallableCommandSpec(getattr(self.klass, command))
        return self.command_spec_cache[command]


    def __getattr__(self, item):
        if item not in self.commands:
            return getattr(self.klass, item)
        else:
            def wrapper(*args, **kwargs):
                constructor_args = args[:len(self.common_meta.vars)]
                rest_args = args[len(self.common_meta.vars):]
                obj = self._get_instance(constructor_args)
                method = getattr(obj, item)
                with obj:
                    result = method(*rest_args, **kwargs)
                    if iterable(result):
                        for res in result:
                            yield res
                    else:
                        yield result


            wrapper.callable_spec = self._get_command_spec(item)

            return wrapper




#class ClassInteractiveCommandsSpec(ClassCommandsSpec):
#
#    def __getattr__(self, item):
#        if item not in self.commands:
#            return getattr(self.klass, item)
#        else:
#            def wrapper(*args, **kwargs):
#                constructor_args = args[:len(self.common_meta.vars)]
#                rest_args = args[len(self.common_meta.vars):]
#                obj = self._get_instance(constructor_args)
#                method = getattr(obj, item)
#                with obj:
#                    result = method(*rest_args, **kwargs)
#                    if iterable(result):
#                        for res in result:
#                            yield res
#                    else:
#                        yield result
#
#            wrapper.callable_spec = self._get_command_spec(item)
#
#            return wrapper




class BaseParserBuilder(object):
    def __init__(self, entity):
        self.entity = entity
        self.parser_conf = ArgumentParser.get_conf(entity)


    def build_parser(self, **conf_params):
        conf = self.parser_conf.copy()
        conf.update(conf_params)
        parser = ArgumentParser(**conf)
        parser.CASE_SENSITIVE = conf_params.get('case_sensitive', getattr(self.entity, 'case_sensitive', True))
        return parser



class CallableParserBuilder(BaseParserBuilder):
    def build_parser(self, **conf_params):
        parser = super(CallableParserBuilder, self).build_parser(**conf_params)
        parser.set_defaults(_cmd_func_=self.entity)
        parser.populate_from(CallableCommandSpec(self.entity))
        return parser



class ClassParserBuilder(BaseParserBuilder):
    def build_parser(self, **conf_params):
        parser = super(ClassParserBuilder, self).build_parser(**conf_params)
        callable_spec = CallableCommandSpec(self.entity.__init__)
        if callable_spec.varargs or callable_spec.varkw:
            raise TypeError('*args and **kwargs are not allowed in constructor')
        parser.populate_from(callable_spec)
        parser.populate_subcommands(self.entity.commands, ClassCommandsSpec(self.entity, self.entity.commands))
        parser.set_defaults(_cmd_func_= None)
        return parser


class ModuleParserBuilder(BaseParserBuilder):
    def build_parser(self, **conf_params):
        parser = super(ClassParserBuilder, self).build_parser(**conf_params)
        callable_spec = CallableCommandSpec(self.entity.__init__)
        if callable_spec.varargs or callable_spec.varkw:
            raise TypeError('*args and **kwargs are not allowed in constructor')
        parser.populate_from(callable_spec)
        parser.populate_subcommands(self.entity.commands, ClassCommandsSpec(self.entity, self.entity.commands))
        parser.set_defaults(_cmd_func_= None)
        return parser

class ArgumentParser(argparse.ArgumentParser):
    """
    An ArgumentParser with .func and .argspec attributes, and possibly
    .commands and .subparsers.
    """
    CASE_SENSITIVE = True
    PARSER_CFG = getfullargspec(argparse.ArgumentParser.__init__).args[1:]
    NONE = object()

    @classmethod
    def get_conf(cls, obj):
        """Extracts the configuration of the underlying ArgumentParser from obj"""
        cfg = dict(description=obj.__doc__,
                   formatter_class=argparse.RawDescriptionHelpFormatter)
        for name in dir(obj):
            if name in cls.PARSER_CFG: # argument of ArgumentParser
                cfg[name] = getattr(obj, name)
        return cfg


    @classmethod
    def parser_from(cls, obj, ignore_errors=False, **conf_params):
        """
        obj can be a callable or an object with a .commands attribute.
        Returns an ArgumentParser.
        """

        #TODO: make it better :))
        if inspect.isclass(obj):
            builder = ClassParserBuilder(obj)
        else:
            builder = CallableParserBuilder(obj)

        parser = builder.build_parser(**conf_params)
        parser.ignore_errors = ignore_errors
        parser.ignored_errors = []

        return parser


    def populate_subcommands(self, commands, obj, title='subcommands', cmd_prefix=''):
        """Extract a list of sub-commands from obj and add them to the parser"""

        if hasattr(obj, 'cmd_prefix') and obj.cmd_prefix in self.prefix_chars:
            raise ValueError('The prefix {0!r} is already taken!'.format(cmd_prefix))

        if not hasattr(self, 'subparsers'):
            self.subparsers = self.add_subparsers(title=title)
        elif title:
            self.add_argument_group(title=title) # populate ._action_groups

        prefix_len = len(getattr(obj, 'cmd_prefix', ''))
        add_help = getattr(obj, 'add_help', True)

        for cmd in commands:
            func = getattr(obj, cmd[prefix_len:]) # strip the prefix
            sub_parser = self.subparsers.add_parser(
                                cmd, add_help=add_help, help=func.__doc__, **self.get_conf(func))
            sub_parser.set_defaults(_cmd_name_=cmd[prefix_len:], _cmd_func_=func)
            sub_parser.populate_from(func.callable_spec)


    def populate_from(self, callable_spec):
        """
        return a populated ArgumentParser instance.
        """

        prefix = self.prefix = getattr(callable_spec, 'prefix_chars', '-')[0]
        self.callable_spec = callable_spec

        for name, default in zip(callable_spec.vars, callable_spec.defaults):
            a = callable_spec.annotations[name]
            metavar = a.metavar

            if default is callable_spec.NONE:
                dflt = None
            else:
                dflt = default
                if a.help is None and  a.kind != 'flag':
                    a.help = '[{0}]'.format(dflt)
                elif a.help:
                    a.help = a.help.format(default=dflt)

            if a.kind in ('option', 'flag'):
                if a.abbrev:
                    short_long = (prefix + a.abbrev, prefix * 2 + name_from_python(name))
                else:
                    short_long = (prefix * 2 + name_from_python(name), )
            elif default is callable_spec.NONE: # required argument
                self.add_argument(name, help=a.help, type=a.type,
                                   choices=a.choices, metavar=metavar)
            else: # default argument
                self.add_argument(
                    name, nargs='?', help=a.help, default=dflt,
                    type=a.type, choices=a.choices, metavar=metavar)

            if a.kind == 'option':
                self.add_argument(dest=name,
                    help=a.help, default=dflt, type=a.type,
                    choices=a.choices, metavar=metavar, *short_long)
            elif a.kind == 'flag':
                if default is not callable_spec.NONE and default is not False:
                    raise TypeError('Flag {0!r} wants default False, got {1!r}'.format(name, default))
                self.add_argument(action='store_true', dest=name, help=a.help, *short_long)

        if callable_spec.varargs:
            a =callable_spec.annotations[callable_spec.varargs]
            self.add_argument(callable_spec.varargs, nargs='*', help=a.help, default=[], action=ArgsAction,
                               const=callable_spec.varkw, type=a.type, metavar=a.metavar)
        if callable_spec.varkw:
            a = callable_spec.annotations[callable_spec.varkw]
            self.add_argument(callable_spec.varkw, nargs='*', help=a.help, default={}, action=KwargsAction,
                               type=DictType(a.type), metavar=a.metavar)


    def consume(self, arg_list, only_known_args=False):
        """Call the underlying function with the args. Works also for
        command containers, by dispatching to the right sub-parser."""
        args, varargs, kwargs, func, ns = self.smart_parse_args(arg_list, only_known_args)

        return ns, func(*(args + varargs), **kwargs)


    def smart_parse_args(self, arg_list, only_known_args=False):
        cmd, subparser = None, None

        if hasattr(self, 'subparsers'):
            subparsers = self._get_subparsers()
            cmd, arg_list = self._extract_cmd(arg_list, subparsers)
            subparser = subparsers.get(cmd)

        if only_known_args:
            ns = vars(self.parse_known_args(arg_list))
        else:
            ns = vars(self.parse_args(arg_list))

        func = self._defaults['_cmd_func_']
        args = [ns[a] for a in self.callable_spec.vars]
        varargs = ns.get(self.callable_spec.varargs or '', [])
        kwargs = ns.get(self.callable_spec.varkw or '', {})

        #TODO review this code.. should write tests
		#Should we analize collisions?
        if subparser:
            parser_args = [ns[a] for a in subparser.callable_spec.vars]
            parser_varargs = ns.get(subparser.callable_spec.varargs or '', [])
            parser_kwargs = ns.get(subparser.callable_spec.varkw or '', {})

        if subparser is None and cmd is not None:
            return  ns, self.missing(cmd)
        elif subparser is not None: # use the sub parser
            func = subparser._defaults['_cmd_func_']
            ns['_cmd_func_'] = func

        if subparser:
            #noinspection PyUnboundLocalVariable
            kwargs.update(parser_kwargs)
            #noinspection PyUnboundLocalVariable
            return args + parser_args, varargs + parser_varargs, kwargs, func, ns

        return args, varargs, kwargs, func, ns



    def _get_subparsers(self):
        if hasattr(self, 'subparsers'):
            return self.subparsers._name_parser_map
        else:
            return None


    def _match_cmd(self, abbrev, commands):
        """Extract the command name from an abbreviation or raise a NameError"""
        if not self.CASE_SENSITIVE:
            abbrev = abbrev.upper()
            commands = [c.upper() for c in commands]

        perfect_matches = [name for name in commands if name == abbrev]
        if len(perfect_matches) == 1:
            return perfect_matches[0]
        matches = [name for name in commands if name.startswith(abbrev)]
        n = len(matches)
        if n == 1:
            return matches[0]
        elif n > 1:
            raise NameError('Ambiguous command {0!r}: matching {1}'.format(abbrev, matches))


    def _extract_cmd(self, arg_list, commands):
        """Extract the right sub-parser from the first recognized argument"""
        opt_prefix = self.prefix_chars[0]
        for i, arg in enumerate(arg_list):
            if not arg.startswith(opt_prefix):
                cmd = self._match_cmd(arg, commands)
                if cmd:
                    arg_list[i] = cmd
                    return  cmd, arg_list
        return None, arg_list


    def _extract_kwargs(self, args):
        """Returns two lists: regular args and name=value args"""
        arg_list = []
        if hasattr(self, 'callable_spec') and self.callable_spec.varkw:
            kwargs = {}
            for arg in args:
                match = re.match(r'([a-zA-Z_]\w*)=', arg)
                if match:
                    name = match.group(1)
                    kwargs[name] = arg[len(name)+1:]
                else:
                    arg_list.append(arg)
            return arg_list, kwargs
        return args, {}


    def missing(self, name):
        """May raise a SystemExit"""
        miss = getattr(self.callable_spec, '__missing__', lambda name: self.error('No command {0!r}'.format(name)))
        return miss(name)


    def print_actions(self):
        """Useful for debugging"""
        print(self)
        for a in self._actions:
            print(a)

    #noinspection PyUnresolvedReferences
    def error(self, message):
        if not self.ignore_errors:
            super(ArgumentParser, self).error(message)
        else:
            self.ignored_errors.append(message)


def iterable(obj):
    """Any object with an __iter__ method which is not a string"""
    return hasattr(obj, '__iter__') and not isinstance(obj, basestring)

def name_from_python(name):
    if name is not None:
        if name.endswith('_') and keyword.iskeyword(name[:-1]):
            name = name[:-1]
        return name.replace('_', '-')

def name_to_python(name):
    if name is not None:
        if keyword.iskeyword(name):
            name += '_'
        return name.replace('-','_')



def call(obj, arg_list=sys.argv[1:], greedy=False, only_known_args=False, **parser_params):
    """
    If obj is a function or a bound method, parse the given arg_list
    by using the parser inferred from the annotations of obj
    and call obj with the parsed arguments.
    If obj is an object with attribute .commands, dispatch to the
    associated subparser.
    """
    ns, result = ArgumentParser.parser_from(obj, **parser_params).consume(arg_list, only_known_args)

    if iterable(result) and not greedy:
        return ns, list(result)

    return ns, result


def wizard_call(obj, wizard_callback, arg_list=sys.argv[1:], greedy=False, default_wizard_mode=True, short_option=None, long_option=None, **parser_params):
    parser = argparse.ArgumentParser(add_help=False)
    if default_wizard_mode:
        additional_options = (short_option or '-W', long_option or '--non-wizard')
        help = 'Command line mode only'
    else:
        additional_options = (short_option or '-w', long_option or '--wizard')
        help = 'Start in wizard mode'
    parser.add_argument(*additional_options, action='store_true', help=help)

    parents = parser_params.get('parents', [])
    parents.append(parser)

    params = set(parser_params)
    params -= set(('parents','ignore_errors'))

    filtered_params = dict([(k, v) for k,v in parser_params if k in params])

    parser = ArgumentParser.parser_from(obj, parents=parents, ignore_errors=True, **filtered_params)
    ns, output = parser.consume(arg_list)

    arg_list = []
    for name, default in zip(parser.callable_spec.vars, parser.callable_spec.defaults):
        annotation = parser.callable_spec.annotations[name]
        value = ns.get(name, None)
        if annotation.kind == 'positional' and value is not None:
            answer = value
        else:
            answer = wizard_callback(name, annotation, default)

        if annotation.kind in ('option', 'flag'):
            arg_list.append("--{0}".format(name_from_python(name)))
        arg_list.append("{0}".format(answer))

    ns, output = ArgumentParser.parser_from(obj, parents=parents, **filtered_params).consume(arg_list)

    if not greedy and iterable(output):
        output = list(output)

    return ns, output








