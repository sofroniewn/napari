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


class PolygonVisual(CompoundVisual):
    """
    Displays a 2D polygon
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
    def __init__(self, pos=None, color='black', vertex_color=None,
                 border_color=None, border_width=1, vertex_size=10,
                 border_method='gl', triangulate=True, **kwargs):
        self._mesh = MeshVisual()
        self._border = LineVisual(method=border_method)
        self._vertices = MarkersVisual()
        self._pos = pos
        self._color = Color(color)
        self._border_width = border_width
        self._border_color = Color(border_color)
        self._triangulate = triangulate
        self._vertex_size = vertex_size
        self._vertex_color = Color(vertex_color)

        self._update()
        CompoundVisual.__init__(self, [self._mesh, self._border, self._vertices], **kwargs)

        self._mesh.set_gl_state(polygon_offset_fill=True,
                                polygon_offset=(1, 1), cull_face=False)
        self.freeze()

    def _update(self):
        if self._pos is None:
            return
        if not self._color.is_blank and self._triangulate:
            data = PolygonData(vertices=np.array(self._pos, dtype=np.float32))
            pts, tris = data.triangulate()
            set_state(polygon_offset_fill=False)
            self._mesh.set_data(vertices=pts, faces=tris.astype(np.uint32),
                                color=self._color.rgba)
        elif not self._color.is_blank:
            self.mesh.set_data(vertices=self._pos,
                               color=self._color.rgba)

        if not self._border_color.is_blank:
            # Close border if it is not already.
            border_pos = self._pos
            if np.any(border_pos[0] != border_pos[-1]):
                border_pos = np.concatenate([border_pos, border_pos[:1]],
                                            axis=0)
            self._border.set_data(pos=border_pos,
                                  color=self._border_color.rgba,
                                  width=self._border_width)
            self._border.update()

        if not self._vertex_color.is_blank:
            self._vertices.set_data(pos=self._pos, size=self._vertex_size,
                                  face_color=self._vertex_color.rgba,
                                  edge_width=0, scaling=True)
            self._vertices.update()

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
        self._color = Color(color, clip=True)
        self._update()

    @property
    def border_color(self):
        """ The border color of the polygon.
        """
        return self._border_color

    @border_color.setter
    def border_color(self, border_color):
        self._border_color = Color(border_color)
        self._update()

    @property
    def vertex_color(self):
        """ The vertex color of the polygon.
        """
        return self._vertex_color

    @vertex_color.setter
    def vertex_color(self, vertex_color):
        self._vertex_color = Color(vertex_color)
        self._update()

    @property
    def mesh(self):
        """The vispy.visuals.MeshVisual that is owned by the PolygonVisual.
           It is used to fill in the polygon
        """
        return self._mesh

    @mesh.setter
    def mesh(self, mesh):
        self._mesh = mesh
        self._update()

    @property
    def border(self):
        """The vispy.visuals.LineVisual that is owned by the PolygonVisual.
           It is used to draw the border of the polygon
        """
        return self._border

    @border.setter
    def border(self, border):
        self._border = border
        self._update()

    @property
    def vertices(self):
        """The vispy.visuals.MarkersVisual that is owned by the PolygonVisual.
           It is used to draw the vertices of the polygon
        """
        return self._vertices

    @vertices.setter
    def vertices(self, vertices):
        self._vertices = vertices
        self._update()

    def set_data(self, pos=None, color='black', vertex_color=None,
                 border_color=None, border_width=1,
                 vertex_size=10, triangulate=True):
        """Set the data used to draw this visual.
            Parameters
            ----------
            pos : array
                Set of vertices defining the polygon.
            color : str | tuple | list of colors
                Fill color of the polygon.
            border_color : str | tuple | list of colors
                Border color of the polygon.
            vertex_color : str | tuple | list of colors
                Vertex color of the polygon.
            border_width : int
                Border width in pixels.
                Line widths > 1px are only
                guaranteed to work when using `border_method='agg'` method.
            vertex_size : int
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
        self._color = Color(color)
        self._border_width = border_width
        self._vertex_size = vertex_size
        self._border_color = Color(border_color)
        self._vertex_color = Color(vertex_color)
        self._triangulate = triangulate
        self._update()
