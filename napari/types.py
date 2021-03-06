from functools import wraps
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    NewType,
    Tuple,
    Type,
    Union,
)

import numpy as np

if TYPE_CHECKING:
    import dask.array
    import zarr
    from magicgui.widgets import FunctionGui
    from qtpy.QtWidgets import QWidget


# This is a WOEFULLY inadequate stub for a duck-array type.
# Mostly, just a placeholder for the concept of needing an ArrayLike type.
# Ultimately, this should come from https://github.com/napari/image-types
# and should probably be replaced by a typing.Protocol
# note, numpy.typing.ArrayLike (in v1.20) is not quite what we want either,
# since it includes all valid arguments for np.array() ( int, float, str...)
ArrayLike = Union[np.ndarray, 'dask.array.Array', 'zarr.Array']


# layer data may be: (data,) (data, meta), or (data, meta, layer_type)
# using "Any" for the data type until ArrayLike is more mature.
FullLayerData = Tuple[Any, Dict, str]
LayerData = Union[Tuple[Any], Tuple[Any, Dict], FullLayerData]

PathLike = Union[str, List[str]]
ReaderFunction = Callable[[PathLike], List[LayerData]]
WriterFunction = Callable[[str, List[FullLayerData]], List[str]]

ExcInfo = Union[
    Tuple[Type[BaseException], BaseException, TracebackType],
    Tuple[None, None, None],
]

# Types for GUI HookSpecs
WidgetCallable = Callable[..., Union['FunctionGui', 'QWidget']]
AugmentedWidget = Union[WidgetCallable, Tuple[WidgetCallable, dict]]


# these types are mostly "intentionality" placeholders.  While it's still hard
# to use actual types to define what is acceptable data for a given layer,
# these types let us point to a concrete namespace to indicate "this data is
# intended to be (and is capable of) being turned into X layer type".
# while their names should not change (without deprecation), their typing
# implementations may... or may be rolled over to napari/image-types

if tuple(np.__version__.split('.')) < ('1', '20'):
    # this hack is because NewType doesn't allow `Any` as a base type
    # and numpy <=1.20 didn't provide type stubs for np.ndarray
    # https://github.com/python/mypy/issues/6701#issuecomment-609638202
    class ArrayBase(np.ndarray):
        def __getattr__(self, name: str) -> Any:
            return super().__getattr__(name)


else:
    ArrayBase = np.ndarray  # type: ignore


ImageData = NewType("ImageData", ArrayBase)
LabelsData = NewType("LabelsData", ArrayBase)
PointsData = NewType("PointsData", ArrayBase)
ShapesData = NewType("ShapesData", List[ArrayBase])
SurfaceData = NewType("SurfaceData", Tuple[ArrayBase, ArrayBase, ArrayBase])
TracksData = NewType("TracksData", ArrayBase)
VectorsData = NewType("VectorsData", ArrayBase)

LayerDataTuple = NewType("LayerDataTuple", tuple)


def image_reader_to_layerdata_reader(
    func: Callable[[PathLike], ArrayLike]
) -> ReaderFunction:
    """Convert a PathLike -> ArrayLike function to a PathLike -> LayerData.

    Parameters
    ----------
    func : Callable[[PathLike], ArrayLike]
        A function that accepts a string or list of strings, and returns an
        ArrayLike.

    Returns
    -------
    reader_function : Callable[[PathLike], List[LayerData]]
        A function that accepts a string or list of strings, and returns data
        as a list of LayerData: List[Tuple[ArrayLike]]
    """

    @wraps(func)
    def reader_function(*args, **kwargs) -> List[LayerData]:
        result = func(*args, **kwargs)
        return [(result,)]

    return reader_function
