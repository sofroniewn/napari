"""Layers are the viewable objects that can be added to a viewer.

Custom layers must inherit from Layer and pass along the
`visual node <http://vispy.org/scene.html#module-vispy.scene.visuals>`_
to the super constructor.
"""


from ._base_layer import Layer
from ._image_layer import Image
from ._markers_layer import Markers
from ._rectangles_layer import Rectangles
from ._ellipses_layer import Ellipses
from ._lines_layer import Lines
from ._register import add_to_viewer
