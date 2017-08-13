#!/usr/bin/env python
# -*- coding: utf-8 -*-


import __init__

import itertools as it
from collections import OrderedDict

import numpy as np
import networkx as nx

import scipy.interpolate as ip

import pomegranate as pmg
from sklearn.neighbors import BallTree


# UTILS
def _find_connected_components(lst):
    """
    Join together a list is list based on their interestion.
        https://stackoverflow.com/questions/9353802/python-merge-multiple-list-with-intersection
    """

    def pairs(lst):
        i = iter(lst)
        first = prev = item = i.next()
        for item in i:
            yield prev, item
            prev = item
        yield item, first

    g = nx.Graph()
    for sub_list in lst:
        for edge in pairs(sub_list):
                g.add_edge(*edge)

    return list(nx.connected_components(g))


def build_seg(pt_list, x_min, x_max):
    """
    Transform a list of points to as segment (with given boundaries).
    """

    return [(x_min, pt_list[0])] +  zip(pt_list, pt_list[1:]) + [(pt_list[-1], x_max)]




# DISTANCE FUNCTIONS
def _curve_dist(f):
    """
    Define a metric such the more likely are curves shapes, the shorter the distance is.
    """

    # Approximate integral on given portion
    nb_pt=10
    def _approx_integral(f, a, b):
        # We can use the sum of several points as an approximation since
        # It is ensured there are at most 2 variations on each portion.
        return np.mean([f(x) for x in np.linspace(a, b, nb_pt)])

    # Give a shift offset to a curve portion
    def _align_to_zero(f, beg): return lambda x: f(x + beg)


    def _eval(s1, s2):
        """
        Evaluate the approximated distance between 2 portions of the curve.
        """

        # Define boundaries
        (a1, b1), (a2, b2) = s1, s2
        ab1, ab2 = b1 - a1, b2 - a2

        # Find the offset between curves portions
        ab_ref, ab_metric = max(ab1, ab2), min(ab1, ab2)
        ab_diff = ab_ref - ab_metric

        # Align curves portions to the left and to the right
        f_ref, f_m = map(lambda a: _align_to_zero(f, a), [a1, a2] if ab1 > ab2 else [a2, a1])

        # Create functions equal to zero out of the bounds
        f_l = lambda x: f_m(x) if x <= ab_metric else 0.0
        f_r = lambda x: f_m(x - ab_diff) if x > ab_diff else 0.0

        # Compute the error
            # Aligned to the left
        e_l = _approx_integral(lambda x: np.power(f_ref(x) - f_l(x), 2), 0., ab_ref)
            # Aligned to the right
        e_r = _approx_integral(lambda x: np.power(f_ref(x) - f_r(x), 2), 0., ab_ref)

        return (e_l + e_r) / 2.

    return _eval



def cluster_seg(bt, seg_list, radius):
    """
    Fetch segments which align themself for a given tolerance.
    """

    cluster, seen_ix = [], set()

    for i, seg in enumerate(seg_list):
        if i not in seen_ix:
            sim_seg_ix = list(bt.query_radius([seg], radius)[0])

            seen_ix |= set(sim_seg_ix)
            cluster.append(sim_seg_ix)

    return _find_connected_components(cluster)


# PROCESS
def sequence_signal(y, X=None, leaf_size=1):
    """
    Analyse the signal and fuzzy index the segments.
    """

    # Index the distribution if needed
    X = X if X is not None else range(len(y))

    # Define the scope
    x_min, x_max = min(X), max(X)

    # Compute interpolation
    spl = ip.UnivariateSpline(X, y, k=4, s=0.)
    d1 = spl.derivative()
    d2 = d1.derivative()

    # Find extremas
    maxima, minima = [r for r in d1.roots() if d2(r) < 0], [r for r in d1.roots() if d2(r) > 0]
    maxima_seg, minima_seg = build_seg(maxima, x_min, x_max), build_seg(minima, x_min, x_max)

    # Build segments from extremas
    #   Indexes are guaranted to be stable between minima and maxima segments
    #   because extracted extremas were strictly different from 0 - ie: only one variation per segment
    segment = [(max(beg_s1, beg_s2), max(end_s1, end_s2)) for (beg_s1, end_s1), (beg_s2, end_s2) in zip(minima_seg, maxima_seg)]

    # Fuzzy index segments
    bt_max = BallTree(maxima_seg, metric=_curve_dist(spl), leaf_size=leaf_size)
    bt_min = BallTree(minima_seg, metric=_curve_dist(spl), leaf_size=leaf_size)


    def _find_periodicity(tol):
        """
        Return noticable curve portions and their cluster.
        """

        # Find cluster
        max_cluster, min_cluster = cluster_seg(bt_max, maxima_seg, tol), cluster_seg(bt_min, minima_seg, tol)

        # Merge min and max clusters
        #   This step ensure resilience to amplitude shift
        cluster = _find_connected_components([list(l) for l in max_cluster] + [list(l) for l in min_cluster])

        # Associate segments with cluster indexes
        ix_cluster = {}
        for i, clu in enumerate(cluster):
            ix_cluster.update(dict(zip(list(clu), [i]*len(clu))))

        return OrderedDict([(seg, ix_cluster[ix]) for ix, seg in enumerate(segment)])

    return _find_periodicity


def find_principal_period(find_periodicity_clj, tol):
    """
    Use the fuzzy indexing of segments to find the principal period of the signal.
    """

    # Sequence the signal
    seq = find_periodicity_clj(tol)
    seg, cluster = zip(*[s for s in seq.iteritems()])

    # Analyse the sequence with HMM
    model = pmg.HiddenMarkovModel.from_samples(pmg.DiscreteDistribution,
                                               n_components=len(set(seq.values())),
                                               X=[cluster])

    # Compare states and select best state as separator
    sum_state = model.predict_proba(cluster).sum(axis=0)
    most_likely_states = sorted(range(len(sum_state)), key=lambda k: sum_state[k], reverse=True)

    # We select only the best match -> could be improved
    separator = most_likely_states[0]

    # Project on segments
    pred = model.predict(cluster)
    seg_ix = [i for i, x in enumerate(pred) if x == separator]

    # Rebuild and return a list of segments
    x_min, x_max = seg[0][0], seg[-1][1]
    return build_seg([beg for (beg, end) in [seg[ix] for ix in seg_ix]], x_min, x_max)
