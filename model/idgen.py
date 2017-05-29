import os, base64

# Generates a new ID. 
# The resulting ID is: 
#     * almost certainly unique and cryptographically secure (see python docs for os.urandom)
#     * made of only the [0123456789ABCDEF] characters (see base16 encoding)

def new_id(): 
    return base64.b16encode(os.urandom(16))


# Checks if the string is a valid ID (that is, an ID that could be made by new_id()).
def is_id(string): 
    # the string must be 32 bytes long
    if len(string) != 32: 
        print 'a'
        return False
    # the string must be made of only the [0123456789ABCDEF] characters
    for i in range(0, len(string)): 
        if not ((ord(string[i]) >= ord('0') and ord(string[i]) <= ord('9'))
                or 
                (ord(string[i]) >= ord('A') and ord(string[i]) <= ord('F'))): 
            print 'b', string[i]
            return False
    return True
