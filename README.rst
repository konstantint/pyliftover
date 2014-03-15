============================================================================
Pure-python implementation of UCSC ``liftOver`` genome coordinate conversion
============================================================================

.. image:: https://travis-ci.org/konstantint/pyliftover.png?branch=master   :target: https://travis-ci.org/konstantint/pyliftover

PyLiftover is a library for quick and easy conversion of genomic (point) coordinates between different assemblies.

It uses the same logic and coordinate conversion mappings as the UCSC `liftOver tool <http://genome.ucsc.edu/cgi-bin/hgLiftOver>`_.

As of current version (0.2), PyLiftover only does conversion of point coordinates, that is, 
unlike ``liftOver``, it does not convert ranges, nor does it provide any special facilities to work with BED files.
For single-point coordinates it produces exactly the same output as ``liftOver`` (verified with at least the ``hg17ToHg18.over.chain.gz`` file for now).

Installation
------------

The simplest way to install the package is via ``easy_install`` or ``pip``::

    $ easy_install pyliftover

Usage
-----
The primary usage example, supported by the library is the following::

    from pyliftover import LiftOver
    lo = LiftOver('hg17', 'hg18')
    lo.convert_coordinate('chr1', 1000000)

The first line will automatically download the hg17-to-hg18 coordinate conversion `chain file <http://genome.ucsc.edu/goldenPath/help/chain.html>`_ from UCSC,
unless it is already cached or available in the current directory. Alternatively, you may provide your own chain file::

    lo = LiftOver('hg17ToHg18.over.chain.gz')
    lo.convert_coordinate('chr1', 1000000, '-')

The result of ``lo.convert_coordinate`` call is either ``None`` (if the source chromosome name is unrecognized) or a list of target positions in the
new assembly. The list may be empty (locus is deleted in the new assembly), have a single element (locus matched uniquely), or, in principle, 
have multiple elements (although this is probably a rare occasion for most default intra-species genomic conversions).
Note that coordinates in the tool are 0-based. That is, a position that you would refer to in the genome browser by ``chr1:10`` 
corresponds to coordinate ``9`` in PyLiftover's terms.

Although you may try to apply the tool with arbitrary chain files, like the original ``liftOver`` tool, it makes most sense for conversion of 
coordinates between different assemblies of the same species.


See also
--------

* Blog post: http://fouryears.eu/2013/02/25/the-curse-of-genomic-coordinates/
* Report issues and submit fixes at Github: https://github.com/konstantint/pyliftover
