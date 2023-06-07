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


def action(regex: str, first_char=''):
    def add_action(action_fn):
        action_fn.action_re = regex
        action_fn.action_re_compiled = re.compile(regex)
        action_fn.action_first_char = first_char
        return action_fn
    
    return add_action