NO_TEXT = 'no'
NO_TEXTS = ['f', 'False', 'n', 'no']
YES_TEXT = 'yes'
YES_TEXTS = ['t', 'true', 'y', 'yes']

def from_string(bool_string):
    if bool_string is not None and bool_string.lower() in YES_TEXTS:
        return True
    else:
        return False
        
def to_string (value):
    if value:
        return YES_TEXT
    else:
        return NO_TEXT

