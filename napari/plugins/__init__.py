import os
import sys
from inspect import isclass
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    List,
    Sequence,
    Tuple,
    Type,
    Union,
)

from napari_plugin_engine import PluginManager

from ..types import DockWidget, MagicFunction
from ..utils._appdirs import user_site_packages
from ..utils.misc import camel_to_spaces, is_sequence, running_as_bundled_app
from . import _builtins, hook_specifications

if sys.platform.startswith('linux') and running_as_bundled_app():
    sys.path.append(user_site_packages())


if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


# the main plugin manager instance for the `napari` plugin namespace.
plugin_manager = PluginManager(
    'napari', discover_entry_point='napari.plugin', discover_prefix='napari_'
)
with plugin_manager.discovery_blocked():
    plugin_manager.add_hookspecs(hook_specifications)
    plugin_manager.register(_builtins, name='builtins')


dock_widgets: Dict[str, Type['QWidget']] = dict()
functions: Dict[str, Type[Tuple[Callable, Dict, Dict]]] = dict()


def register_dock_widget(cls: Union[DockWidget, List[DockWidget]], hookimpl):
    from qtpy.QtWidgets import QWidget

    for _cls in cls if isinstance(cls, list) else [cls]:
        if isinstance(_cls, tuple):
            widget_tuple = _cls + ({},) * (2 - len(_cls))
        else:
            widget_tuple = (_cls, {})

        # Get widget name
        name = widget_tuple[1].get(
            'name', camel_to_spaces(widget_tuple[0].__name__)
        )

        key = (hookimpl.plugin_name, name)
        if key in dock_widgets:
            warnings.warn(
                f'Plugin {key[0]} has already registered a widget {key[1]} which has now been overwritten'
            )
        dock_widgets[key] = widget_tuple


def register_function(
    func: Union[MagicFunction, List[MagicFunction]], hookimpl
):
    for _func in func if isinstance(func, list) else [func]:
        if isinstance(_func, tuple):
            func_tuple = _func + ({},) * (3 - len(_func))
        else:
            func_tuple = (_func, {}, {})

        # Get function name
        name = func_tuple[2].get(
            'name', func_tuple[0].__name__.replace('_', ' ')
        )

        key = (hookimpl.plugin_name, name)
        if key in functions:
            warnings.warn(
                f'Plugin {key[0]} has already registered a function {key[1]} which has now been overwritten'
            )

        functions[(hookimpl.plugin_name, name)] = func_tuple


plugin_manager.hook.napari_experimental_provide_dock_widgets.call_historic(
    result_callback=register_dock_widget, with_impl=True
)


plugin_manager.hook.napari_experimental_provide_functions.call_historic(
    result_callback=register_function, with_impl=True
)


__all__ = [
    "PluginManager",
    "plugin_manager",
]
