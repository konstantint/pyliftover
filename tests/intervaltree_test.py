'''
Pure-python implementation of UCSC "liftover" genome coordinate conversion.
IntervalTree test module.

Copyright 2013, Konstantin Tretyakov.
http://kt.era.ee/

Licensed under MIT license.
'''

from pyliftover.intervaltree import IntervalTree
def test_intervaltree():
    intervals = [(10, 20), (20, 30), (21, 31), (30, 40), (40, 50), (45, 55), (45, 56), (46, 57), (55, 56), (58, 59), (50, 51)]
    query_points = [-1, 0, 1, 10, 11, 19, 20, 21, 24, 25, 26, 30, 40, 41, 48, 49, 50, 51, 52, 60, 74, 75, 76, 90, 100, 1000]
    do_test_tree(0, 100, intervals, query_points)
    do_test_tree(0, 100, [(a, a) for a in range(100)] + [(a, a) for a in range(100)], [a for a in range(100)])
    do_test_tree(0, 100, [(a, a) for a in range(100)] + [(a, a+1) for a in range(100)] + [(a, 2*a) for a in range(100)], [a for a in range(100)])
    
def do_test_tree(min, max, intervals, query_points):
    t = IntervalTree(min, max)
    for int in intervals:
        t.add_interval(*int)
    t.sort()
    assert len(t) == len([i for i in intervals if i[0] < i[1]])
    assert len(t) == len(list(t))
    for q in query_points:
        r = t.query(q)
        true_r = [(a, b, None) for (a,b) in intervals if a <= q < b]
        assert sorted(r) == sorted(true_r)
