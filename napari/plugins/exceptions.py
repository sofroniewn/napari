import re
import sys
from collections import defaultdict
from types import TracebackType
from typing import (
    Callable,
    DefaultDict,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

# This is a mapping of plugin_name -> PluginError instances
# all PluginErrors get added to this in PluginError.__init__
PLUGIN_ERRORS: DefaultDict[str, List['PluginError']] = defaultdict(list)

# standard tuple type returned from sys.exc_info()
ExcInfoTuple = Tuple[Type[Exception], Exception, Optional[TracebackType]]

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata
Distribution = importlib_metadata.Distribution


class PluginError(Exception):
    """Base class for all plugin-related errors.

    Instantiating a PluginError (whether raised or not), adds the exception
    instance to the PLUGIN_ERRORS dict for later retrieval.

    Parameters
    ----------
    message : str
        A message for the exception
    plugin_name : str
        The name of the plugin that had the error
    plugin_module : str
        The module of the plugin that had the error
    """

    def __init__(self, message: str, plugin_name: str, plugin_module: str):
        super().__init__(message)
        self.plugin_name = plugin_name
        self.plugin_module = plugin_module
        PLUGIN_ERRORS[plugin_name].append(self)

    def format_with_contact_info(self) -> str:
        """Make formatted string with context and contact info if possible."""
        # circular imports
        from napari import __version__

        msg = f'\n\nPluginError: {self}'
        msg += '\n(Use "Plugins > Plugin errors..." to review/report errors.)'
        if self.__cause__:
            cause = str(self.__cause__).replace("\n", "\n" + " " * 13)
            msg += f'\n  Cause was: {cause}'
        contact = fetch_module_metadata(self.plugin_module)
        if contact:
            extra = [f'{k: >11}: {v}' for k, v in contact.items()]
            extra += [f'{"napari": >11}: v{__version__}']
            msg += "\n".join(extra)
        msg += '\n'
        return msg

    def info(self,) -> ExcInfoTuple:
        """Return info as would be returned from sys.exc_info()."""
        return (self.__class__, self, self.__traceback__)


class PluginCallError(PluginError):
    """Raised when an error is raised when calling a plugin implementation."""

    def __init__(self, hook_implementation, msg=None, cause=None):
        plugin_name = hook_implementation.plugin_name
        # hook_implementation may not have a plugin module if it was created
        # in tests.
        if hook_implementation.plugin:
            plugin_module = hook_implementation.plugin.__name__
        else:
            plugin_module = None
        specname = (
            getattr(hook_implementation, 'specname', '')
            or hook_implementation.function.__name__
        )

        if not msg:
            msg = f"Error in plugin '{plugin_name}', hook '{specname}'"
            if cause:
                msg += f": {str(cause)}"

        super().__init__(msg, plugin_name, plugin_module)
        if cause:
            self.__cause__ = cause


class PluginImportError(PluginError, ImportError):
    """Raised when a plugin fails to import."""

    def __init__(self, plugin_name: str, plugin_module: str):
        msg = f"Failed to import plugin: '{plugin_name}'"
        super().__init__(msg, plugin_name, plugin_module)


class PluginRegistrationError(PluginError):
    """Raised when a plugin fails to register with pluggy."""

    def __init__(self, plugin_name: str, plugin_module: str):
        msg = f"Failed to register plugin: '{plugin_name}'"
        super().__init__(msg, plugin_name, plugin_module)


def format_exceptions(plugin_name: str, as_html: bool = False):
    """Return formatted tracebacks for all exceptions raised by plugin.

    Parameters
    ----------
    plugin_name : str
        The name of a plugin for which to retrieve tracebacks.
    as_html : bool
        Whether to return the exception string as formatted html,
        defaults to False.

    Returns
    -------
    str
        A formatted string with traceback information for every exception
        raised by ``plugin_name`` during this session.
    """
    _plugin_errors: List[PluginError] = PLUGIN_ERRORS.get(plugin_name)
    if not _plugin_errors:
        return ''

    from napari import __version__

    format_exc_info = get_tb_formatter()

    _linewidth = 80
    _pad = (_linewidth - len(plugin_name) - 18) // 2
    msg = [
        f"{'=' * _pad} Errors for plugin '{plugin_name}' {'=' * _pad}",
        '',
        f'{"napari version": >16}: {__version__}',
    ]

    err0 = _plugin_errors[0]
    package_meta = fetch_module_metadata(err0.plugin_module)
    if package_meta:
        msg.extend(
            [
                f'{"plugin package": >16}: {package_meta["package"]}',
                f'{"version": >16}: {package_meta["version"]}',
                f'{"module": >16}: {err0.plugin_module}',
            ]
        )
    msg.append('')

    for n, err in enumerate(_plugin_errors):
        _pad = _linewidth - len(str(err)) - 10
        msg += ['', f'ERROR #{n + 1}:  {str(err)} {"-" * _pad}', '']
        msg.append(format_exc_info(err.info(), as_html))

    msg.append('=' * _linewidth)

    return ("<br>" if as_html else "\n").join(msg)


def get_tb_formatter() -> Callable[[ExcInfoTuple, bool], str]:
    """Return a formatter callable that uses IPython VerboseTB if available.

    Imports IPython lazily if available to take advantage of ultratb.VerboseTB.
    If unavailable, cgitb is used instead, but this function overrides a lot of
    the hardcoded citgb styles and adds error chaining (for exceptions that
    result from other exceptions).

    Returns
    -------
    callable
        A function that accepts a 3-tuple and a boolean ``(exc_info, as_html)``
        and returns a formatted traceback string. The ``exc_info`` tuple is of
        the ``(type, value, traceback)`` format returned by sys.exc_info().
        The ``as_html`` determines whether the traceback is formated in html
        or plain text.
    """
    try:
        import IPython.core.ultratb

        def format_exc_info(info: ExcInfoTuple, as_html: bool) -> str:
            color = 'Linux' if as_html else 'NoColor'
            vbtb = IPython.core.ultratb.VerboseTB(color_scheme=color)
            if as_html:
                ansi_string = vbtb.text(*info).replace(" ", "&nbsp;")
                html = "".join(ansi2html(ansi_string))
                html = html.replace("\n", "<br>")
                html = (
                    "<span style='font-family: monaco,courier,monospace;'>"
                    + html
                    + "</span>"
                )
                return html
            else:
                return vbtb.text(*info)

    except ImportError:
        import cgitb
        import traceback

        # cgitb does not support error chaining...
        # see https://www.python.org/dev/peps/pep-3134/#enhanced-reporting
        # this is a workaround
        def cgitb_chain(exc: Exception) -> Generator[str, None, None]:
            """Recurse through exception stack and chain cgitb_html calls."""
            if exc.__cause__:
                yield from cgitb_chain(exc.__cause__)
                yield (
                    '<br><br><font color="#51B432">The above exception was '
                    'the direct cause of the following exception:</font><br>'
                )
            elif exc.__context__:
                yield from cgitb_chain(exc.__context__)
                yield (
                    '<br><br><font color="#51B432">During handling of the '
                    'above exception, another exception occurred:</font><br>'
                )
            yield cgitb_html(exc)

        def cgitb_html(exc: Exception) -> str:
            """Format exception with cgitb.html."""
            info = (type(exc), exc, exc.__traceback__)
            return cgitb.html(info)

        def format_exc_info(info: ExcInfoTuple, as_html: bool) -> str:
            if as_html:
                html = "\n".join(cgitb_chain(info[1]))
                # cgitb has a lot of hardcoded colors that don't work for us
                # remove bgcolor, and let theme handle it
                html = re.sub('bgcolor="#.*"', '', html)
                # remove superfluous whitespace
                html = html.replace('<br>\n', '\n')
                # but retain it around the <small> bits
                html = re.sub(r'(<tr><td><small.*</tr>)', f'<br>\\1<br>', html)
                # weird 2-part syntax is a workaround for hard-to-grep text.
                html = html.replace(
                    "<p>A problem occurred in a Python script.  "
                    "Here is the sequence of",
                    "",
                )
                html = html.replace(
                    "function calls leading up to the error, "
                    "in the order they occurred.</p>",
                    "<br>",
                )
                # remove hardcoded fonts
                html = html.replace('face="helvetica, arial"', "")
                html = (
                    "<span style='font-family: monaco,courier,monospace;'>"
                    + html
                    + "</span>"
                )
                return html
            else:
                # if we don't need HTML, just use traceback
                return ''.join(traceback.format_exception(*info))

    return format_exc_info


def fetch_module_metadata(dist: Union[Distribution, str]) -> Dict[str, str]:
    """Attempt to retrieve name, version, contact email & url for a package.

    Parameters
    ----------
    distname : str or Distribution
        Distribution object or name of a distribution.  If a string, it must
        match the *name* of the package in the METADATA file... not the name of
        the module.

    Returns
    -------
    package_info : dict
        A dict with metadata about the package
        Returns None of the distname cannot be found.
    """
    if isinstance(dist, Distribution):
        meta = dist.metadata
    else:
        try:
            meta = importlib_metadata.metadata(dist)
        except importlib_metadata.PackageNotFoundError:
            return {}
    return {
        'package': meta.get('Name', ''),
        'version': meta.get('Version', ''),
        'summary': meta.get('Summary', ''),
        'url': meta.get('Home-page') or meta.get('Download-Url', ''),
        'author': meta.get('Author', ''),
        'email': meta.get('Author-Email') or meta.get('Maintainer-Email', ''),
        'license': meta.get('License', ''),
    }


ANSI_STYLES = {
    1: {"font_weight": "bold"},
    2: {"font_weight": "lighter"},
    3: {"font_weight": "italic"},
    4: {"text_decoration": "underline"},
    5: {"text_decoration": "blink"},
    6: {"text_decoration": "blink"},
    8: {"visibility": "hidden"},
    9: {"text_decoration": "line-through"},
    30: {"color": "black"},
    31: {"color": "red"},
    32: {"color": "green"},
    33: {"color": "yellow"},
    34: {"color": "blue"},
    35: {"color": "magenta"},
    36: {"color": "cyan"},
    37: {"color": "white"},
}


def ansi2html(
    ansi_string: str, styles: Dict[int, Dict[str, str]] = ANSI_STYLES
) -> Generator[str, None, None]:
    """Convert ansi string to colored HTML

    Parameters
    ----------
    ansi_string : str
        text with ANSI color codes.
    styles : dict, optional
        A mapping from ANSI codes to a dict of css kwargs:values,
        by default ANSI_STYLES

    Yields
    -------
    str
        HTML strings that can be joined to form the final html
    """
    previous_end = 0
    in_span = False
    ansi_codes = []
    ansi_finder = re.compile("\033\\[" "([\\d;]*)" "([a-zA-z])")
    for match in ansi_finder.finditer(ansi_string):
        yield ansi_string[previous_end : match.start()]
        previous_end = match.end()
        params, command = match.groups()

        if command not in "mM":
            continue

        try:
            params = [int(p) for p in params.split(";")]
        except ValueError:
            params = [0]

        for i, v in enumerate(params):
            if v == 0:
                params = params[i + 1 :]
                if in_span:
                    in_span = False
                    yield "</span>"
                ansi_codes = []
                if not params:
                    continue

        ansi_codes.extend(params)
        if in_span:
            yield "</span>"
            in_span = False

        if not ansi_codes:
            continue

        style = [
            "; ".join([f"{k}: {v}" for k, v in styles[k].items()]).strip()
            for k in ansi_codes
            if k in styles
        ]
        yield '<span style="%s">' % "; ".join(style)

        in_span = True

    yield ansi_string[previous_end:]
    if in_span:
        yield "</span>"
        in_span = False
