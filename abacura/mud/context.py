class Context():

    def __init__(self, app):
        self._app = app

    def sessions(self):
        return self._app.sessions
    
    
