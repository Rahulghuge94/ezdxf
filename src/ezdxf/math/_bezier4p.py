# Copyright (c) 2010-2020 Manfred Moitzi
# License: MIT License
from typing import TYPE_CHECKING, Iterable, Union, Sequence
import math
from functools import lru_cache
# A pure Python implementation of a base type can't import from ._types or ezdxf.math!
from ._vector import Vec3, Vec2
from ._matrix44 import Matrix44


if TYPE_CHECKING:
    from ezdxf.eztypes import Vertex

__all__ = ['Bezier4P']


def check_if_in_valid_range(t: float):
    if not (0 <= t <= 1.):
        raise ValueError("t not in range [0 to 1]")


# Optimization:
# cubic P(t) = (1-t)^3*P0 + 3*(1-t)^2*t*P1 + 3*(1-t)*t^2*P2 + t^3*P3
# cubic P(t) = a*P0 + b*P1 + c*P2 + d*P3
# a, b, c, d = bernstein3(t) ... cached
@lru_cache(maxsize=300)
def bernstein3(t: float) -> Sequence[float]:
    """ Bernstein polynom of 3rd degree. """
    t2 = t * t
    _1_minus_t = 1.0 - t
    _1_minus_t_square = _1_minus_t * _1_minus_t
    a = _1_minus_t_square * _1_minus_t
    b = 3.0 * _1_minus_t_square * t
    c = 3.0 * _1_minus_t * t2
    d = t2 * t
    return a, b, c, d


@lru_cache(maxsize=300)
def bernstein3_d1(t: float) -> Sequence[float]:
    """ First derivative of Bernstein polynom of 3rd degree. """
    t2 = t * t
    a = -3.0 * (1.0 - t) ** 2
    b = 3.0 * (1.0 - 4.0 * t + 3.0 * t2)
    c = 3.0 * t * (2.0 - 3.0 * t)
    d = 3.0 * t2
    return a, b, c, d


class Bezier4P:
    """ Implements an optimized cubic `Bézier curve`_ for exact 4 control points.

    A `Bézier curve`_ is a parametric curve, parameter `t` goes from 0 to 1,
    where 0 is the first control point and 1 is the fourth control point.

    Special behavior:

        - 2D control points in, returns 2D results as :class:`~ezdxf.math.Vec2` objects
        - 3D control points in, returns 3D results as :class:`~ezdxf.math.Vec3` objects
        - Object is immutable.

    Args:
        defpoints: iterable of definition points as :class:`Vec2` or
            :class:`Vec3` compatible objects.

    """

    def __init__(self, defpoints: Sequence['Vertex']):
        if len(defpoints) == 4:
            is3d = any(len(p) > 2 for p in defpoints)
            vector_class = Vec3 if is3d else Vec2
            self._control_points = vector_class.tuple(defpoints)
        else:
            raise ValueError("Four control points required.")

    @property
    def control_points(self) -> Sequence[Union[Vec3, Vec2]]:
        """ Control points as tuple of :class:`~ezdxf.math.Vec3` or
        :class:`~ezdxf.math.Vec2` objects.
        """
        return self._control_points

    def tangent(self, t: float) -> Union[Vec3, Vec2]:
        """ Returns direction vector of tangent for location `t` at the
        Bèzier-curve.

        Args:
            t: curve position in the range ``[0, 1]``

        """
        check_if_in_valid_range(t)
        return self._get_curve_tangent(t)

    def point(self, t: float) -> Union[Vec3, Vec2]:
        """ Returns point for location `t`` at the Bèzier-curve.

        Args:
            t: curve position in the range ``[0, 1]``

        """
        check_if_in_valid_range(t)
        return self._get_curve_point(t)

    def approximate(self, segments: int) -> Iterable[Union[Vec3, Vec2]]:
        """ Approximate `Bézier curve`_ by vertices, yields `segments` + 1
        vertices as ``(x, y[, z])`` tuples.

        Args:
            segments: count of segments for approximation

        """
        if segments < 1:
            raise ValueError(segments)
        delta_t = 1. / segments
        yield self._control_points[0]
        for segment in range(1, segments):
            yield self._get_curve_point(delta_t * segment)
        yield self._control_points[3]

    def flattening(self, distance: float,
                   segments: int = 4) -> Iterable[Union[Vec3, Vec2]]:
        """ Adaptive recursive flattening. The argument `segments` is the
        minimum count of approximation segments, if the distance from the center
        of the approximation segment to the curve is bigger than `distance` the
        segment will be subdivided.

        Args:
            distance: maximum distance from the center of the cubic (C3)
                curve to the center of the linear (C1) curve between two
                approximation points to determine if a segment should be
                subdivided.
            segments: minimum segment count

        .. versionadded:: 0.15

        """

        def subdiv(start_point, end_point, start_t: float, end_t: float):
            mid_t = (start_t + end_t) * 0.5
            mid_point = self._get_curve_point(mid_t)
            chk_point = start_point.lerp(end_point)
            # center point point is faster than projecting mid point onto
            # vector start -> end:
            if chk_point.distance(mid_point) < distance:
                yield end_point
            else:
                yield from subdiv(start_point, mid_point, start_t, mid_t)
                yield from subdiv(mid_point, end_point, mid_t, end_t)

        dt = 1.0 / segments
        t0 = 0.0
        start_point = self._control_points[0]
        yield start_point
        while t0 < 1.0:
            t1 = t0 + dt
            if math.isclose(t1, 1.0):
                end_point = self._control_points[3]
                t1 = 1.0
            else:
                end_point = self._get_curve_point(t1)
            yield from subdiv(start_point, end_point, t0, t1)
            t0 = t1
            start_point = end_point

    def _get_curve_point(self, t: float) -> Union[Vec3, Vec2]:
        b1, b2, b3, b4 = self._control_points
        a, b, c, d = bernstein3(t)
        return b1 * a + b2 * b + b3 * c + b4 * d

    def _get_curve_tangent(self, t: float) -> Union[Vec3, Vec2]:
        b1, b2, b3, b4 = self._control_points
        a, b, c, d = bernstein3_d1(t)
        return b1 * a + b2 * b + b3 * c + b4 * d

    def approximated_length(self, segments: int = 128) -> float:
        """ Returns estimated length of Bèzier-curve as approximation by line
        `segments`.
        """
        length = 0.
        prev_point = None
        for point in self.approximate(segments):
            if prev_point is not None:
                length += prev_point.distance(point)
            prev_point = point
        return length

    def reverse(self) -> 'Bezier4P':
        """ Returns a new Bèzier-curve with reversed control point order. """
        return Bezier4P(list(reversed(self.control_points)))

    def transform(self, m: Matrix44) -> 'Bezier4P':
        """ General transformation interface, returns a new :class:`Bezier4p`
        curve and it is always a 3D curve.

        Args:
             m: 4x4 transformation matrix (:class:`ezdxf.math.Matrix44`)

        .. versionadded:: 0.14

        """
        if len(self._control_points[0]) == 2:
            defpoints = Vec3.generate(self._control_points)
        else:
            defpoints = self._control_points

        defpoints = tuple(m.transform_vertices(defpoints))
        return Bezier4P(defpoints)
