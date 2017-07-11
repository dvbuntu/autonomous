class IsFirst:
    ''' A simple class that tracks if this is the first time something has been
        called or not.
        The first time a function on the class is called it will return true for
        is_first. All other times it will return false.
    '''

    def __init__(self):
        self._first = True

    def is_first(self):
        first = self._first

        if first:
            self._first = not first

        return first

    def is_not_first(self):
        return not self.is_first()
