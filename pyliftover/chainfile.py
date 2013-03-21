'''
Pure-python implementation of UCSC "liftover" genome coordinate conversion.
Class for dealing with "xx.over.chain" files.

Copyright 2013, Konstantin Tretyakov.
http://kt.era.ee/

Licensed under MIT license.
'''

import os.path
import gzip
import urllib
import shutil

from intervaltree import IntervalTree

class ErrorAwareURLOpener(urllib.FancyURLopener):
  def http_error_default(self, url, fp, errcode, errmsg, headers):
    raise Exception("404")
_urlopener = ErrorAwareURLOpener()

def open_liftover_chain_file(from_db, to_db, search_dir='.', cache_dir=os.path.expanduser("~/.pyliftover"), use_web=True, write_cache=True):
    '''
    A "smart" way of obtaining liftover chain files.
    By default acts as follows:
     1. If the file ``<from_db>To<to_db>.over.chain.gz`` exists in <search_dir>,
        opens it for reading via gzip.open.
     2. Otherwise, if the file ``<from_db>To<to_db>.over.chain`` exists
        in the <search_dir> opens it (as uncompressed file).
        Steps 1 and 2 may be disabled if search_dir is set to None.
     3. Otherwise, checks whether ``<cache_dir>/<from_db>To<to_db>.over.chain.gz`` exists.
        This step may be disabled by specifying cache_dir = None.
     4. If file still not found attempts to download the file from the URL
        'http://hgdownload.cse.ucsc.edu/goldenPath/<from_db>/liftOver/<from_db>To<to_db>.over.chain.gz'
        to a temporary location. This step may be disabled by specifying use_web=False. In this case the operation fails and 
        the function returns None.
     5. At this point, if write_cache=True and cache_dir is not None and writable, the file is copied to cache_dir and opened from there.
        Otherwise it is opened from the temporary location.
        
    In case of errors (e.g. URL cannot be opened), None is returned.
    '''
    to_db = to_db[0].upper() + to_db[1:]
    FILE_NAME_GZ = '%sTo%s.over.chain.gz' % (from_db, to_db)
    FILE_NAME = '%sTo%s.over.chain' % (from_db, to_db)
    
    if search_dir is not None:
        FILE_GZ = os.path.join(search_dir, FILE_NAME_GZ)
        FILE = os.path.join(search_dir, FILE_NAME)
        if os.path.isfile(FILE_GZ):
            return gzip.open(FILE_GZ)
        elif os.path.isfile(FILE):
            return open(FILE, 'r')
    if cache_dir is not None:
        FILE_GZ = os.path.join(cache_dir, FILE_NAME_GZ)
        if os.path.isfile(FILE_GZ):
            return gzip.open(FILE_GZ)
    if use_web:
        # Download file from the web.
        try:
            url = 'http://hgdownload.cse.ucsc.edu/goldenPath/%s/liftOver/%sTo%s.over.chain.gz' % (from_db, from_db, to_db)
            (filename, headers) = _urlopener.retrieve(url)
        except:
            # Download failed, exit
            return None
        # Move the file to cache?
        if write_cache and (cache_dir is not None):
            try:
                if not os.path.isdir(cache_dir):
                    os.mkdir(cache_dir)
                shutil.move(filename, FILE_GZ)
                # Move successful, open from cache
                return gzip.open(FILE_GZ)
            except:
                # Move failed, open file from temp location
                return gzip.open(filename)
        else:
            # Open from temp location
            return gzip.open(filename)
    # If we didn't quit before this place, all failed.
    return None


