# -*- coding: utf-8 -*-
# Copyright (c) Vispy Development Team. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.


"""
Simple polygon visual based on MeshVisual, LineVisual, and MarkersVisual
"""

from __future__ import division

import numpy as np

from vispy.visuals.visual import CompoundVisual
from vispy.visuals.mesh import MeshVisual
from vispy.visuals.line import LineVisual
from vispy.visuals.markers import MarkersVisual
from vispy.color import Color
from vispy.geometry import PolygonData
from vispy.gloo import set_state

from .ellipseBox import EllipseBoxVisual

class EllipseBoxListVisual(CompoundVisual):
    """
    Displays 2D ellipses
    Parameters
    ----------
    pos : list
        List of set of vertices defining the polygon.
    color : str | tuple | list of colors
        Fill color of the polygon.
    border_color : str | tuple | list of colors
        Border color of the polygon.
    border_width : int
        Border width in pixels.
        Line widths > 1px are only
        guaranteed to work when using `border_method='agg'` method.
    num_segments : int
        Vertex size in pixels.
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
        if isinstance(color, list):
            self._color = [Color(c) for c in color]
        else:
            self._color = Color(color)
        if isinstance(box_color, list):
            self._box_color = [Color(c) for c in box_color]
        else:
            self._box_color = Color(box_color)
        if isinstance(border_color, list):
            self._border_color = [Color(c) for c in border_color]
        else:
            self._border_color = Color(border_color)

        self._border_width = border_width
        self._num_segments = num_segments
        self._border_method = border_method

        self._update()
        CompoundVisual.__init__(self, [], **kwargs)

        self.freeze()

    def _update(self):
        if self.pos is None:
            return

        len_pos = len(self.pos)
        len_visual = len(self._subvisuals)
        for i in range(min(len_pos,len_visual)):
            if isinstance(self.color, list):
                color = self.color[i]
            else:
                color = self.color
            if isinstance(self.box_color, list):
                box_color = self.box_color[i]
            else:
                box_color = self.box_color
            if isinstance(self.border_color, list):
                border_color = self.border_color[i]
            else:
                border_color = self.border_color

            self._subvisuals[i].set_data(
                pos=self.pos[i], color=color, box_color=box_color,
                border_color=border_color, border_width=self._border_width,
                num_segments=self._num_segments)
            self._subvisuals[i].update()

        for i in range(len_pos, len_visual):
             self.remove_subvisual(self._subvisuals[i])

        for i in range(len_visual, len_pos):
            if isinstance(self.color, list):
                color = self.color[i]
            else:
                color = self.color
            if isinstance(self.box_color, list):
                box_color = self.box_color[i]
            else:
                box_color = self.box_color
            if isinstance(self.border_color, list):
                border_color = self.border_color[i]
            else:
                border_color = self.border_color
            self.add_subvisual(EllipseBoxVisual(
                pos=self.pos[i], color=color, box_color=box_color,
                border_color=border_color, border_width=self._border_width,
                num_segments=self._num_segments, border_method=self._border_method))
    @property
    def pos(self):
        """ The vertex position of the polygon.
        """
        return self._pos

    @pos.setter
    def pos(self, pos):
        self._pos = pos
        self._update()

    @property
    def color(self):
        """ The color of the polygon.
        """
        return self._color

    @color.setter
    def color(self, color):
        if isinstance(color, list):
            self._color = [Color(c, clip=True) for c in color]
        else:
            self._color = Color(color, clip=True)
        self._update()

    @property
    def border_color(self):
        """ The border color of the polygon.
        """
        return self._border_color

    @border_color.setter
    def border_color(self, border_color):
        if isinstance(border_color, list):
            self._border_color = [Color(c) for c in border_color]
        else:
            self._border_color = Color(border_color)
        self._update()

    @property
    def box_color(self):
        """ The vertex color of the polygon.
        """
        return self._box_color

    @box_color.setter
    def box_color(self, box_color):
        if isinstance(box_color, list):
            self._box_color = [Color(c) for c in box_color]
        else:
            self._box_color = Color(box_color)
        self._update()

    def set_data(self, pos=None, color='black', box_color=None,
                 border_color=None, border_width=1,
                 num_segments=100, triangulate=True):
        """Set the data used to draw this visual.
            Parameters
            ----------
            pos : list
                List of set of vertices defining the polygon.
            color : str | tuple | list of colors
                Fill color of the polygon.
            border_color : str | tuple | list of colors
                Border color of the polygon.
            box_color : str | tuple | list of colors
                Vertex color of the polygon.
            border_width : int
                Border width in pixels.
                Line widths > 1px are only
                guaranteed to work when using `border_method='agg'` method.
            num_segments : int
                Vertex size in pixels.
            border_method : str
                Mode to use for drawing the border line (see `LineVisual`).
                    * "agg" uses anti-grain geometry to draw nicely antialiased lines
                      with proper joins and endcaps.
                    * "gl" uses OpenGL's built-in line rendering. This is much faster,
                      but produces much lower-quality results and is not guaranteed to
                      obey the requested line width or join/endcap styles.
            triangulate : boolean
                Triangulate the set of vertices
        """
        self._pos = pos
        if isinstance(color, list):
            self._color = [Color(c) for c in color]
        else:
            self._color = Color(color)
        self._border_width = border_width
        self._num_segments = num_segments
        if isinstance(border_color, list):
            self._border_color = [Color(c) for c in border_color]
        else:
            self._border_color = Color(border_color)
        if isinstance(box_color, list):
            self._box_color = [Color(c) for c in box_color]
        else:
            self._box_color = Color(box_color)
        self._update()
