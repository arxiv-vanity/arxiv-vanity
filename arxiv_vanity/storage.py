import os

# https://github.com/ephes/homepage/blob/a62d45611c2f3849f0845b8ec4256f130d68db25/homepage/blogs/utils.py
def storage_walk(storage, cur_dir=""):
    """
    Recursive listdir() for Django storages.
    """
    dirs, files = storage.listdir(cur_dir)
    for directory in dirs:
        new_dir = os.path.join(cur_dir, directory)
        for path in storage_walk(storage, cur_dir=new_dir):
            yield path
    for fname in files:
        path = os.path.join(cur_dir, fname)
        yield path


def storage_delete_path(storage, root_path):
    """
    Resursive delete for Django storage.
    """
    for path in storage_walk(storage, root_path):
        storage.delete(path)
