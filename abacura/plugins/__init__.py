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