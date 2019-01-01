# -*- coding: utf-8 -*-
# Copyright (c) Vispy Development Team. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.


"""
Simple boxed ellipse visual based on two PolygonVisuals
"""

from __future__ import division

import numpy as np
from .polygon import PolygonVisual
from .ellipse import EllipseVisual
from vispy.visuals.visual import CompoundVisual
from vispy.color import Color


class EllipseBoxVisual(CompoundVisual):
    """
    Displays a 2D elipse with a bounding box
    Parameters
    ----------
    pos : array
        Set of vertices defining the polygon.
    color : str | tuple | list of colors
        Fill color of the polygon.
    border_color : str | tuple | list of colors
        Border color of the polygon.
    border_width : int
        Border width in pixels.
        Line widths > 1px are only
        guaranteed to work when using `border_method='agg'` method.
    vertex_size : int
        Vertex size in pixels.
    vertices : bool
        Bool to show vertices or not.
    border_method : str
        Mode to use for drawing the border line (see `LineVisual`).
            * "agg" uses anti-grain geometry to draw nicely antialiased lines
              with proper joins and endcaps.
            * "gl" uses OpenGL's built-in line rendering. This is much faster,
              but produces much lower-quality results and is not guaranteed to
              obey the requested line width or join/endcap styles.
    triangulate : boolean
        Triangulate the set of vertices
    **kwargs : dict
        Keyword arguments to pass to `CompoundVisual`.
    """
    def __init__(self, pos=None, color='black', box_color=None,
                 border_color=None, border_width=1, num_segments=100,
                 border_method='gl', **kwargs):

        self._pos = pos
        self._box_color = Color(None)
        self._box_width = 1
        self._box_border_color = Color(box_color)
        self._box_vertex_edge_color = Color(box_color)
        if self._box_border_color.is_blank:
            self._box_vertex_color = Color(None)
        else:
            self._box_vertex_color = Color('white')
        self._box_vertex_size = 7
        self._box_vertex_symbol = 'square'

        self._start_angle = 0.
        self._span_angle = 360.
        self._num_segments = num_segments
        self._color = Color(color)
        self._border_color = Color(border_color)
        self._border_width = border_width
        self._set_center()

        self._ellipse = EllipseVisual()
        self._box = PolygonVisual(border_method=border_method, triangulate=True)

        self._update()
        CompoundVisual.__init__(self, [self._ellipse, self._box], **kwargs)



    def _set_center(self):
        if self._pos is None:
            self._center = None
            self._radius = (None, None)
        else:
            self._center = [(self._pos[0][0]+self._pos[2][0])/2, (self._pos[0][1]+self._pos[2][1])/2]
            self._radius = ([(self._pos[2][0]-self._pos[0][0])/2, (self._pos[2][1]-self._pos[0][1])/2])

    def _update(self):
        self._box.set_data(pos=self._pos, color=self._box_color,
            vertex_color=self._box_vertex_color, border_color=self._box_border_color,
            border_width=self._box_width, vertex_size=self._box_vertex_size,
            vertex_symbol=self._box_vertex_symbol, vertex_edge_color=self._box_vertex_edge_color)

        self._ellipse.set_data(center=self._center, color=self._color, border_color=self._border_color,
             border_width=self._border_width, radius=self._radius, start_angle=self._start_angle,
             span_angle=self._span_angle, num_segments=self._num_segments)

    def set_data(self, pos=None, color='black', box_color=None,
            border_color=None, border_width=1, num_segments=100):

        self._pos = pos
        self._box_border_color = Color(box_color)
        self._box_vertex_edge_color = Color(box_color)
        if self._box_border_color.is_blank:
            self._box_vertex_color = Color(None)
        else:
            self._box_vertex_color = Color('white')
        self._num_segments = num_segments
        self._color = Color(color)
        self._border_color = Color(border_color)
        self._border_width = border_width
        self._set_center()
        self._update()
