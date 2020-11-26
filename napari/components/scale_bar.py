import numpy as np

from ..utils.colormaps.standardize_color import transform_single_color
from ..utils.events.dataclass import Property, dataclass
from ._viewer_constants import Position


@dataclass(events=True, properties=True)
class ScaleBar:
    """Scale bar indicating size in world coordinates.

    Parameters
    ----------
    background_color : np.ndarray
        Background color of canvas. If scale bar is not colored
        then it has the color opposite of this color.
    colored : bool
        If scale bar are colored or not. If colored then
        default color is magenta. If not colored than
        scale bar color is the opposite of the canvas
        background.
    events : EmitterGroup
        Event emitter group
    position : str
        Position of the scale bar in the canvas. Must be one of
        'top left', 'top right', 'bottom right', 'bottom left'.
        Default value is 'bottom right'.
    ticks : bool
        If scale bar has ticks at ends or not.
    visible : bool
        If scale bar is visible or not.
    """

    visible: bool = False
    colored: bool = False
    ticks: bool = True
    position: Property[Position, str, Position] = Position.BOTTOM_RIGHT
    background_color: Property[
        np.ndarray, None, transform_single_color
    ] = np.array([1, 1, 1, 1])
