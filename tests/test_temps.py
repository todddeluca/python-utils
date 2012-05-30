


import temps
import os

def test_tmpfile():
    with temps.tmpfile() as path:
        assert not os.path.exists(path)
        with open(path, 'w') as fh:
            fh.write('test')
        assert os.path.exists(path)
    assert not os.path.exists(path)


def test_tmpdir():
    path = None
    with temps.tmpdir() as td:
        assert os.path.isdir(td)
        path = os.path.join(td, 'test')
        with open(path, 'w') as fh:
            fh.write('test')
        assert os.path.exists(path)
    assert not os.path.exists(path)
    assert not os.path.exists(td)