class LiftOverChainFile:
    '''
    The class, which loads and indexes USCS's .over.chain files.
    
    Specification of the chain format can be found here: http://genome.ucsc.edu/goldenPath/help/chain.html
    '''
    
    def __init__(self, f):
        '''
        Reads chain data from the file and initializes an interval index.
        f must be a file object open for reading.
        If any errors are detected, an Exception is thrown.
        '''
        self.chains = self._load_chains(f)
        self.chain_index = self._index_chains(self.chains)
        
    @staticmethod
    def _load_chains(f):
        '''
        Loads all LiftOverChain objects from a file into an array. Returns the result.
        '''
        chains = []
        while True:
            line = f.readline()
            if not line:
                break

            if line.startswith('#') or line.startswith('\n') or line.startswith('\r'):
                continue
            if line.startswith('chain'):
                # Read chain
                chains.append(LiftOverChain(line, f))
                continue
        return chains

    @staticmethod
    def _index_chains(chains):
        '''
        Given a list of LiftOverChain objects, creates a
         dict: source_name --> 
            IntervalTree: <source_from, source_to> -->
                (target_from, target_to, chain)
        Returns the resulting dict.
        Throws an exception on any errors or inconsistencies among chains (e.g. different sizes specified for the same chromosome in various chains).
        '''
        chain_index = {}
        source_size = {}
        target_size = {}
        for c in chains:
            # Verify that sizes of chromosomes are consistent over all chains
            source_size.setdefault(c.source_name, c.source_size)
            if source_size[c.source_name] != c.source_size:
                raise Exception("Chains have inconsistent specification of source chromosome size for %s (%d vs %d)" % (c.source_name, source_size[c.source_name], c.source_size))
            target_size.setdefault(c.target_name, c.target_size)
            if target_size[c.target_name] != c.target_size:
                raise Exception("Chains have inconsistent specification of target chromosome size for %s (%d vs %d)" % (c.target_name, target_size[c.target_name], c.target_size))
            chain_index.setdefault(c.source_name, IntervalTree(0, c.source_size))
            # Register all blocks from the chain in the corresponding interval tree
            tree = chain_index[c.source_name]
            for (sfrom, sto, tfrom, tto) in c.blocks:
                tree.add_interval(sfrom, sto, (tfrom, tto, c))

        # Sort all interval trees
        for k in chain_index:
            chain_index[k].sort()
        return chain_index

    def query(self, chromosome, position):
        '''
        Given a chromosome and position, returns all matching records from the chain index.
        Each record is an interval (source_from, source_to, data)
        where data = (target_from, target_to, chain). Note that depending on chain.target_strand, the target values may need to be reversed (e.g. pos --> chain.target_size - pos).
        
        If chromosome is not found in the index, None is returned.
        '''
        if chromosome not in self.chain_index:
            return None
        else:
            return self.chain_index[chromosome].query(position)


class LiftOverChain:
    '''
    Represents a single chain from an .over.chain file.
    A chain basically maps a set of intervals from "source" coordinates to corresponding coordinates in "target" coordinates.
    The "source" and "target" are somehow referred to in the specs (http://genome.ucsc.edu/goldenPath/help/chain.html)
    as "target" and "query" respectively.
    '''
    def __init__(self, header, f):
        '''
        Reads the chain from a stream given the first line and a file opened at all remaining lines.
        On error throws an exception.
        '''
        fields = header.split()
        if fields[0] != 'chain' and len(fields) not in [12, 13]:
            raise Exception("Invalid chain format. (%s)" % header)
        # chain 4900 chrY 58368225 + 25985403 25985638 chr5 151006098 - 43257292 43257528 1
        self.score = int(fields[1])        # Alignment score
        self.source_name = fields[2]       # E.g. chrY
        self.source_size = int(fields[3])  # Full length of the chromosome
        self.source_strand = fields[4]     # Must be +
        if self.source_strand != '+':
            raise Exception("Source strand in an .over.chain file must be +. (%s)" % header)
        self.source_start = int(fields[5]) # Start of source region
        self.source_end = int(fields[6])   # End of source region
        self.target_name = fields[7]       # E.g. chr5
        self.target_size = int(fields[8])  # Full length of the chromosome
        self.target_strand = fields[9]     # + or -
        if self.target_strand not in ['+', '-']:
            raise Exception("Target strand must be - or +. (%s)" % header)
        self.target_start = int(fields[10])
        self.target_end = int(fields[11])
        self.id = None if len(fields) == 12 else fields[12]
        
        # Now read the alignment chain from the file and store it as a list (source_from, source_to) -> (target_from, target_to)
        sfrom, tfrom = self.source_start, self.target_start
        self.blocks = []
        fields = f.readline().split()
        while len(fields) == 3:
            size, sgap, tgap = int(fields[0]), int(fields[1]), int(fields[2])
            self.blocks.append((sfrom, sfrom+size, tfrom, tfrom+size))
            sfrom += size + sgap
            tfrom += size + tgap
            fields = f.readline().split()
        if len(fields) != 1:
            raise Exception("Expecting one number on the last line of alignments block. (%s)" % header)
        size = int(fields[0])
        self.blocks.append((sfrom, sfrom+size, tfrom, tfrom+size))
        if (sfrom + size) != self.source_end  or (tfrom + size) != self.target_end:
            raise Exception("Alignment blocks do not match specified block sizes. (%s)" % header)
