from typing import Union
from collections import Iterable

import numpy as np
from numpy import clip, integer, ndarray, append, insert, delete, empty
from copy import copy

from ._base_layer import Layer
from ._register import add_to_viewer
from .._vispy.scene.visuals import PolygonList as ShapeNode
from vispy.color import get_color_names

from .qt import QtRectanglesLayer as QtShapeLayer

@add_to_viewer
class Rectangles(Layer):
    """Rectangles layer.

    Parameters
    ----------
    coords : np.ndarray
        List of vertices defining rectangles.

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

        visual = ShapeNode(border_method='gl')
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

        self.name = 'rectangles'
        self._qt = QtShapeLayer(self)
        self._selected_shapes = None
        self._selected_shapes_stored = None
        self._ready_to_create_box = False
        self._creating_box = False
        self._create_tl = None
        self._drag_start = None
        self._fixed = None
        self._fixed_aspect = False
        self._aspect_ratio = 1
        self.highlight = False
        self._is_moving=False
        self._fixed_index = 0
        self._view_data = None

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

    def _expand_bounding_box(self, box):
        tl = np.array([min(box[0][0],box[1][0]), min(box[0][1],box[1][1])])
        tr = np.array([max(box[0][0],box[1][0]), min(box[0][1],box[1][1])])
        br = np.array([max(box[0][0],box[1][0]), max(box[0][1],box[1][1])])
        bl = np.array([min(box[0][0],box[1][0]), max(box[0][1],box[1][1])])
        return [tl, (tl+tr)/2, tr, (tr+br)/2, br, (br+bl)/2, bl, (bl+tl)/2]

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

    def _get_selected_shapes(self, indices):
        """Determines if any shapes at given indices.

        Parameters
        ----------
        indices : sequence of int
            Indices to check if shape at.
        """
        in_slice_boxes, matches = self._slice_boxes(indices)

        # Check boxes if there are any in this slice
        if len(in_slice_boxes) > 0:
            matches = matches.nonzero()[0]
            boxes = []
            for box in in_slice_boxes:
                boxes.append(self._expand_bounding_box(box))
            in_slice_boxes = np.array(boxes)

            offsets = np.broadcast_to(indices[:2], (len(in_slice_boxes), 8, 2)) - in_slice_boxes
            distances = abs(offsets)

            # Get the vertex sizes
            sizes = self.size

            # Check if any matching vertices
            in_slice_matches = np.less_equal(distances, np.broadcast_to(sizes/2, (2, 8, len(in_slice_boxes))).T)
            in_slice_matches = np.all(in_slice_matches, axis=2)
            indices = in_slice_matches.nonzero()

            if len(indices[0]) > 0:
                matches = matches[indices[0][-1]]
                vertex = indices[1][-1]
                return [matches, vertex]
            else:
                # If no matching vertex check if index inside bounding box
                in_slice_matches = np.all(np.array([np.all(offsets[:,0]>=0, axis=1), np.all(offsets[:,4]<=0, axis=1)]), axis=0)
                indices = in_slice_matches.nonzero()
                if len(indices[0]) > 0:
                    matches = matches[indices[0][-1]]
                    return [matches, None]
                else:
                    return None
        else:
            return None

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
                boxes.append(self._expand_bounding_box(box))

            # Update the boxes node
            data = np.array(boxes) + 0.5
            #data = data[0]
        else:
            # if no markers in this slice send dummy data
            data = np.empty((0, 2))


        self._view_data = data
        self._node.set_data(
            data, border_width=self.edge_width, vertex_color=None,
            vertex_edge_color=None,
            border_color=self.edge_color, color=self.face_color, vertex_size=0)
        self._need_visual_update = True
        self._set_highlight()
        self._update()

    def _set_highlight(self):
        if self.highlight and self._selected_shapes is not None:
            data = self._view_data[self._selected_shapes[0]].mean(axis=0)
            self._highlight_node.set_data(np.array([data]), size=10, face_color='red')
        else:
            self._highlight_node.set_data(np.empty((0, 2)), size=0)

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
        value = self._get_selected_shapes(coord)
        coord_shift = copy(coord)
        coord_shift[0] = coord[1]
        coord_shift[1] = coord[0]
        msg = f'{coord_shift}'
        if value is None:
            pass
        else:
            msg = msg + ', %s, index %d' % (self.name, value[0])
            # if value[1] is None:
            #     pass
            # else:
            #     msg = msg + ', vertex %d' % value[1]
        return coord, value, msg

    def _add(self, coord, br=None):
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

        if br is None:
            tl = [coord[0]-25, coord[1]-25, *coord[2:]]
            br = [coord[0]+25, coord[1]+25, *coord[2:]]
            index = None
        else:
            tl = coord
            br = br
            if br[0] == tl[0]:
                br[0] = tl[0]+1
            if br[1] == tl[1]:
                br[1] = tl[1]+1
            index = 2

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

        # print('to_add', [[tl, br]])
        # print('data', self.data)
        # print('index', index)
        self.data = append(self.data, [[tl, br]], axis=0)
        self._selected_shapes = [len(self.data)-1, index]
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
        index = self._selected_shapes
        if index is None:
            pass
        else:
            self.data = delete(self.data, index[0], axis=0)
            self._selected_shapes = self._get_selected_shapes(coord)
            self._refresh()

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
        self._is_moving=True
        index = self._selected_shapes
        if index is None:
            pass
        else:
            if index[1] is None:
                box = self._expand_box(self.data[index[0]])

                #Check where dragging box from
                if self._drag_start is None:
                    tl = [coord[0] - (box[2][0]-box[0][0])/2, coord[1] - (box[2][1]-box[0][1])/2]
                    br = [coord[0] + (box[2][0]-box[0][0])/2, coord[1] + (box[2][1]-box[0][1])/2]
                else:
                    tl = [box[0][0] - (self._drag_start[0]-coord[0]), box[0][1] - (self._drag_start[1]-coord[1])]
                    br = [box[2][0] - (self._drag_start[0]-coord[0]), box[2][1] - (self._drag_start[1]-coord[1])]
                    self._drag_start = coord

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
                box = self._expand_bounding_box(self.data[index[0]])
                if self._fixed is None:
                    self._fixed_index = np.mod(index[1]+4,8)
                    self._fixed = box
                    self._aspect_ratio = (box[4][1]-box[0][1])/(box[4][0]-box[0][0])

                if np.mod(self._fixed_index, 2) == 0:
                    # corner selected
                    br = self._fixed[self._fixed_index]
                    tl = coord
                elif np.mod(self._fixed_index, 4) == 1:
                    # top selected
                    br = self._fixed[np.mod(self._fixed_index-1,8)]
                    tl = [self._fixed[np.mod(self._fixed_index+1,8)][0], coord[1]]
                else:
                    # side selected
                    br = self._fixed[np.mod(self._fixed_index-1,8)]
                    tl = [coord[0], self._fixed[np.mod(self._fixed_index+1,8)][1]]

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

                if self._fixed_aspect:
                    ratio = abs((tl[1]-br[1])/(tl[0]-br[0]))
                    if np.mod(self._fixed_index, 2) == 0:
                        # corner selected
                        if ratio>self._aspect_ratio:
                            tl[1] = br[1]+(tl[1]-br[1])*self._aspect_ratio/ratio
                        else:
                            tl[0] = br[0]+(tl[0]-br[0])*ratio/self._aspect_ratio

                self.data[index[0]] = [tl, br]

            self.highlight = True
            self._selected_shapes_stored = index
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
        if self._selected_shapes == self._selected_shapes_stored:
            return

        if self._selected_shapes is None:
            self.highlight = False
        else:
            self.highlight = True
        self._selected_shapes_stored = self._selected_shapes
        self._set_highlight()


    def _unselect(self):
        if self.highlight:
            self.highlight = False
            self._selected_shapes_stored = None
            self._refresh()

    def interact(self, position, indices, mode=True, dragging=False, shift=False, ctrl=False,
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
        if not self._fixed_aspect == shift:
            self._fixed_aspect = shift
            if self._is_moving:
                coord = self._get_coord(position, indices)
                self._move(coord)

        if mode is None:
            #If not in edit or addition mode unselect all
            self._unselect()
        elif mode == 'edit':
            #If in edit mode
            coord = self._get_coord(position, indices)
            if pressed and not ctrl:
                #Set coordinate of initial drag
                self._selected_shapes = self._get_selected_shapes(coord)
                self._drag_start = coord
            elif pressed and ctrl:
                #Delete an existing box if any on control press
                self._selected_shapes = self._get_selected_shapes(coord)
                self._remove(coord)
            elif moving and dragging:
                #Drag an existing box if any
                self._move(coord)
            elif released:
                self._is_moving=False
            elif self._is_moving:
                pass
            else:
                #Highlight boxes if any an over
                self._selected_shapes = self._get_selected_shapes(coord)
                self._select(coord)
                self._fixed = None
        elif mode == 'add':
            #If in addition mode
            coord = self._get_coord(position, indices)
            if pressed:
                #Start add a new box
                self._ready_to_create_box = True
                self._creating_box = False
                self._create_tl = coord
            elif moving and dragging:
                #If moving and dragging check if ready to make new box
                if self._ready_to_create_box:
                    self.highlight = True
                    self._add(self._create_tl, coord)
                    self._ready_to_create_box = False
                    self._creating_box = True
                elif self._creating_box:
                    #If making a new box, update it's position
                    self._move(coord)
            elif released and dragging:
                #One release add new box
                if self._creating_box:
                    self._creating_box = False
                    self._unselect()
                    self._fixed = None
                else:
                    self._add(coord)
                    self._ready_to_create_box = False
                self._is_moving=False
            elif released:
                self._is_moving=False
            else:
                self._unselect()
        else:
            pass
