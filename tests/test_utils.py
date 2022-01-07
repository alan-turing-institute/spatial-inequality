from spineq.utils import distance_matrix, coverage_matrix

import numpy as np


def test_distance_matrix():
    x1 = [0, 3, 6]
    y1 = [0, 4, 8]
    d1 = np.array([[0, 5, 10], [5, 0, 5], [10, 5, 0]])
    assert (distance_matrix(x1, y1) == d1).all()

    x2 = [9]
    y2 = [12]
    d2 = np.array([[15], [10], [5]])
    assert (distance_matrix(x1, y1, x2=x2, y2=y2) == d2).all()


def test_coverage_matrix():
    x1 = [0, 3, 6]
    y1 = [0, 4, 8]
    d1 = np.array([[0, 5, 10], [5, 0, 5], [10, 5, 0]])
    theta = 2
    assert (coverage_matrix(x1, y1, theta=theta) == np.exp(-d1 / theta)).all()

    x2 = [9]
    y2 = [12]
    d2 = np.array([[15], [10], [5]])
    theta = 2
    assert (
        coverage_matrix(x1, y1, x2=x2, y2=y2, theta=theta) == np.exp(-d2 / theta)
    ).all()
