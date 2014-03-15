'''
Pure-python implementation of UCSC "liftover" genome coordinate conversion.
Chain file "smart" locator routine test module.

NB: Look at the SKIP_TEST variable below.

Copyright 2013, Konstantin Tretyakov.
http://kt.era.ee/

Licensed under MIT license.
'''

import os, urllib, shutil, gzip
from tempfile import mkdtemp
from pyliftover.chainfile import open_liftover_chain_file

# This test requires creating directories, downloading files, etc, so
# sometimes we don't care to wait and just skip it.
SKIP_TEST = False

# The corresponding chain file seems to be the smallest.
from_db = 'hg17'
to_db = 'hg18'

def setup_module(module):
    global root_dir, cache_dir, search_dir
    if SKIP_TEST:
        return
    root_dir = mkdtemp()
    cache_dir = os.path.join(root_dir, 'cache')
    search_dir = os.path.join(root_dir, 'search')
    assert not os.path.exists(cache_dir)
    assert not os.path.exists(search_dir)

def teardown_module(module):
    if SKIP_TEST:
        return
    shutil.rmtree(root_dir)

def test_open_liftover_chain_file():
    if SKIP_TEST:
        return
    # No-web, no-cache, must return none
    f = open_liftover_chain_file(from_db, to_db, search_dir=None, cache_dir=None, use_web=False, write_cache=False)
    assert f is None
    assert not os.path.exists(cache_dir)
    
    # No-web, cache, nonexistent search dir, must return none
    f = open_liftover_chain_file(from_db, to_db, search_dir=search_dir, cache_dir=cache_dir, use_web=False, write_cache=True)
    assert f is None
    assert not os.path.exists(cache_dir)

    # Web, no write cache, nonexistent search dir, must open temp file
    f = open_liftover_chain_file(from_db, to_db, search_dir=search_dir, cache_dir=cache_dir, use_web=True, write_cache=False)
    assert f is not None
    assert not os.path.exists(cache_dir)
    ln = f.readline()
    assert ln.startswith(b'##matrix')
    f.close()
    os.unlink(f.name)
    
    # Web, nonexistent db. Must not modify cache.
    f = open_liftover_chain_file(from_db, 'blablabla', search_dir=search_dir, cache_dir=cache_dir, use_web=True, write_cache=True)
    assert f is None
    assert not os.path.exists(cache_dir)
    
    # Web, write cache, nonexistent search dir, must save to cache, creating cache dir
    f = open_liftover_chain_file(from_db, to_db, search_dir=search_dir, cache_dir=cache_dir, use_web=True, write_cache=True)
    assert f is not None
    assert os.path.exists(cache_dir)
    ln = f.readline()
    assert ln.startswith(b'##matrix')
    f.close()

    # No web, file in cache, nonexistent search dir, must exist
    f = open_liftover_chain_file(from_db, to_db, search_dir=search_dir, cache_dir=cache_dir, use_web=False, write_cache=True)
    assert f is not None
    ln = f.readline()
    assert ln.startswith(b'##matrix')
    f.close()
    
    # No web, no file in cache, nonexistent db
    f = open_liftover_chain_file(from_db, 'blablabla', search_dir=search_dir, cache_dir=cache_dir, use_web=False, write_cache=True)
    assert f is None
    
    os.mkdir(search_dir)
    # File both in cache and search_dir. Assert search_dir is used and uncompressed file is preferred
    filename = '%sTo%s.over.chain' % (from_db, to_db[0].upper() + to_db[1:])
    filename = os.path.join(search_dir, filename)
    fout = open(filename, 'wb')
    fout.write(b'test-test')
    fout.close()
    f = open_liftover_chain_file(from_db, to_db, search_dir=search_dir, cache_dir=cache_dir, use_web=True, write_cache=True)
    assert f is not None
    assert f.readline() == b'test-test'
    f.close()
    
    # gzipped file is preferred
    fout = gzip.open(filename + '.gz', 'w')
    fout.write(b'test-test-gzip')
    fout.close()
    f = open_liftover_chain_file(from_db, to_db, search_dir=search_dir, cache_dir=cache_dir, use_web=True, write_cache=True)
    assert f is not None
    assert f.readline() == b'test-test-gzip'
    f.close()
    os.unlink(filename)
    os.unlink(filename + '.gz')

