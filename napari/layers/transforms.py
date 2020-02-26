from __future__ import annotations  # noqa: F407

import toolz as tz
from typing import Sequence
import numpy as np

from ..utils.list import ListModel


class Transform:
    """Base transform class.

    Defaults to the identity transform.

    Parameters
    ----------
    func : callable, Coords -> Coords
        A function converting an NxD array of coordinates to NxD'.
    """

    def __init__(self, func=tz.identity, inverse=None, name=None):
        self.func = func
        self._inverse_func = inverse
        self.name = name
        if func is tz.identity:
            self._inverse_func = tz.identity
        self.translate = None
        self.scale = None

    def __call__(self, coords):
        """Transform input coordinates to output."""
        return self.func(coords)

    def set_slice(self, axes: Sequence[int]) -> Transform:
        """Return a transform subset to the visible dimensions."""
        raise NotImplementedError('Cannot subset arbitrary transforms.')

    @property
    def inverse(self):
        if self._inverse_func is not None:
            return Transform(self._inverse_func, self.func)
        else:
            raise ValueError('Inverse function was not provided.')


class TransformChain(ListModel, Transform):
    """Class performing an ordered sequence of transforms.

    Parameters
    ----------
    transforms : list
        List of napari transforms to chain together.

    Attributes
    ----------

    events : vispy.util.event.EmitterGroup
        Event hooks:
            * added(item, index): whenever an item is added
            * removed(item): whenever an item is removed
            * reordered(): whenever the list is reordered

    """

    def __init__(self, transforms=[]):
        super().__init__(
            basetype=Transform,
            iterable=transforms,
            lookup={str: lambda q, e: q == e.name},
        )

    def __call__(self, coords):
        return tz.pipe(coords, *self)

    def __newlike__(self, iterable):
        return ListModel(self._basetype, iterable, self._lookup)

    def set_slice(self, axes: Sequence[int]) -> TransformChain:
        return TransformChain([tf.set_slice(axes) for tf in self])

    def _update_attributes(self):
        if self != []:
            for idx, t in enumerate(self):
                # Account for the fact t.scale or t.translate may equal None
                if t.scale is None:
                    t.scale = np.array([1.0])
                if t.translate is None:
                    t.translate = np.array([0.0])
                if idx == 0:
                    tmp_scale = t.scale
                    tmp_translate = t.translate
                else:
                    tmp_scale = tmp_scale * t.scale
                    tmp_translate = (tmp_translate * t.scale) + t.translate
            self._scale = tmp_scale
            self._translate = tmp_translate
        else:
            self._scale = np.array([1.0])
            self._translate = np.array([0.0])

    @property
    def scale(self):
        """Scale of all the chained transforms combined.

        No setter method: you should not modify this attribute directly,
        but instead add/remove elements to napari TransformChain.
        """
        self._update_attributes()
        return self._scale

    @property
    def translate(self):
        """Translation of all the chained transforms combined.

        No setter method: you should not modify this attribute directly,
        but instead add/remove elements to napari TransformChain.
        """
        self._update_attributes()
        return self._translate


class IdentityTransform(Transform):
    """n-dimensional identity transformation class.

    Attributes
    ----------
    scale : ndarray
    translate : ndarray
    """

    def __init__(self, scale=(1.0,), translate=(0.0,), name='identity'):
        super().__init__(name=name)
        self.scale = np.array(scale)
        self.translate = np.array(translate)


class Translate(Transform):
    """n-dimensional translation (shift) class.

    An empty translation vector implies no translation.

    Translation is broadcast to 0 in leading dimensions, so that, for example,
    a translation of [4, 18, 34] in 3D can be used as a translation of
    [0, 4, 18, 34] in 4D without modification.

    Attributes
    ----------
    translate : ndarray
    """

    def __init__(self, translate=(0.0,), name='translate'):
        super().__init__(name=name)
        self.translate = np.array(translate)

    def __call__(self, coords):
        coords = np.atleast_2d(coords)
        translate = np.concatenate(
            ([0.0] * (coords.shape[1] - len(self.translate)), self.translate)
        )
        return coords + translate

    @property
    def inverse(self):
        return Translate(-self.translate)

    def set_slice(self, axes: Sequence[int]) -> Translate:
        return Translate(self.translate[axes])


class Scale(Transform):
    """n-dimensional scale class.

    An empty scale class implies a scale of 1.

    Attributes
    ----------
    scale : ndarray
    """

    def __init__(self, scale=(1.0,), name='scale'):
        super().__init__(name=name)
        self.scale = np.array(scale)

    def __call__(self, coords):
        coords = np.atleast_2d(coords)
        if coords.shape[1] > len(self.scale):
            scale = np.concatenate(
                ([1.0] * (coords.shape[1] - len(self.scale)), self.scale)
            )
        return coords * scale

    @property
    def inverse(self):
        return Scale(1 / self.scale)

    def set_slice(self, axes: Sequence[int]) -> Scale:
        return Scale(self.scale[axes])