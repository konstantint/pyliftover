'''
Pure-python implementation of UCSC "liftover" genome coordinate conversion.
LiftoverChain test.

Copyright 2013, Konstantin Tretyakov.
http://kt.era.ee/

Licensed under MIT license.
'''
import os
import sys
if sys.version_info < (3, 0):
    from cStringIO import StringIO
else:
    from io import BytesIO as StringIO

from pyliftover.chainfile import LiftOverChain, LiftOverChainFile, open_liftover_chain_file

# Examples from spec page: http://genome.ucsc.edu/goldenPath/help/chain.html
example_1 = b'''
chain 4900 chrY 58368225 + 25985403 25985638 chr5 151006098 - 43257292 43257528 1
9       1       0
10      0       5
61      4       0
16      0       4
42      3       0
16      0       8
14      1       0
3       7       0
48
'''

example_2 = b'''
chain 4900 chrY 58368225 + 25985406 25985566 chr5 151006098 - 43549808 43549970 2
  16      0       2
  60      4       0
  10      0       4
  70
'''

def load_chain(data):
    f = StringIO(data)
    f.readline()
    header = f.readline()
    return LiftOverChain(header, f)
    
def test_liftover_chain():
    '''
    This is just a smoke test.
    '''
    chain = load_chain(example_1)
    assert (chain.score, chain.source_name, chain.source_size, chain.source_start, chain.source_end, 
                         chain.target_name, chain.target_size, chain.target_strand, chain.target_start, chain.target_end, 
            chain.id) == (4900, 'chrY', 58368225, 25985403, 25985638, 'chr5', 151006098, '-', 43257292, 43257528, '1')
    assert chain.blocks[0] == (25985403, 25985403+9, 43257292)
    assert chain.blocks[1] == (25985403+9+1, 25985403+9+1+10, 43257292+9+0)
    assert len(chain.blocks) == 9
    
    chain = load_chain(example_2)
    assert (chain.score, chain.source_name, chain.source_size, chain.source_start, chain.source_end, 
                         chain.target_name, chain.target_size, chain.target_strand, chain.target_start, chain.target_end, 
            chain.id) == (4900, 'chrY', 58368225, 25985406, 25985566, 'chr5', 151006098, '-', 43549808, 43549970, '2')
    assert chain.blocks[0] == (25985406, 25985406+16, 43549808)
    assert chain.blocks[1] == (25985406+16, 25985406+16+60, 43549808+16+2)
    assert len(chain.blocks) == 4

def test_liftover_chain_file():
    '''
    This is just a smoke test. (NB: it loads actual hg17-to-hg18.over.chain, attempting to download it to cache).
    '''
    # Simple example
    data = example_1 + example_2
    chains = LiftOverChainFile._load_chains(StringIO(data))
    assert len(chains) == 2
    index = LiftOverChainFile._index_chains(chains)
    assert len(index) == 1
    assert len(index['chrY']) == 9+4
    assert len(index['chrY'].query(25985406)) == 2
    assert len(index['chrY'].query(25985403)) == 1
    assert len(index['chrY'].query(25985402)) == 0
    assert len(index['chrY'].query(25985405)) == 1
    assert index['chrY'].query(25985405)[0][2][-1] == chains[0]
    cf = LiftOverChainFile(StringIO(data))
    assert len(cf.query('chrY', 25985406)) == 2
    assert len(cf.query('chrY', 25985403)) == 1
    assert len(cf.query('chrY', 25985402)) == 0
    assert len(cf.query('chrY', 25985405)) == 1
    assert cf.query('chrY', 25985405)[0][2][-1] == cf.chains[0]
    assert cf.query('chrZ', 25985405) is None
    
    # hg17-to-hg18 example
    f = open_liftover_chain_file('hg17', 'hg18')
    chains = LiftOverChainFile._load_chains(f)
    assert len(chains) > 1000
    f.close()
    index = LiftOverChainFile._index_chains(chains)
    assert len(index) >= 22

def test_issue_1():
    testdata_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'mds42.to.mg1655.liftOver')
    with open(testdata_file, 'rb') as f:
        locf = LiftOverChainFile(f)
        assert len(locf.chains) == 1