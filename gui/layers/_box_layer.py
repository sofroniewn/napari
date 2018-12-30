from typing import Union
from collections import Iterable

import numpy as np
from numpy import clip, integer, ndarray, append, insert, delete, empty
from copy import copy

from ._base_layer import Layer
from ._register import add_to_viewer
from .._vispy.scene.visuals import PolygonList as PolygonNode
from vispy.color import get_color_names

from .qt import QtBoxLayer

@add_to_viewer
class Box(Layer):
    """Bounding box layer.

    Parameters
    ----------
    coords : np.ndarray
        Set of vertices defining the box.

    border_width : int
        border width in pixels.

    color : Color, ColorArray
        fill color of the box

    border_color : Color, ColorArray
        border color of the box

    See vispy's polygon visual docs for more details:
    http://api.vispy.org/en/latest/visuals.html#vispy.visuals.PolygonVisual



    """

    def __init__(self, coords, edge_width=1, size=10, vertex_color = 'black', edge_color='black', face_color='white'):

        visual = PolygonNode(border_method='agg')
        super().__init__(visual)

        # Save the bbox coordinates
        self._coords = coords

        # Save the marker style params
        self._edge_width = edge_width
        self._size = size
        self._edge_color = edge_color
        self._face_color = face_color
        self._vertex_color = vertex_color
        self._colors = get_color_names()

        # update flags
        self._need_display_update = False
        self._need_visual_update = False

        self.name = 'box'
        self._qt = QtBoxLayer(self)
        self._selected_boxes = None
        self._selected_boxes_stored = None
        self.highlight = False

    @property
    def coords(self) -> np.ndarray:
        """ndarray: coordinates of the box
        """
        return self._coords

    @coords.setter
    def coords(self, coords: np.ndarray):
        self._coords = coords

        self.viewer._child_layer_changed = True
        self._refresh()

    @property
    def data(self) -> np.ndarray:
        """ndarray: coordinates of the box
        """
        return self._coords

    @data.setter
    def data(self, data: np.ndarray) -> None:
        self.coords = data

    @property
    def edge_width(self) -> int:
        """int: width of the border edge in px
        """

        return self._edge_width

    @edge_width.setter
    def edge_width(self, edge_width: int) -> None:
        self._edge_width = edge_width

        self.refresh()

    @property
    def size(self) -> int:
        """int: width of vertices in px
        """

        return self._size

    @size.setter
    def size(self, size: int) -> None:
        self._size = size

        self.refresh()

    @property
    def vertex_color(self) -> str:
        """Color, ColorArray: the box vertex color
        """

        return self._vertex_color

    @vertex_color.setter
    def vertex_color(self, vertex_color: str) -> None:
        self._vertex_color = vertex_color

        self.refresh()

    @property
    def edge_color(self) -> str:
        """Color, ColorArray: the box edge color
        """

        return self._edge_color

    @edge_color.setter
    def edge_color(self, edge_color: str) -> None:
        self._edge_color = edge_color

        self.refresh()

    @property
    def face_color(self) -> str:
        """Color, ColorArray: the box face color
        """

        return self._face_color

    @face_color.setter
    def face_color(self, face_color: str) -> None:
        self._face_color = face_color

        self.refresh()

    def _get_shape(self):
        if len(self.coords) == 0:
            return np.ones(self.coords.shape[2:],dtype=int)
        else:
            return np.max(self.coords, axis=(0,1)) + 1

    def _update(self):
        """Update the underlying visual.
        """
        if self._need_display_update:
            self._need_display_update = False

            self._set_view_slice(self.viewer.dimensions.indices)

        if self._need_visual_update:
            self._need_visual_update = False
            self._node.update()

    def _refresh(self):
        """Fully refresh the underlying visual.
        """
        self._need_display_update = True
        self._update()

    def _expand_box(self, box):
        tl = [min(box[0][0],box[1][0]), min(box[0][1],box[1][1])]
        tr = [max(box[0][0],box[1][0]), min(box[0][1],box[1][1])]
        br = [max(box[0][0],box[1][0]), max(box[0][1],box[1][1])]
        bl = [min(box[0][0],box[1][0]), max(box[0][1],box[1][1])]
        return [tl, tr, br, bl]

    def _slice_boxes(self, indices):
        """Determines the slice of boxes given the indices.

        Parameters
        ----------
        indices : sequence of int or slice
            Indices to slice with.
        """
        # Get a list of the coords for the markers in this slice
        coords = self.coords
        if len(coords) > 0:
            matches = np.equal(
                coords[:, :, 2:],
                np.broadcast_to(indices[2:], (len(coords), 2, len(indices) - 2)))

            matches = np.all(matches, axis=(1,2))

            in_slice_boxes = coords[matches, :, :2]
            return in_slice_boxes, matches
        else:
            return [], []

    def _set_selected_boxes(self, indices):
        """Determines selected boxes selected given indices.

        Parameters
        ----------
        indices : sequence of int
            Indices to check if box at.
        """
        in_slice_boxes, matches = self._slice_boxes(indices)

        # Check boxes if there are any in this slice
        if len(in_slice_boxes) > 0:
            matches = matches.nonzero()[0]
            boxes = []
            for box in in_slice_boxes:
                boxes.append(self._expand_box(box))
            in_slice_boxes = np.array(boxes)

            offsets = np.broadcast_to(indices[:2], (len(in_slice_boxes), 4, 2)) - in_slice_boxes
            distances = abs(offsets)

            # Get the vertex sizes
            sizes = self.size

            # Check if any matching vertices
            in_slice_matches = np.less_equal(distances, np.broadcast_to(sizes/2, (2, 4, len(in_slice_boxes))).T)
            in_slice_matches = np.all(in_slice_matches, axis=2)
            indices = in_slice_matches.nonzero()

            if len(indices[0]) > 0:
                matches = matches[indices[0][-1]]
                vertex = indices[1][-1]
            else:
                # If no matching vertex check if index inside bounding box
                in_slice_matches = np.all(np.array([np.all(offsets[:,0]>=0, axis=1), np.all(offsets[:,2]<=0, axis=1)]), axis=0)
                indices = in_slice_matches.nonzero()
                if len(indices[0]) > 0:
                    matches = matches[indices[0][-1]]
                    vertex = None
                else:
                    matches = None
                    vertex = None
        else:
            matches = None
            vertex = None

        if matches is None:
            self._selected_boxes = None
        else:
            self._selected_boxes = [matches, vertex]

    def _set_view_slice(self, indices):
        """Sets the view given the indices to slice with.

        Parameters
        ----------
        indices : sequence of int or slice
            Indices to slice with.
        """

        in_slice_boxes, matches = self._slice_boxes(indices)

        # Display boxes if there are any in this slice
        if len(in_slice_boxes) > 0:
            boxes = []
            for box in in_slice_boxes:
                boxes.append(self._expand_box(box))

            # Update the boxes node
            data = np.array(boxes) + 0.5
            #data = data[0]
        else:
            # if no markers in this slice send dummy data
            data = np.empty((0, 2))

        if self.highlight and self._selected_boxes is not None:
            vertex_color = [self.vertex_color for i in range(len(data))]
            edge_color = [self.edge_color for i in range(len(data))]
            face_color = [self.face_color for i in range(len(data))]
            if self._selected_boxes[1] is None:
                edge_color[self._selected_boxes[0]] = 'red'
                face_color[self._selected_boxes[0]] = 'red'
            else:
                vertex_color[self._selected_boxes[0]] = 'red'
            self._node.set_data(
                data, border_width=self.edge_width, vertex_color=vertex_color,
                border_color=edge_color, color=face_color, size=self.size)
        else:
            self._node.set_data(
                data, border_width=self.edge_width, vertex_color=self.vertex_color,
                border_color=self.edge_color, color=self.face_color, size=self.size)
        self._need_visual_update = True
        self._update()

    def _get_coord(self, position, indices):
        max_shape = self.viewer.dimensions.max_shape
        transform = self.viewer._canvas.scene.node_transform(self._node)
        pos = transform.map(position)
        pos = [clip(pos[1],0,max_shape[0]-1), clip(pos[0],0,max_shape[1]-1)]
        coord = copy(indices)
        coord[0] = int(pos[1])
        coord[1] = int(pos[0])
        return coord

    def get_value(self, position, indices):
        """Returns coordinates, values, and a string
        for a given mouse position and set of indices.

        Parameters
        ----------
        position : sequence of two int
            Position of mouse cursor in canvas.
        indices : sequence of int or slice
            Indices that make up the slice.

        Returns
        ----------
        coord : sequence of int
            Position of mouse cursor in data.
        value : int or float or sequence of int or float
            Value of the data at the coord.
        msg : string
            String containing a message that can be used as
            a status update.
        """
        coord = self._get_coord(position, indices)
        self._set_selected_boxes(coord)
        value = self._selected_boxes
        coord_shift = copy(coord)
        coord_shift[0] = coord[1]
        coord_shift[1] = coord[0]
        msg = f'{coord_shift}'
        if value is None:
            pass
        else:
            msg = msg + ', %s, index %d' % (self.name, value[0])
            if value[1] is None:
                pass
            else:
                msg = msg + ', vertex %d' % value[1]
        return coord, value, msg

    def _add(self, coord):
        """Returns coordinates, values, and a string
        for a given mouse position and set of indices.

        Parameters
        ----------
        position : sequence of two int
            Position of mouse cursor in canvas.
        indices : sequence of int or slice
            Indices that make up the slice.
        """
        max_shape = self.viewer.dimensions.max_shape
        tl = [coord[0]-25, coord[1]-25]
        br = [coord[0]+25, coord[1]+25]
        if br[0] > max_shape[0]-1:
            br[0] = max_shape[0]-1
            tl[0] = max_shape[0]-1-50
        if br[1] > max_shape[1]-1:
            br[1] = max_shape[1]-1
            tl[1] = max_shape[1]-1-50
        if tl[0] < 0:
            br[0] = 50
            tl[0] = 0
        if tl[1] < 0:
            br[1] = 50
            tl[1] = 0

        self.data = append(self.data, [[tl, br]], axis=0)
        self._selected_boxes = [len(self.data)-1, None]
        self._refresh()

    def _remove(self, coord):
        """Returns coordinates, values, and a string
        for a given mouse position and set of indices.

        Parameters
        ----------
        position : sequence of two int
            Position of mouse cursor in canvas.
        indices : sequence of int or slice
            Indices that make up the slice.
        """
        index = self._selected_boxes
        if index is None:
            pass
        else:
            self._selected_boxes = None
            self.data = delete(self.data, index[0], axis=0)
            self._refresh()
            self._select(coord)

    def _move(self, coord):
        """Moves object at given mouse position
        and set of indices.

        Parameters
        ----------
        position : sequence of two int
            Position of mouse cursor in canvas.
        indices : sequence of int or slice
            Indices that make up the slice.
        """
        index = self._selected_boxes
        if index is None:
            pass
        else:
            if index[1] is None:
                box = self._expand_box(self.data[index[0]])
                tl = [coord[0] - (box[2][0]-box[0][0])/2, coord[1] - (box[2][1]-box[0][1])/2]
                br = [coord[0] + (box[2][0]-box[0][0])/2, coord[1] + (box[2][1]-box[0][1])/2]

                # block box move if goes of edge
                max_shape = self.viewer.dimensions.max_shape
                if tl[0] < 0:
                    br[0] = br[0] - tl[0]
                    tl[0] = 0
                if tl[1] < 0:
                    br[1] = br[1] - tl[1]
                    tl[1] = 0
                if br[0] > max_shape[0]-1:
                    tl[0] = max_shape[0]-1 - (br[0] - tl[0])
                    br[0] = max_shape[0]-1
                if br[1] > max_shape[1]-1:
                    tl[1] = max_shape[1]-1 - (br[1] - tl[1])
                    br[1] = max_shape[1]-1
                self.data[index[0]] = [tl, br]
            else:
                box = self._expand_box(self.data[index[0]])
                tl = coord
                br = box[np.mod(index[1]+2,4)]
                if tl[0]==br[0]:
                    if index[1] == 1 or index[1] == 2:
                        tl[0] = tl[0]+1
                    else:
                        tl[0] = tl[0]-1
                if tl[1]==br[1]:
                    if index[1] == 2 or index[1] == 3:
                        tl[1] = tl[1]+1
                    else:
                        tl[1] = tl[1]-1

                self.data[index[0]] = [tl, br]

            self.highlight = True
            self._selected_boxes_stored = index
            self._refresh()

    def _select(self, coord):
        """Highlights object at given mouse position
        and set of indices.

        Parameters
        ----------
        position : sequence of two int
            Position of mouse cursor in canvas.
        indices : sequence of int or slice
            Indices that make up the slice.
        """
        self._set_selected_boxes(coord)
        index = self._selected_boxes
        if index == self._selected_boxes_stored:
            pass
        elif index is None:
            self.highlight = False
            self._refresh()
            self._selected_boxes_stored = index
        else:
            self.highlight = True
            self._refresh()
            self._selected_boxes_stored = index

    def _unselect(self):
        if self.highlight:
            self.highlight = False
            self._selected_boxes_stored = None
            self._refresh()

    def interact(self, position, indices, annotation=True, dragging=False, shift=False, ctrl=False,
        pressed=False, released=False, moving=False):
        """Highlights object at given mouse position
        and set of indices.

        Parameters
        ----------
        position : sequence of two int
            Position of mouse cursor in canvas.
        indices : sequence of int or slice
            Indices that make up the slice.
        """
        if not annotation:
            #If not in annotation mode unselect all
            self._unselect()
        else:
            #If in annotation mode
            if pressed and not shift and not ctrl:
                #Add a new box
                coord = self._get_coord(position, indices)
                self._add(coord)
            elif pressed and ctrl:
                #Delete an existing box if any
                coord = self._get_coord(position, indices)
                self._remove(coord)
            elif moving and dragging and shift:
                #Drag an existing box if any
                coord = self._get_coord(position, indices)
                self._move(coord)
            elif shift or ctrl:
                #Highlight boxes if any
                coord = self._get_coord(position, indices)
                self._select(coord)
            else:
                #Turn off highlight mode if it was on
                self._unselect()
