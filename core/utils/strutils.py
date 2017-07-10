import re

def after(string, substring):
    ''' Returns the text before the search string
        Or returns the whole string if not found.
    '''
    
    if string is not None and substring is not None:
        index = string.find (substring)
    else:
        index = -1

    if index > -1: 
        return string [index + len (substring):]
    else:
        return string

def before(string, substring):
    ''' Returns the text before the search string
        Or returns the whole string if not found.
    '''
    
    if string is not None and substring is not None:
        index = string.find (substring)
    else:
        index = -1

    if index > -1: 
        return string [:index]
    else:
        return string

def contains(string, substring):
    ''' None safe check if a string contains another string.
    '''

    if string is not None and substring is not None:
        return (string.find (substring)) > -1
    elif substring is None:
        return True
    else:
        return False

def contains_ignore_case(string, substring):
    ''' None safe check if a string contains another string.
    '''

    if string is not None and substring is not None:
        return (string.lower().find (substring.lower())) > -1
    elif substring is None:
        return True
    else:
        return False

def ends_with(string, end_string):
    ''' None safe check to see if a string ends in another string.
    '''
    
    if string is not None and end_string is not None:
        return string.endswith(end_string)
    elif end_string is None:
        return True
    else:
        return False

def equals_ignore_case(string1, string2):
    ''' Compare strings ignoring case.
        None safe.
        None == None -> True
    '''
    
    if string1 is not None and string2 is not None:
        return string1.lower() == string2.lower()
    elif string1 is None and string2 is None:
        return True
    else:
        # One is None but not both.
        return False

def find_match_indexes(string, search_string):
    
    return [match.start() for match in re.finditer(search_string, string)]
    

def is_blank(string):
    
    if not string or string.isspace():
        return True
    else:
        return False
    
def is_not_blank(string):
    
    return not is_blank (string)

def join(strings, separator):
    ''' Convenience function for joining a list of strings with a separator between items. 
    '''
    
    return separator.join(strings)

def lower(string):
    ''' None safe string to lowercase function.
    '''
    
    if string is not None:
        string = string.lower()
    
    return string

def replace(string, search_string, replace_string):
    ''' None safe replace function.
        None returns None
        Also handles integers.
    '''
    
    if string is not None:

        # Change int to string:
        if isinstance(replace_string, int):    
            replace_string = str(replace_string)

        # Replace:
        string = string.replace(search_string, replace_string)

    # Else
        # Return as is (None).
    
    return string

def startswith(string, start):
    ''' Null safe startswith function.
    '''
    
    if string is not None:
        return string.startswith(start)
    else:
        return False
    
def startswith_ignore_case(string, start):
    ''' Null safe case insensitive startswith function.
    '''
    
    if string is not None:
        return bool(re.match(start, string, re.IGNORECASE))
    else:
        return False

def strip(string):
    '''None safe string strip function.
       None returns None.
    '''

    if string:
        return string.strip()
    else:
        return string


