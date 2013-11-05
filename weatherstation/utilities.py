"""General utilities functions.

Functions:
isFloat:                        Determines if a string is a number.
floor_to_n:                     Floors a float to the next integer dividable by n.
ceil_to_n:                      Ceils a float to the next integer dividable by n.
"""
import math


def isFloat(string):
    """Determines if a string is a number.
    
    Args:
    string:                     String to be checked.   
    
    Returns:                             
    result:                 True if the string is a number, False otherwise.
                                
    Raises:
    None
    """
    try:
        float(string)
        return True
    except ValueError:
        return False


def floor_to_n( val, n ):
    """Floors a float to the next integer dividable by n.
    
    Args:
    val:                        Value to be floored.
    n:                          The number will be floored to the next integer dividable by this number.
    
    Returns:                             
    floord_val:                 Value floored to the next integer dividable by 'n'.
                                
    Raises:
    None
    """
    floored_val = math.floor( val / n ) * n

    return floored_val


def ceil_to_n( val, n ):
    """Ceils a float to the next integer dividable by n.
    
    Args:
    val:                        Value to be ceiled.
    n:                          The number will be ceiled to the next integer dividable by this number.
    
    Returns:                             
    ceiled_val:                 Value ceiled to the next integer dividable by 'n'.
                                
    Raises:
    None
    """
    ceiled_val = math.ceil( val / n ) * n

    return ceiled_val