def isFloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False