class IsFirst:

    def __init__(self):

        self._first = True

    def is_first(self):

        first = self._first

        if first:
            self._first = not first

        return first

    def is_not_first(self):

        return not self.is_first()
