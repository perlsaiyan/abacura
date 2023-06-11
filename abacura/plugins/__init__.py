import re


class Plugin:
    """Generic Plugin Class"""
    name = ""
    plugin_enabled = True

    def get_name(self):
        return self.name        
    
    def get_help(self):
        doc = getattr(self, '__doc__', None)
        return doc

    def do(self, line, context):
        pass


def action(regex: str, color: bool = False):
    def add_action(action_fn):
        action_fn.action_re = regex
        action_fn.action_re_compiled = re.compile(regex)
        action_fn.action_color = color
        return action_fn
    
    return add_action


def command(function=None, name: str = ''):
    def add_command(fn):
        fn.command = True
        fn.command_name = name or fn.__name__

        return fn

    if function:
        return add_command(function)

    return add_command
