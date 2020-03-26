Announcement: napari 0.3.0
==========================

We're happy to announce the release of napari 0.3.0!
napari is a fast, interactive, multi-dimensional image viewer for Python.
It's designed for browsing, annotating, and analyzing large multi-dimensional
images. It's built on top of Qt (for the GUI), vispy (for performant GPU-based
rendering), and the scientific Python stack (numpy, scipy).


For more information, examples, and documentation, please visit our website:
https://github.com/napari/napari

Highlights
**********

New Features
************

Improvements
************

Bugfixs
*******

API Changes
***********

Deprecations
************

Build Tools
***********

Other Pull Requests
*******************
- generalize keybindings (#791)
- Hook up reader plugins (#937)
- Points view data refactor (#951)
- publish developer resources (#967)
- Support for magicgui (#981)
- fix recursive include in manifest.in (#1003)
- add magic name guessing (#1008)
- Refactor labels layer mouse bindings (#1010)
- Fix pip install with older versions of pip (#1011)
- Refactor cleanup, prevent leaked widgets, add viewer.close method (#1014)
- Reduce code duplication: vispy _on_scale_change() & _on_translate_change() (#1015)
- Style refactor (#1017)
- Add ScaleTranslate transform (#1018)
- Add docstrings for all the Qt classees (#1022)
- Allow StringEnum to accept instances of self as argument (#1027)
- Close the canvas used to retrieve maximum texture size. (#1028)
- Fix points color cycle refresh (#1034)
- Fix styles for Qt < 5.12.  Fix styles in manifest for pip install (#1037)
- Fix label styles in contrast limit popup  (#1039)
- Add chains of transforms (#1042)
- Shapes layer internal renaming (#1046)
- Internal utils / keybindings / layer accessories renaming (#1047)
- make console loading lazy (#1055)
- check if PyQt5 is installed and then not install PySide2 (#1059)
- fix resources/build_icons:build_resources_qrc (#1060)
- add error raise in Viewer._add_layer_from_data (#1063)
- use pip instead of invoking setup.py (#1072)
- fix image format (#1076)
- pyenv with PyQt5 in other enviroment workaround (#1080)
- Lazy console fixes (#1081)
- Fix function and signature to match with code (#1083)

7 authors added to this release (alphabetical)
----------------------------------------------
- `Genevieve Buckley <https://github.com/napari/napari/commits?author=GenevieveBuckley>`_ - `@GenevieveBuckley <https://github.com/GenevieveBuckley>`_
- `Grzegorz Bokota <https://github.com/napari/napari/commits?author=Czaki>`_ - `@Czaki <https://github.com/Czaki>`_
- `kevinyamauchi <https://github.com/napari/napari/commits?author=kevinyamauchi>`_ - `@kevinyamauchi <https://github.com/kevinyamauchi>`_
- `Kira Evans <https://github.com/napari/napari/commits?author=kne42>`_ - `@kne42 <https://github.com/kne42>`_
- `Nicholas Sofroniew <https://github.com/napari/napari/commits?author=sofroniewn>`_ - `@sofroniewn <https://github.com/sofroniewn>`_
- `Talley Lambert <https://github.com/napari/napari/commits?author=tlambert03>`_ - `@tlambert03 <https://github.com/tlambert03>`_
- `Tony Tung <https://github.com/napari/napari/commits?author=ttung>`_ - `@ttung <https://github.com/ttung>`_


10 reviewers added to this release (alphabetical)
-------------------------------------------------
- `Ahmet Can Solak <https://github.com/napari/napari/commits?author=AhmetCanSolak>`_ - `@AhmetCanSolak <https://github.com/AhmetCanSolak>`_
- `Genevieve Buckley <https://github.com/napari/napari/commits?author=GenevieveBuckley>`_ - `@GenevieveBuckley <https://github.com/GenevieveBuckley>`_
- `Grzegorz Bokota <https://github.com/napari/napari/commits?author=Czaki>`_ - `@Czaki <https://github.com/Czaki>`_
- `Juan Nunez-Iglesias <https://github.com/napari/napari/commits?author=jni>`_ - `@jni <https://github.com/jni>`_
- `kevinyamauchi <https://github.com/napari/napari/commits?author=kevinyamauchi>`_ - `@kevinyamauchi <https://github.com/kevinyamauchi>`_
- `Kira Evans <https://github.com/napari/napari/commits?author=kne42>`_ - `@kne42 <https://github.com/kne42>`_
- `Nicholas Sofroniew <https://github.com/napari/napari/commits?author=sofroniewn>`_ - `@sofroniewn <https://github.com/sofroniewn>`_
- `Shannon Axelrod <https://github.com/napari/napari/commits?author=shanaxel42>`_ - `@shanaxel42 <https://github.com/shanaxel42>`_
- `Talley Lambert <https://github.com/napari/napari/commits?author=tlambert03>`_ - `@tlambert03 <https://github.com/tlambert03>`_
- `Tony Tung <https://github.com/napari/napari/commits?author=ttung>`_ - `@ttung <https://github.com/ttung>`_

