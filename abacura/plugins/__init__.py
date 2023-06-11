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


def command(name: str = ''):
    def add_command(command_fn):
        command_fn.command = True
        command_fn.command_name = name or command_fn.__name__

        return command_fn

    return add_command
