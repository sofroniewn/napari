import os.path
import subprocess
import warnings

import numpy as np
import zarr
from imageio import imwrite

from .._version import get_versions
from ..components import ViewerModel

__version__ = get_versions()['version']
del get_versions


def make_square(mat):
    """Make a matrix square along its first two axes.
    Parameters
    ----------
    mat : array.
        Array to be made square.
    Returns
    ----------
    out : array
        Square matrix.
    """
    (a, b) = mat.shape[:2]
    if a > b:
        padding = ((0, 0), ((a - b) // 2, (a - b + 1) // 2))
    else:
        padding = (((b - a) // 2, (b - a + 1) // 2), (0, 0))
    padding = padding + ((0, 0),) * (mat.ndim - 2)
    return np.pad(mat, padding, mode='constant')


def set_icon(folder, icon):
    """Set folder to have an icon.
    Parameters
    ----------
    folder : str.
        Path to folder that will be given icon.
    icon : str.
        Base name of icon file located inside target folder.
    """
    try:
        resource_file = os.path.join(folder, 'Icon.rsrc')
        hidden_icon_file = os.path.join(folder, 'Icon\r')
        icon_file = icon + '.icns'

        # Create a temporary resource file
        with open(resource_file, "w") as resource:
            resource.write(f"read 'icns' (-16455)\"{icon_file}\";")

        # Create an Icon file
        # Set icon of the folder
        # Set Icon file to be invisible
        # Remove the temporary resource file
        # Set folder to be a package
        cmds = [
            ['Rez', '-a', resource_file, '-o', hidden_icon_file],
            ['SetFile', '-a', 'C', folder],
            ['SetFile', '-a', 'V', hidden_icon_file],
            ['rm', '-rf', resource_file],
            ['SetFile', '-a', 'B', folder],
        ]

        for c in cmds:
            subprocess.run(c)
    except OSError:
        warnings.warn('icon not set')


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

    screenshot = viewer.screenshot()
    root.array(
        'screenshot',
        screenshot,
        shape=screenshot.shape,
        chunks=(None, None, None),
        dtype=screenshot.dtype,
    )

    if store is not None:
        icon = make_square(screenshot)
        imwrite(os.path.join(store, 'screenshot.icns'), icon)
        imwrite(os.path.join(store, 'screenshot.ico'), icon)
        set_icon(store, 'screenshot')

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
