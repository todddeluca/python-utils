

'''
Why do I never use the tempfile module?

- I am responsible for removing files and dirs tempfile creates, which creates
  lots of boilerplate whenever I use it.
- There is no context manager for temp dirs.
- When using mkstemp(), I get an open file descriptor, not a file object, that
  I have to close.
- The context manager for temp files contains ambiguous statements like this
  from the tempfile docs: "Whether the name can be used to open the file a
  second time, while the named temporary file is still open, varies across
  platforms"
- I do not get to choose the file perms of files and dirs I create.

What do I like about this module:

- It has a context manager for creating a temp dirs.  And one for temp files.
- The context manager clean up the dir or file upon exit, not upon file
  closure.
- No ambiguity about whether you can or cannot open a file twice.
- You can set the permissions of the temp file or dir to what you want.
- It is very clear what the implementation is:
    - directories are created and the path is returned.
    - files are not created, since you'll want to do that in a `with
      open(filename) ...` statement, and the path is returned.
    - directories and files are cleaned up by the context managers.
    - file and dir names are generated using the uuid module, which presumably
      will avoid race conditions.

Usage examples:

Creating a working dir for subprocesses:

    with temp_dir() as workdir:
        with open(os.path.join(workdir, 'datafile'), 'wb') as fh:
            fh.write(data)
        subprocess.call('compute.sh'.format(workdir), shell=True)
        with open(os.path.join(workdir, 'outfile')) as fh:
            print fh.read()

Creating a temp file for a transform and upload:

    with temp_file() as transformed_path:
        transform(input_path, transformed_path)
        upload(transformed_path, destination)

The default values when parameter are not specified, are stored in variables
that are set using environment variables if available or a default value
otherwise.  Here is a table listing the variable, the environment variable 
checked, and the default value:

    Variable, ENV_VAR, Default
    TEMPS_DIR, TEMPS_DIR, os.cwd()
    TEMPS_PREFIX, TEMPS_PREFIX, ''
    TEMPS_SUFFIX, TEMPS_SUFFIX, ''
    TEMPS_MODE, TEMPS_MODE, '0777'
'''

import contextlib
import os
import shutil
import uuid


# SET THE DEFAULTS

TEMPS_DIR = os.environ.get('TEMPS_DIR') or os.getcwd()
TEMPS_PREFIX = os.environ.get('TEMPS_PREFIX', '')
TEMPS_SUFFIX = os.environ.get('TEMPS_SUFFIX', '')
TEMPS_MODE = int(os.environ.get('TEMPS_MODE', '0777'), 8)

@contextlib.contextmanager
def tmpfile(root=TEMPS_DIR, prefix=TEMPS_PREFIX, suffix=TEMPS_SUFFIX):
    '''
    For use in a with statement, this function yields a path directly under
    root guaranteed to be unique by using the uuid module.  This path
    is not created.  However if the path is an existing file when the with
    statement is exited, the file will be removed.

    This function is useful if you want to use a file temporarily but do not
    want to write boilerplate to make sure it is removed when you are done with
    it.
    '''
    path = _tmppath(root, prefix, suffix)
    try:
        yield path
    finally:
        if os.path.isfile(path):
            # try to delete the file
            os.unlink(path)


@contextlib.contextmanager
def tmpdir(root=TEMPS_DIR, prefix=TEMPS_PREFIX, suffix=TEMPS_SUFFIX,
             mode=TEMPS_MODE, use_umask=True):
    '''
    use_umask: if False, the mode of the created directory will be explicitly
    set to `mode` using os.chmod.  By default, `mode` is altered by the current
    umask.

    For use in a with statement, this function makes and a directory directly
    under root with the given mode that is guaranteed to be uniquely named by
    using the uuid module.  Then it yields the directory path.  When the with
    statement is exited the directory and everything under it will be removed.

    This function is useful if you need an isolated place to do some temporary
    work with files and dirs without worrying about naming conflicts and
    without having to write boilerplate and error handling to make sure the
    directory is cleaned up.
    '''
    path = _tmppath(root, prefix, suffix)
    os.makedirs(path, mode=mode)
    if not use_umask:
        os.chmod(path, mode)

    try:
        yield path
    finally:
        shutil.rmtree(path)


def _tmppath(root=TEMPS_DIR, prefix=TEMPS_PREFIX, suffix=TEMPS_SUFFIX):
    '''
    Returns a path directly under root that is guaranteed to be unique by
    using the uuid module.
    '''
    return os.path.join(root, prefix + uuid.uuid4().hex + suffix)



