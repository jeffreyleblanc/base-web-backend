

def as_bytes(val):
    if isinstance(val,bytes): return val
    if isinstance(val,str): return val.encode('utf-8')
    raise TypeError()

def as_string(val):
    if isinstance(val,str): return val
    if isinstance(val,bytes): return val.decode('utf-8')
    raise TypeError()
