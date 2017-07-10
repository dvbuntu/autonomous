class CoreException (Exception):
    def __init__(self,*args,**kwargs):
        super.__init__(self,*args,**kwargs)
        
        # Add messages property:
        if args:
            if isinstance(args[0], list):
                self.messages = args[0]
                
            elif isinstance (args[0], str):
                self.messages = [args[0]]
                
            else:
                self.messages = []
                
    def messages_as_string(self):
        return ' '.join (self.messages)

class FailedValidation(CoreException):
    def __init__(self, *args, **kwargs):
        super.__init__(self, *args, **kwargs)

class InvalidConfig(CoreException):
    def __init__(self, *args, **kwargs):
        super.__init__(self, *args, **kwargs)

class ItemAlreadyExistsError(CoreException):
    def __init__(self, *args, **kwargs):
        super.__init__(self, *args, **kwargs)

class ItemNotFound(CoreException):
    def __init__(self, *args, **kwargs):
        super.__init__(self, *args, **kwargs)
