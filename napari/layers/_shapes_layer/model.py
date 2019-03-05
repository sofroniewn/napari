from typing import Union
from collections import Iterable

import numpy as np
from numpy import clip, integer, ndarray, append, insert, delete, empty
from copy import copy

from ...util import is_permutation, inside_boxes, inside_triangles
from .._base_layer import Layer
from .._register import add_to_viewer
from ..._vispy.scene.visuals import Mesh
from ..._vispy.scene.visuals import Markers
from ..._vispy.scene.visuals import Line
from ..._vispy.scene.visuals import Compound as VisualNode
from .utils import ShapesData
from vispy.color import get_color_names, Color
from vispy.util.event import Event

from .view import QtShapesLayer
from .view import QtShapesControls

@add_to_viewer
class Shapes(Layer):
    """Shapes layer.
    Parameters
    ----------
    lines : np.ndarray
        Nx2x2 array of endpoints of lines.
    rectangles : np.ndarray
        Nx2x2 array of corners of rectangles.
    ellipses : np.ndarray
        Nx2x2 array of corners of ellipses.
    paths : list
        list of Nx2 arrays of points on each path.
    polygons : list
        list of Nx2 arrays of vertices of each polygon.
    edge_width : int
        width of all lines and edges in pixels.
    face_color : Color, ColorArray
        fill color of all faces
    edge_color : Color, ColorArray
        color of all lines and edges
    """

    def __init__(self, points=None, lines=None, paths=None, rectangles=None,
                 ellipses=None, polygons=None, edge_width=1, edge_color='black',
                 face_color='white', *, name=None):

        visual = VisualNode([Markers(), Line(), Mesh(), Mesh()])

        super().__init__(visual, name)

        # Freeze refreshes
        with self.freeze_refresh():
            # Save the shape data
            self._data = ShapesData(lines=lines, paths=paths, rectangles=rectangles,
                                    ellipses=ellipses, polygons=polygons,
                                    thickness=edge_width)

            # Save the style params
            self._colors = get_color_names()
            self._mesh_color_array = np.empty((len(self.data._mesh_faces), 4))
            self._edge_color_array = np.empty((self.data.count, 4))
            self._face_color_array = np.empty((self.data.count, 4))
            self.edge_width = edge_width
            self.edge_color = edge_color
            self.face_color = face_color

            self._show_meshes = np.ones(len(self.data._mesh_faces), dtype=bool)
            self.show_objects = np.ones((self.data.count, 2), dtype=bool)

            default_z_order, counts = np.unique(self.data._mesh_faces_index[:,0], return_counts=True)
            self._face_counts = counts
            self.z_order = default_z_order

            self._vertex_size = 10

            # update flags
            self._need_display_update = False
            self._need_visual_update = False

            self._highlight = True
            self._highlight_color = (0, 0.6, 1)
            self._highlight_thickness = 0.5
            self._selected_shapes = []
            self._selected_shapes_stored = []
            self._hover_shapes = [None, None]
            self._hover_shapes_stored = [None, None]

            self._drag_start = None
            self._fixed_vertex = None
            self._fixed_aspect = False
            self._selected_vertex = [None, None]
            self._aspect_ratio = 1
            self._is_moving=False
            self._fixed_index = 0
            self._is_selecting = False
            self._drag_box = None
            self._mouse_coord = [0, 0]

            self._ready_to_create = False
            self._creating = False
            self._create_coord = [None, None]

            self._mode = 'pan/zoom'
            self._mode_history = self._mode
            self._status = self._mode

            self.events.add(mode=Event)
            self._qt_properties = QtShapesLayer(self)
            self._qt_controls = QtShapesControls(self)

    @property
    def data(self):
        """ShapesData: object with shapes data
        """
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

        self.refresh()

    @property
    def edge_width(self):
        """int: width of edges in px
        """

        return self._edge_width

    @edge_width.setter
    def edge_width(self, edge_width):
        self._edge_width = edge_width
        self.set_thickness(thickness=self._edge_width)

    @property
    def edge_color(self):
        """Color, ColorArray: color of edges and lines
        """

        return self._edge_color

    @edge_color.setter
    def edge_color(self, edge_color):
        self._edge_color = edge_color
        self.set_color(edge_color=self._edge_color)

    @property
    def face_color(self):
        """Color, ColorArray: color of faces
        """

        return self._face_color

    @face_color.setter
    def face_color(self, face_color):
        self._face_color = face_color
        self.set_color(face_color=self._face_color)

    @property
    def z_order(self):
        """list: list of z order of objects. If there are N objects it
        must be a permutation of 0,...,N-1
        """

        return self._z_order

    @z_order.setter
    def z_order(self, z_order):
        ## Check z_order is a permutation of 0,...,N-1
        if not is_permutation(z_order, self.data.count):
            raise ValueError('z_order is not permutation')

        self._z_order = np.array(z_order)

        if len(self._z_order) == 0:
            self._z_order_faces = np.empty((0), dtype=int)
        else:
            _, idx = np.unique(self.data._mesh_faces_index[:,0], return_index=True)
            z_order_faces = [np.arange(idx[z], idx[z]+self._face_counts[z]) for z in self._z_order]
            self._z_order_faces = np.concatenate(z_order_faces)

        self.refresh()

    @property
    def mode(self):
        """None, str: Interactive mode
        """
        return self._mode

    @mode.setter
    def mode(self, mode):
        if mode == self.mode:
            return
        old_mode = self.mode
        if mode == 'select':
            self.cursor = 'pointing'
            self.interactive = False
            self.help = 'hold <space> to pan/zoom'
            self.status = mode
            self._mode = mode
        elif mode == 'direct':
            self.cursor = 'pointing'
            self.interactive = False
            self.help = 'hold <space> to pan/zoom'
            self.status = mode
            self._mode = mode
        elif mode == 'pan/zoom':
            self.cursor = 'standard'
            self.interactive = True
            self.help = ''
            self.status = mode
            self._mode = mode
        elif mode == 'add_rectangle':
            self.cursor = 'cross'
            self.interactive = False
            self.help = 'hold <space> to pan/zoom'
            self.status = mode
            self._mode = mode
        else:
            raise ValueError("Mode not recongnized")

        self.events.mode(mode=mode)
        if mode == 'direct' and old_mode == 'select':
            self.data.select_box([])
        elif mode == 'select' and old_mode == 'direct':
            self.data.select_box(self._selected_shapes)
        else:
            self._selected_shapes = []
            self.data.select_box([])
            self._unselect()
        self.refresh()

    def _get_shape(self):
        return [1, 1]

    # def _get_shape(self):
    #     if len(self.coords) == 0:
    #         return np.ones(self.coords.shape[2:],dtype=int)
    #     else:
    #         return np.max(self.coords, axis=(0,1)) + 1

    def _update(self):
        """Update the underlying visual.
        """
        if self._need_display_update:
            self._need_display_update = False
            self._set_view_slice(self.viewer.dims.indices)

        if self._need_visual_update:
            self._need_visual_update = False
            self._node.update()

    def _refresh(self):
        """Fully refresh the underlying visual.
        """
        self._need_display_update = True
        self._update()

    def add_shapes(self, lines=None, rectangles=None, ellipses=None, paths=None,
                   polygons=None, thickness=1):
        """Adds shapes to the exisiting ones.
        """
        num_shapes = self.data.count
        num_faces = len(self.data._mesh_faces_index)
        self.data.add_shapes(lines=lines, rectangles=rectangles,
                             ellipses=ellipses, paths=paths, polygons=polygons,
                             thickness=thickness)
        new_num_shapes = self.data.count
        num_added = new_num_shapes - num_shapes
        t = np.ones(len(self.data._mesh_faces_index)-len(self._show_meshes), dtype=bool)
        self._show_meshes = np.append(self._show_meshes, t)
        self.show_objects = np.concatenate((self.show_objects, np.ones((num_added, 2), dtype=bool)), axis=0)

        ec = Color(self.edge_color).rgba
        fc = Color(self.face_color).rgba
        color_array = np.repeat([ec], len(self.data._mesh_faces_index)-num_faces, axis=0)
        color_array[self.data._mesh_faces_index[num_faces:,2]==0] = fc
        _edge_color_array = np.repeat([ec], num_added, axis=0)
        _face_color_array = np.repeat([fc], num_added, axis=0)
        self._edge_color_array = np.concatenate((self._edge_color_array, _edge_color_array), axis=0)
        self._face_color_array = np.concatenate((self._face_color_array, _face_color_array), axis=0)
        self._mesh_color_array = np.concatenate((self._mesh_color_array, color_array), axis=0)
        default_z_order, counts = np.unique(self.data._mesh_faces_index[:,0], return_counts=True)
        self._face_counts = counts
        self.z_order = np.concatenate((np.arange(num_shapes, new_num_shapes), self.z_order))

    def set_shapes(self, lines=None, rectangles=None, ellipses=None, paths=None,
                   polygons=None, thickness=1):
        """Resets shapes to be only these ones.
        """
        self.data.set_shapes(lines=lines, rectangles=rectangles,
                             ellipses=ellipses, paths=paths, polygons=polygons,
                             thickness=thickness)

        self._show_meshes = np.ones(len(self.data._mesh_faces_index), dtype=bool)
        self.show_objects = np.ones((len(self.data.count), 2), dtype=bool)

        ec = Color(self.edge_color).rgba
        fc = Color(self.face_color).rgba
        color_array = np.repeat([ec], len(self.data._mesh_faces_index), axis=0)
        color_array[self.data._mesh_faces_index[:,2]==0] = fc
        self._mesh_color_array = np.array(color_array)
        self._edge_color_array = np.repeat([ec], len(self.data.count), axis=0)
        self._face_color_array = np.repeat([fc], len(self.data.count), axis=0)
        default_z_order, counts = np.unique(self.data._mesh_faces_index[:,0], return_counts=True)
        self._face_counts = counts
        self.z_order = default_z_order

    def remove_shapes(self, index=True):
        """Remove shapes specified in index.
        """
        self._selected_shapes = []
        if index==True:
            self.data.remove_all_shapes()
            self._show_meshes = np.empty((0), dtype=bool)
            self._mesh_color_array =  np.empty((0, 4))
            self._face_color_array =  np.empty((0, 4))
            self._edge_color_array =  np.empty((0, 4))
            self._face_counts = np.empty((0), dtype=int)
            self.z_order = np.empty((0), dtype=int)
            self.show_objects = np.empty((0, 2), dtype=bool)

        elif type(index) is list:
            for i in np.sort(index)[::-1]:
                self._remove_one_shape(int(i))
            self.z_order = self._z_order
        else:
            self._remove_one_shape(index)
            self.z_order = self._z_order

    def _remove_one_shape(self, index, renumber=True):
        faces_indices = self.data._mesh_faces_index[:, 0]
        self.data.remove_one_shape(index, renumber=renumber)
        if renumber:
            z_order = self._z_order[self._z_order!=index]
            z_order[z_order>index] = z_order[z_order>index]-1
            self._z_order = z_order
            self._face_counts = np.delete(self._face_counts, index, axis=0)
            self._face_color_array = np.delete(self._face_color_array, index, axis=0)
            self._edge_color_array = np.delete(self._edge_color_array, index, axis=0)
            self.show_objects = np.delete(self.show_objects, index, axis=0)
        self._show_meshes = self._show_meshes[faces_indices!=index]
        self._mesh_color_array = self._mesh_color_array[faces_indices!=index]

    def edit_shape(self, index, vertices):
        """Replaces the current vertices of the selected shape with new ones
        Parameters
        ----------
        index : int
            index of single object that is to be edited.
        vertices : np.ndarray
            Nx2 array specifying new vertices of shape.
        """
        object_type = self.data.objects[self.data.id[index]]
        if object_type == 'ellipse':
            # NOT IMPLEMENTED
            return

        self._remove_one_shape(index, renumber=False)
        if object_type == 'line':
            self.data._add_polygon(vertices, index=index, thickness=self.data._thickness[index])
        elif object_type == 'rectangle':
            # converts rectange into polygon on editing
            self.data.id[index] = self.data.objects.index('polygon')
            self.data._add_polygon(vertices, index=index, thickness=self.data._thickness[index])
        elif object_type == 'ellipse':
            pass
            #self.data._add_ellipse(vertices, index=index, thickness=self.data._thickness[index])
        elif object_type == 'path':
            self.data._add_path(vertices, index=index, thickness=self.data._thickness[index])
        elif object_type == 'polygon':
            self.data._add_polygon(vertices, index=index, thickness=self.data._thickness[index])
        else:
            raise ValueError("Object type not recongnized")

        faces = self.data._mesh_faces_index[:,0]==index
        new_faces = sum(faces)
        self._face_counts[index] = new_faces
        new_show = np.ones(new_faces, dtype='bool')
        if self.show_objects[index, 0] is False:
            new_show[self.data._mesh_faces_index[faces, 2]==0] = False
        if self.show_objects[index, 1] is False:
            new_show[self.data._mesh_faces_index[faces, 2]==1] = False
        self._show_meshes = np.concatenate((self._show_meshes, new_show), axis=0)
        ec = self._edge_color_array[index]
        fc = self._face_color_array[index]
        color_array = np.repeat([ec], new_faces, axis=0)
        color_array[self.data._mesh_faces_index[-new_faces:,2]==0] = fc
        self._mesh_color_array = np.concatenate((self._mesh_color_array, color_array), axis=0)
        self.z_order = self._z_order

    def scale_shapes(self, scale, vertex=-2, index=True):
        """Perfroms a scaling on selected shapes
        Parameters
        ----------
        scale : float, list
            scalar or list specifying rescaling of shapes in 2D.
        vertex : int
            coordinate of bounding box to use as center of scaling.
        index : bool, list, int
            index of objects to be selected. Where True corresponds to all
            objects, a list of integers to a list of objects, and a single
            integer to that particular object.
        """
        self.data.select_box(index)
        center = self.data.selected_box[vertex]
        self.data.scale_shapes(scale, center=center, index=index)
        self.refresh()

    def flip_vertical_shapes(self, vertex=-2, index=True):
        """Perfroms an vertical flip on selected shapes
        Parameters
        ----------
        vertex : int
            coordinate of bounding box to use as center of flip axes.
        index : bool, list, int
            index of objects to be selected. Where True corresponds to all
            objects, a list of integers to a list of objects, and a single
            integer to that particular object.
        """
        self.data.select_box(index)
        center = self.data.selected_box[vertex]
        self.data.flip_vertical_shapes(center=center, index=index)
        self.refresh()

    def flip_horizontal_shapes(self, vertex=-2, index=True):
        """Perfroms an horizontal flip on selected shapes
        Parameters
        ----------
        vertex : int
            coordinate of bounding box to use as center of flip axes.
        index : bool, list, int
            index of objects to be selected. Where True corresponds to all
            objects, a list of integers to a list of objects, and a single
            integer to that particular object.
        """
        self.data.select_box(index)
        center = self.data.selected_box[vertex]
        self.data.flip_horizontal_shapes(center=center, index=index)
        self.refresh()

    def rotate_shapes(self, angle, vertex=-2, index=True):
        """Perfroms a rotation on selected shapes
        Parameters
        ----------
        angle : float
            angle specifying rotation of shapes in degrees.
        vertex : int
            coordinate of bounding box to use as center of rotation.
        index : bool, list, int
            index of objects to be selected. Where True corresponds to all
            objects, a list of integers to a list of objects, and a single
            integer to that particular object.
        """
        self.data.select_box(index)
        center = self.data.selected_box[vertex]
        self.data.rotate_shapes(angle, center=center, index=index)
        self.refresh()

    def shift_shapes(self, shift, index=True):
        """Perfroms an 2D shift on selected shapes
        Parameters
        ----------
        shift : np.ndarray
            length 2 array specifying shift of shapes.
        index : bool, list, int
            index of objects to be selected. Where True corresponds to all
            objects, a list of integers to a list of objects, and a single
            integer to that particular object.
        """
        self.data.shift_shapes(shift, index=index)
        self.refresh()

    def set_thickness(self, index=True, thickness=1):
        if isinstance(thickness, (list, np.ndarray)):
            if index is True:
                self.data._thickness = thickness
            else:
                self.data._thickness[index] = thickness
        else:
            if index is True:
                self.data._thickness = np.repeat(thickness, len(self.data._thickness))
            elif isinstance(index, (list, np.ndarray)):
                self.data._thickness[index] = np.repeat(thickness, len(index))
            else:
                self.data._thickness[index] = thickness
        self.data.update_thickness(index)
        self.refresh()

    def move_forward(self, index):
        if type(index) is list:
            z_order = self._z_order.tolist()
            indices = [z_order.index(i) for i in index]
            for i in np.sort(indices):
                self._move_one_forward(z_order[i])
        else:
            self._move_one_forward(index)
        self.z_order = self._z_order

    def move_backward(self, index):
        if type(index) is list:
            z_order = self._z_order.tolist()
            indices = [z_order.index(i) for i in index]
            for i in np.sort(indices)[::-1]:
                self._move_one_backward(z_order[i])
        else:
            self._move_one_backward(index)
        self.z_order = self._z_order

    def move_to_front(self, index):
        if type(index) is list:
            z_order = self._z_order.tolist()
            indices = [z_order.index(i) for i in index]
            for i in np.sort(indices)[::-1]:
                self._move_one_to_front(z_order[i])
        else:
            self._move_one_to_front(index)
        self.z_order = self._z_order

    def move_to_back(self, index):
        if type(index) is list:
            z_order = self._z_order.tolist()
            indices = [z_order.index(i) for i in index]
            for i in np.sort(indices):
                self._move_one_to_back(z_order[i])
        else:
            self._move_one_to_back(index)
        self.z_order = self._z_order

    def _move_one_forward(self, index):
        ind = self._z_order.tolist().index(index)
        if ind != 0:
            self._z_order[ind] = self._z_order[ind-1]
            self._z_order[ind-1] = index

    def _move_one_backward(self, index):
        ind = self._z_order.tolist().index(index)
        if ind != len(self._z_order)-1:
            self._z_order[ind] = self._z_order[ind+1]
            self._z_order[ind+1] = index

    def _move_one_to_front(self, index):
        self._z_order[1:] = self._z_order[self._z_order!=index]
        self._z_order[0] = index

    def _move_one_to_back(self, index):
        self._z_order[:-1] = self._z_order[self._z_order!=index]
        self._z_order[-1] = index

    def hide_shapes(self, index=True, object_type=None):
        indices = self.data._select_meshes(index=index, meshes=self.data._mesh_faces_index, object_type=object_type)
        self._show_meshes[indices] = False
        if object_type is None:
            self.show_objects[index, :] = False
        else:
            self.show_objects[index, object_type] = False
        self.refresh()

    def show_shapes(self, index=True, object_type=None):
        indices = self.data._select_meshes(index=index, meshes=self.data._mesh_faces_index, object_type=object_type)
        self._show_meshes[indices] = True
        if object_type is None:
            self.show_objects[index, :] = True
        else:
            self.show_objects[index, object_type] = True
        self.refresh()

    def set_color(self, index=True, edge_color=False, face_color=False):
        if face_color is False:
            pass
        else:
            if type(face_color) is list:
                if index is True:
                    for i, col in enumerate(face_color):
                        self._face_color_array[i] = Color(col).rgba
                    for i in range(len(self.data._mesh_faces_index)):
                        if self.data._mesh_faces_index[i, 2] == 0:
                            self._mesh_color_array[i] = self._face_color_array[self.data._mesh_faces_index[i, 0]]
                else:
                    assert(type(index) is list and len(face_color)==len(index))
                    for i, ind in enumerate(index):
                        indices = self.data._select_meshes(ind, self.data._mesh_faces_index, 0)
                        self._face_color_array[ind] = Color(face_color[i]).rgba
                        self._mesh_color_array[indices] = self._face_color_array[ind]
            else:
                indices = self.data._select_meshes(index, self.data._mesh_faces_index, 0)
                self._mesh_color_array[indices] = Color(face_color).rgba
                if index is True:
                    for i in range(self.data.count):
                        self._face_color_array[i] = Color(face_color).rgba
                else:
                    self._face_color_array[index] = Color(face_color).rgba
        if edge_color is False:
            pass
        else:
            if type(edge_color) is list:
                if index is True:
                    for i, col in enumerate(edge_color):
                        self._edge_color_array[i] = Color(col).rgba
                    for i in range(len(self.data._mesh_faces_index)):
                        if self.data._mesh_faces_index[i, 2] == 1:
                            self._mesh_color_array[i] = self._edge_color_array[self.data._mesh_faces_index[i, 0]]
                else:
                    assert(type(index) is list and len(face_color)==len(index))
                    for i, ind in enumerate(index):
                        indices = self.data._select_meshes(ind, self.data._mesh_faces_index, 1)
                        self._edge_color_array[ind] = Color(edge_color[i]).rgba
                        self._mesh_color_array[indices] = self._edge_color_array[ind]
            else:
                indices = self.data._select_meshes(index, self.data._mesh_faces_index, 1)
                self._mesh_color_array[indices] = Color(edge_color).rgba
                if index is True:
                    for i in range(self.data.count):
                        self._edge_color_array[i] = Color(edge_color).rgba
                else:
                    self._edge_color_array[index] = Color(edge_color).rgba

        self.refresh()

    def _shape_at(self, indices):
        """Determines if any shapes at given indices by looking inside triangle
        meshes.
        Parameters
        ----------
        indices : sequence of int
            Indices to check if shape at.
        """
        # Check selected shapes
        if len(self._selected_shapes) > 0:
            if self.mode == 'select':
                # Check if inside vertex of bounding box or rotation handle
                inds = list(range(0,8))
                inds.append(9)
                box = self.data.selected_box[inds]
                distances = abs(box - indices[:2])

                # Get the vertex sizes
                sizes = self._vertex_size

                # Check if any matching vertices
                matches = np.all(distances <=  self._vertex_size/2, axis=1).nonzero()
                if len(matches[0]) > 0:
                    return [self._selected_shapes[0], matches[0][-1]]
            elif self.mode == 'direct':
                # Check if inside vertex of shape
                inds = np.isin(self.data.index, self._selected_shapes)
                vertices = self.data.vertices[inds]
                distances = abs(vertices - indices[:2])

                # Get the vertex sizes
                sizes = self._vertex_size

                # Check if any matching vertices
                matches = np.all(distances <=  self._vertex_size/2, axis=1).nonzero()[0]
                if len(matches) > 0:
                    index = inds.nonzero()[0][matches[-1]]
                    shape = self.data.index[index]
                    _, idx = np.unique(self.data.index, return_index=True)
                    return [shape, index - idx[shape]]

        # Check if mouse inside shape
        triangles = self.data._mesh_vertices[self.data._mesh_faces[self._show_meshes]]
        shapes = self.data._mesh_faces_index[inside_triangles(triangles - indices[:2])]

        if len(shapes) > 0:
            indices = shapes[:, 0]
            z_list = self._z_order.tolist()
            order_indices = np.array([z_list.index(m) for m in indices])
            ordered_shapes = indices[np.argsort(order_indices)]
            return [ordered_shapes[0], None]
        else:
            return [None, None]

    def _shapes_in_box(self, box):
        box = self.data._expand_box(box)[[0, 4]]
        triangles = self.data._mesh_vertices[self.data._mesh_faces[self._show_meshes]]

        # check if triangle corners are inside box
        points_inside = np.empty(triangles.shape[:-1], dtype=bool)
        for i in range(3):
            points_inside[:, i] = np.all(np.concatenate(([box[1] >= triangles[:,0,:], triangles[:,i,:] >= box[0]]), axis=1), axis=1)

        # check if triangle edges intersect box edges
        # not implemented

        inside = np.any(points_inside, axis=1)
        shapes = self.data._mesh_faces_index[inside, 0]

        return np.unique(shapes).tolist()

    def _set_view_slice(self, indices):
        """Sets the view given the indices to slice with.
        Parameters
        ----------
        indices : sequence of int or slice
            Indices to slice with.
        """
        show_faces = self._show_meshes[self._z_order_faces]
        faces = self.data._mesh_faces[self._z_order_faces][show_faces]
        colors = self._mesh_color_array[self._z_order_faces][show_faces]
        vertices = self.data._mesh_vertices
        if len(faces) == 0:
            self._node._subvisuals[3].set_data(vertices=None, faces=None)
        else:
            self._node._subvisuals[3].set_data(vertices=vertices, faces=faces,
                                               face_colors=colors)
        self._need_visual_update = True
        self._set_highlight()
        self._update()

    def _set_highlight(self):
        if self._highlight and (self._hover_shapes[0] is not None or len(self._selected_shapes)>0):
            # show outlines hover shape or any selected shapes
            if len(self._selected_shapes)>0:
                index = copy(self._selected_shapes)
                if self._hover_shapes[0] is not None:
                    if self._hover_shapes[0] in index:
                        pass
                    else:
                        index.append(self._hover_shapes[0])
                index.sort()
            else:
                index = self._hover_shapes[0]

            faces_indices = self.data._select_meshes(index, self.data._mesh_faces_index, 1)
            vertices_indices = self.data._select_meshes(index, self.data._mesh_vertices_index, 1)
            vertices = self.data._mesh_vertices_centers[vertices_indices] + self._highlight_thickness*self.data._mesh_vertices_offsets[vertices_indices]
            faces = self.data._mesh_faces[faces_indices]
            if type(index) is list:
                faces_index = self.data._mesh_faces_index[faces_indices][:,0]
                starts = np.unique(self.data._mesh_vertices_index[vertices_indices][:,0], return_index=True)[1]
                for i, ind in enumerate(index):
                    faces[faces_index==ind] = faces[faces_index==ind] - vertices_indices[starts[i]] + starts[i]
            else:
                faces = faces - vertices_indices[0]
            self._node._subvisuals[2].set_data(vertices=vertices, faces=faces,
                                               color=self._highlight_color)
        else:
            self._node._subvisuals[2].set_data(vertices=None, faces=None)

        if self._highlight and len(self._selected_shapes) > 0:
            if self.mode == 'select' or self.mode == 'add_rectangle':
                inds = list(range(0,8))
                inds.append(9)
                box = self.data.selected_box[inds]
                if self._hover_shapes[0] is None:
                    face_color = 'white'
                elif self._hover_shapes[1] is None:
                    face_color = 'white'
                else:
                    face_color = self._highlight_color
                edge_color = self._highlight_color
                self._node._subvisuals[0].set_data(box, size=8, face_color=face_color,
                                                   edge_color=edge_color, edge_width=1,
                                                   symbol='square', scaling=True)
                self._node._subvisuals[1].set_data(pos=box[[1, 2, 4, 6, 0, 1, 8]],
                                                   color=edge_color, width=1)
            elif self.mode == 'direct':
                inds = np.isin(self.data.index, self._selected_shapes)
                vertices = self.data.vertices[inds]
                if self._hover_shapes[0] is None:
                    face_color = 'white'
                elif self._hover_shapes[1] is None:
                    face_color = 'white'
                else:
                    face_color = self._highlight_color
                edge_color = self._highlight_color
                self._node._subvisuals[0].set_data(vertices, size=8, face_color=face_color,
                                                   edge_color=edge_color, edge_width=1,
                                                   symbol='square', scaling=True)
                self._node._subvisuals[1].set_data(pos=None, width=0)
        elif self._is_selecting:
            box = self.data._expand_box(self._drag_box)
            edge_color = self._highlight_color
            self._node._subvisuals[0].set_data(np.empty((0, 2)), size=0)
            self._node._subvisuals[1].set_data(pos=box[[0, 2, 4, 6, 0]],
                                               color=edge_color, width=1)
        else:
            self._node._subvisuals[0].set_data(np.empty((0, 2)), size=0)
            self._node._subvisuals[1].set_data(pos=None, width=0)

    def _get_coord(self, position, indices):
        max_shape = self.viewer.dims.max_shape
        transform = self.viewer._canvas.scene.node_transform(self._node)
        pos = transform.map(position)
        pos = [pos[1], pos[0]]
        coord = copy(indices)
        coord[0] = pos[1]
        coord[1] = pos[0]
        self._mouse_coord = np.array(coord)
        return self._mouse_coord

    def get_message(self, coord, value):
        """Returns coordinate and value string for given mouse coordinates
        and value.

        Parameters
        ----------
        coord : sequence of int
            Position of mouse cursor in data.
        value : int or float or sequence of int or float
            Value of the data at the coord.

        Returns
        ----------
        msg : string
            String containing a message that can be used as
            a status update.
        """
        coord_shift = copy(coord)
        coord_shift[0] = int(coord[1])
        coord_shift[1] = int(coord[0])
        msg = f'{coord_shift.astype(int)}, {self.name}'
        if value[0] is not None:
            msg = msg + ', shape ' + str(value[0])
            if value[1] is not None:
                msg = msg + ', vertex ' + str(value[1])
        return msg

    def _move(self, coord):
        """Moves object at given mouse position
        and set of indices.
        Parameters
        ----------
        coord : sequence of two int
            Position of mouse cursor in data.
        """
        index = self._selected_shapes
        vertex = self._selected_vertex[1]
        if self.mode == 'select' or self.mode == 'add_rectangle':
            if len(index) > 0:
                self._is_moving=True
                if vertex is None:
                    #Check where dragging box from to move whole object
                    if self._drag_start is None:
                        center = self.data.selected_box[-1]
                        self._drag_start = coord - center
                    center = self.data.selected_box[-1]
                    shift = coord - center - self._drag_start
                    self.shift_shapes(shift, index=index)
                elif vertex < 8:
                    #Corner / edge vertex is being dragged so resize object
                    box = self.data.selected_box
                    if self._fixed_vertex is None:
                        self._fixed_index = np.mod(vertex+4,8)
                        self._fixed_vertex = box[self._fixed_index]
                        if np.any(box[4]-box[0] == np.zeros(2)):
                            self._aspect_ratio = 1
                        else:
                            self._aspect_ratio = (box[4][1]-box[0][1])/(box[4][0]-box[0][0])

                    size = box[np.mod(self._fixed_index+4,8)] - box[self._fixed_index]
                    offset = box[-1] - box[-2]
                    offset = offset/np.linalg.norm(offset)
                    offset_perp = np.array([offset[1], -offset[0]])

                    if np.mod(self._fixed_index, 2) == 0:
                        # corner selected
                        fixed = self._fixed_vertex
                        new = copy(coord)
                        if self._fixed_aspect:
                            ratio = abs((new - fixed)[1]/(new - fixed)[0])
                            if ratio>self._aspect_ratio:
                                new[1] = fixed[1]+(new[1]-fixed[1])*self._aspect_ratio/ratio
                            else:
                                new[0] = fixed[0]+(new[0]-fixed[0])*ratio/self._aspect_ratio
                        dist = np.dot(new-fixed, offset)/np.dot(size, offset)
                        dist_perp = np.dot(new-fixed, offset_perp)/np.dot(size, offset_perp)
                        scale = np.array([dist_perp, dist])
                    elif np.mod(self._fixed_index, 4) == 1:
                        # top selected
                        fixed = self._fixed_vertex
                        new = copy(coord)
                        dist = np.dot(new-fixed, offset)/np.dot(size, offset)
                        scale = np.array([1, dist])
                    else:
                        # side selected
                        fixed = self._fixed_vertex
                        new = copy(coord)
                        dist_perp = np.dot(new-fixed, offset_perp)/np.dot(size, offset_perp)
                        scale = np.array([dist_perp, 1])

                    # prvent box from dissappearing if shrunk near 0
                    scale[scale==0]=1

                    # check orientation of box
                    angle = -np.arctan2(offset[0], -offset[1])
                    if angle == 0:
                        self.data.scale_shapes(scale, center=self._fixed_vertex, index=index)
                    else:
                        rotation = np.array([[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])
                        scale_tranform = np.array([[scale[0], 0], [0, scale[1]]])
                        inverse_rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
                        transform = np.matmul(rotation, np.matmul(scale_tranform, inverse_rotation))
                        self.data.shift_shapes(-self._fixed_vertex, index=index)
                        self.data.transform_shapes(transform, index=index)
                        self.data.shift_shapes(self._fixed_vertex, index=index)
                    self.refresh()
                elif vertex==8:
                    #Rotation handle is being dragged so rotate object
                    handle = self.data.selected_box[-1]
                    if self._drag_start is None:
                        self._fixed_vertex = self.data.selected_box[-2]
                        offset = handle - self._fixed_vertex
                        self._drag_start = -np.arctan2(offset[0], -offset[1])/np.pi*180

                    new_offset = coord - self._fixed_vertex
                    new_angle = -np.arctan2(new_offset[0], -new_offset[1])/np.pi*180
                    fixed_offset = handle - self._fixed_vertex
                    fixed_angle = -np.arctan2(fixed_offset[0], -fixed_offset[1])/np.pi*180

                    if np.linalg.norm(new_offset)<1:
                        angle = 0
                    elif self._fixed_aspect:
                        angle = np.round(new_angle/45)*45 - fixed_angle
                    else:
                        angle = new_angle - fixed_angle

                    self.data.rotate_shapes(angle, center=self._fixed_vertex, index=index)
                    self.refresh()
            else:
                self._is_selecting=True
                if self._drag_start is None:
                    self._drag_start = coord
                self._drag_box = np.array([self._drag_start, coord])
                self._set_highlight()
        elif self.mode == 'direct':
            if len(index) > 0:
                if vertex is not None:
                    self._is_moving=True
                    index = self._selected_vertex[0]
                    vertices = self.data.vertices[self.data.index == index]
                    vertices[vertex] = coord
                    self.edit_shape(index, vertices)
            else:
                self._is_selecting=True
                if self._drag_start is None:
                    self._drag_start = coord
                self._drag_box = np.array([self._drag_start, coord])
                self._set_highlight()

    def _select(self):
        if (self._selected_shapes == self._selected_shapes_stored and
            self._hover_shapes == self._hover_shapes_stored):
            return
        self._highlight = True
        self._selected_shapes_stored = copy(self._selected_shapes)
        self._hover_shapes_stored = copy(self._hover_shapes)
        self._set_highlight()

    def _unselect(self):
        if self._highlight:
            self._highlight = False
            self._selected_shapes_stored = []
            self._hover_shapes_stored = [None, None]
            self._set_highlight()

    def on_mouse_move(self, event):
        """Called whenever mouse moves over canvas.
        """
        if event.pos is None:
            return
        position = event.pos
        indices = self.viewer.dims.indices
        coord = self._get_coord(position, indices)

        if self.mode == 'select':
            if event.is_dragging:
                # Drag any selected shapes
                self._move(coord)
            elif self._is_moving:
                pass
            elif self._is_selecting:
                pass
            else:
                # Highlight boxes if hover over any
                self._hover_shapes = self._shape_at(coord)
                self._select()
            shape = self._hover_shapes
        elif self.mode == 'direct':
            if event.is_dragging:
                # Drag any selected shapes
                self._move(coord)
            elif self._is_moving:
                pass
            elif self._is_selecting:
                pass
            else:
                # Highlight boxes if hover over any
                self._hover_shapes = self._shape_at(coord)
                self._select()
            shape = self._hover_shapes
        elif self.mode == 'pan/zoom':
            # If in pan/zoom mode just look at coord all
            shape = self._shape_at(coord)
        elif self.mode == 'add_rectangle':
            # If ready to create rectangle start making one
            if self._ready_to_create and np.all(self._create_coord != coord):
                shape = np.array([[self._create_coord, coord]])
                self.add_shapes(rectangles = shape)
                self._ready_to_create = False
                self._selected_shapes = [self.data.count-1]
                self.data.select_box(self._selected_shapes[0])
                ind = np.all(self.data.selected_box==coord, axis=1).nonzero()[0][0]
                self._selected_vertex = [self._selected_shapes[0], ind]
                self._hover_shapes = [self._selected_shapes[0], ind]
                self._creating = True
                self._select()
            # While drawing a rectangle or doing nothing
            if self._creating and event.is_dragging:
                # Drag any selected shapes
                self._move(coord)
                shape = self._hover_shapes
            else:
                shape = self._shape_at(coord)
        else:
            raise ValueError("Mode not recongnized")

        self.status = self.get_message(coord, shape)

    def on_mouse_press(self, event):
        """Called whenever mouse pressed in canvas.
        """
        position = event.pos
        indices = self.viewer.dims.indices
        coord = self._get_coord(position, indices)
        shift = 'Shift' in event.modifiers

        if self.mode == 'select':
            if not self._is_moving and not self._is_selecting:
                shape = self._shape_at(coord)
                self._selected_vertex = shape
                if self._selected_vertex[1] is None:
                    if shift and shape[0] is not None:
                        if shape[0] in self._selected_shapes:
                            self._selected_shapes.remove(shape[0])
                            self.data.select_box(self._selected_shapes)
                        else:
                            self._selected_shapes.append(shape[0])
                            self.data.select_box(self._selected_shapes)
                    elif shape[0] is not None:
                        if shape[0] not in self._selected_shapes:
                            self._selected_shapes = [shape[0]]
                            self.data.select_box(self._selected_shapes)
                    else:
                        self._selected_shapes = []
                        self.data.select_box(self._selected_shapes)
                self._select()
                self.status = self.get_message(coord, shape)
        elif self.mode == 'direct':
            if not self._is_moving and not self._is_selecting:
                shape = self._shape_at(coord)
                self._selected_vertex = shape
                if self._selected_vertex[1] is None:
                    if shift and shape[0] is not None:
                        if shape[0] in self._selected_shapes:
                            self._selected_shapes.remove(shape[0])
                        else:
                            self._selected_shapes.append(shape[0])
                    elif shape[0] is not None:
                        if shape[0] not in self._selected_shapes:
                            self._selected_shapes = [shape[0]]
                    else:
                        self._selected_shapes = []
                self._select()
                self.status = self.get_message(coord, shape)
        elif self.mode == 'pan/zoom':
            # If in pan/zoom mode do nothing
            pass
        elif self.mode == 'add_rectangle':
            # Start drawing a rectangle
            self._ready_to_create = True
            self._create_coord = coord
        else:
            raise ValueError("Mode not recongnized")

    def on_mouse_release(self, event):
        """Called whenever mouse released in canvas.
        """
        position = event.pos
        indices = self.viewer.dims.indices
        coord = self._get_coord(position, indices)
        shift = 'Shift' in event.modifiers

        if self.mode == 'select':
            shape = self._shape_at(coord)
            if not self._is_moving and not self._is_selecting and not shift:
                if shape[0] is not None:
                    self._selected_shapes = [shape[0]]
                    self.data.select_box(self._selected_shapes)
                else:
                    self._selected_shapes = []
                    self.data.select_box(self._selected_shapes)
            elif self._is_selecting:
                self._selected_shapes = self._shapes_in_box(self._drag_box)
                self.data.select_box(self._selected_shapes)
                self._is_selecting=False
                self._set_highlight()
            self._is_moving = False
            self._drag_start = None
            self._drag_box = None
            self._fixed_vertex = None
            self._selected_vertex = [None, None]
            self._hover_shapes = shape
            self._select()
            self.status = self.get_message(coord, shape)
        elif self.mode == 'direct':
            shape = self._shape_at(coord)
            if not self._is_moving and not self._is_selecting and not shift:
                if shape[0] is not None:
                    self._selected_shapes = [shape[0]]
                    self.data.select_box(self._selected_shapes)
                else:
                    self._selected_shapes = []
                    self.data.select_box(self._selected_shapes)
            elif self._is_selecting:
                self._selected_shapes = self._shapes_in_box(self._drag_box)
                self.data.select_box(self._selected_shapes)
                self._is_selecting=False
                self._set_highlight()
            self._is_moving = False
            self._drag_start = None
            self._drag_box = None
            self._fixed_vertex = None
            self._selected_vertex = [None, None]
            self._hover_shapes = shape
            self._select()
            self.status = self.get_message(coord, shape)
        elif self.mode == 'pan/zoom':
            # If in pan/zoom mode do nothing
            pass
        elif self.mode == 'add_rectangle':
            # Finish drawing a rectangle
            self._ready_to_create = False
            self._create_coord = [None, None]
            self._is_moving = False
            self._selected_shapes = []
            self._drag_start = None
            self._drag_box = None
            self._fixed_vertex = None
            self._selected_vertex = [None, None]
            self._hover_shapes = [None, None]
            self._creating = False
            self.data.select_box([])
            self._unselect()
            shape = self._shape_at(coord)
            self.status = self.get_message(coord, shape)
        else:
            raise ValueError("Mode not recongnized")

    def on_key_press(self, event):
        """Called whenever key pressed in canvas.
        """
        if event.native.isAutoRepeat():
            return
        else:
            if event.key == ' ':
                if self.mode != 'pan/zoom':
                    self._mode_history = self.mode
                    self.mode = 'pan/zoom'
                else:
                    self._mode_history = 'pan/zoom'
            elif event.key == 'Shift':
                self._fixed_aspect = True
                if self._is_moving:
                    box = self.data.selected_box
                    if box is not None:
                        self._aspect_ratio = abs((box[4][1]-box[0][1])/(box[4][0]-box[0][0]))
                    self._move(self._mouse_coord)
            elif event.key == 'r':
                self.mode = 'add_rectangle'
            elif event.key == 'd':
                self.mode = 'direct'
            elif event.key == 's':
                self.mode = 'select'
            elif event.key == 'z':
                self.mode = 'pan/zoom'

    def on_key_release(self, event):
        """Called whenever key released in canvas.
        """
        if event.key == ' ':
            if self._mode_history != 'pan/zoom':
                self.mode = self._mode_history
        elif event.key == 'Shift':
            self._fixed_aspect = False
            if self._is_moving:
                box = self.data.selected_box
                if box is not None:
                    self._aspect_ratio = abs((box[4][1]-box[0][1])/(box[4][0]-box[0][0]))
                self._move(self._mouse_coord)
