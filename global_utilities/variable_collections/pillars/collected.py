from . import source

l = [getattr(source,item) for item in dir(source) if not item.startswith("__")\
        or not item.startswith("_")]
