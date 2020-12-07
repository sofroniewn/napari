import zarr

from .._version import get_versions
from ..components import ViewerModel

__version__ = get_versions()['version']
del get_versions


def to_zarr(viewer, store=None):
    """Create a zarr group with viewer data."""

    root = zarr.group(store=store)
    root.attrs['napari'] = True
    root.attrs['version'] = __version__
    root.create_group('viewer')
    root.attrs['metadata'] = {}

    root['viewer'].create_groups(
        ['axes', 'camera', 'dims', 'grid', 'layers', 'scale_bar']
    )
    root['viewer'].attrs['title'] = viewer.title
    root['viewer'].attrs['theme'] = viewer.theme

    root['viewer']['axes'].attrs.put(viewer.axes.asdict())
    root['viewer']['camera'].attrs.put(viewer.camera.asdict())
    root['viewer']['cursor'].attrs.put(viewer.cursor.asdict())
    root['viewer']['grid'].attrs.put(viewer.grid.asdict())
    root['viewer']['scale_bar'].attrs.put(viewer.scale_bar.asdict())

    layer_gp = root['viewer']['layers']
    layer_gp
    # for layer in viewer.layers:
    #     layer_gp = layer.to_zarr(layer_gp)

    return root


def from_zarr(root, viewer=None):
    """Load a zarr group with viewer data."""
    if type(root) == str:
        root = zarr.open(root)

    if 'napari' not in root.attrs:
        raise ValueError('zarr object not recognized as a napari zarr')

    if viewer is None:
        viewer = ViewerModel()

    viewer.title = root['viewer'].attrs['title']
    viewer.theme = root['viewer'].attrs['theme']

    # for layer in root['viewer']['layers']:
    #     viewer.layers.add_

    # for name in root['layers'].attrs['layer_names']:
    #     g = root['layers/' + name]
    #     layer_type = g.attrs['layer_type']
    #     args = copy(g.attrs.asdict())
    #     del args['layer_type']
    #     for array_name, array in g.arrays():
    #         if array_name not in ['data', 'thumbnail']:
    #             args[array_name] = array
    #     if isinstance(g['data'], zarr.Group):
    #         data = []
    #         for array_name, array in g['data'].arrays():
    #             data.append(array)
    #     else:
    #         data = g['data']
    #     self._add_layer[layer_type](data, **args)

    viewer.axes.update(root['viewer']['axes'].asdict())
    viewer.axes.update(root['viewer']['camera'].asdict())
    viewer.axes.update(root['viewer']['cursor'].asdict())
    viewer.axes.update(root['viewer']['grid'].asdict())
    viewer.axes.update(root['viewer']['scale_bar'].asdict())

    return viewer
