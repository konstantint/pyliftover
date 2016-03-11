'''
Pure-python implementation of UCSC "liftover" genome coordinate conversion.
Liftover coordinate conversion correctness test.

Copyright 2013, Konstantin Tretyakov.
http://kt.era.ee/

Licensed under MIT license.
'''

import os.path
import gzip
import sys
from pyliftover.liftover import LiftOver

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(THIS_DIR, 'data')
    
def test_liftover():
    '''
    The test data was prepared as follows:
        * We loaded all intervals from hg17-to-hg18.
        * We then picked positions from the genome as follows:
            For each interval we picked the first, the last, the first-1, last+1, and first+4 positions.
            From the resulting ~40k points we chose 10000 random sites.
            We converted those via UCSC-hosted Web "liftOver" tool and wrote down the results.
     The test results are in data/hg17ToHg18.testpoints.txt.gz.
     Just in case we also saved the corresponding over.chain file.
    '''
    lo = LiftOver(os.path.join(DATA_DIR, 'hg17ToHg18.over.chain.gz'))
    testdata_file = os.path.join(DATA_DIR, 'hg17ToHg18.testpoints.txt.gz')
    test_counter = 0
    f = gzip.open(testdata_file)    # no "with" here because we want to support Python 2.6
    for ln in f:
        ln = ln.decode('ascii')
        s_chr, s_pos, t_chr, t_pos = ln.split('\t')
        result = lo.convert_coordinate(s_chr, int(s_pos))   
        if t_chr == '-':
            assert len(result) == 0
        else:
            assert len(result) == 1
            res_chr = result[0][0]
            res_pos = result[0][1]
            assert res_chr == t_chr
            assert res_pos == int(t_pos)
        
        # Check that we can provide chromosome as a bytes object and 
        # everything will work still
        if sys.version_info >= (3, 0):
            result = lo.convert_coordinate(s_chr.encode('ascii'), int(s_pos))
            if t_chr == '-':
                assert len(result) == 0
            else:
                assert len(result) == 1
                res_chr = result[0][0]
                res_pos = result[0][1]
                assert res_chr == t_chr
                assert res_pos == int(t_pos)
                 
        test_counter += 1
    assert test_counter == 10000

def test_liftover_2():
    '''
    Check that liftover can open files given both as strings and file objects.
    '''
    lo = LiftOver(os.path.join(DATA_DIR, 'hg17ToHg18.over.chain.gz'))
    assert len(lo.chain_file.chain_index) > 22
    lo = LiftOver(gzip.open(os.path.join(DATA_DIR, 'hg17ToHg18.over.chain.gz')))
    assert len(lo.chain_file.chain_index) > 22


def test_issue_2_3_4():
    '''
    Check the correctness of coordinate conversion for issue 2/3/4.
    
    NB: We are using the "live" hg38ToHg19.over.chain.gz file, hence if it happens to change later on,
    the test may start failing. Just in case we have the original cached in the data directory as well.
    '''
    lo = LiftOver('hg38', 'hg19')
    test_input = os.path.join(DATA_DIR, 'hg38ToHg19.testinput.txt')
    test_output = os.path.join(DATA_DIR, 'hg38ToHg19.testoutput.txt')
    
    test_input = dict([(ln[3], (ln[0], int(ln[1]), ln[5].strip())) for ln in [line.split() for line in open(test_input)]])
    test_output = dict([(ln[3], (ln[0], int(ln[1]), ln[5].strip())) for ln in [line.split() for line in open(test_output)]])
    
    for k in test_input:
        res = lo.convert_coordinate(*test_input[k])
        if k not in test_output:
            assert len(res) == 0
        else:
            assert len(res) == 1 and res[0][0:3] == test_output[k]
