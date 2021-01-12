# Roadmap

## For 0.4.* series of releases - November 2020

The napari roadmap captures current development priorities within the project and aims to guide for napari core developers, to encourage and inspire contributors, and to provide insights to external developers who are interested in building for the napari ecosystem. For more details on what this document is and is not, see the [about this document section](#about-this-document).

The [mission](MISSION_AND_VALUES.md#our-mission) of napari is to be a foundational multi-dimensional image viewer for Python and provide graphical user interface (GUI) access to image analysis tools from the Scientific Python ecosystem for scientists across domains and levels of coding experience. To work towards this mission, we have set the following three high-level priorities to guide us over the upcoming months:

- Make the **data viewing and annotation** capabilities **bug-free, fast, and delightful to use**.

- Support **functional and interactive** plugins that enable complete image analysis workflows.

- Add accessible **documentation**, tutorials, and demos.

You can read more about how this roadmap builds on and continues the work in our `0.3` series of releases in our [0.3 retrospective](https://napari.org/docs/dev/developers/ROADMAP_0_3_retrospective.html). We're continuing to prioritize the robustness and polish of the core viewer to ensure that plugin development happens against a solid foundation, and because we believe that looking at and annotating your data should be a bug free and delighful experience, regardless of how large it is. We want to build on the success of our reader / writer plugins to provide the ability to add functional and interactive plugins and further empower a lot of the great work being built ontop of napari.

## Make the data viewing and annotation capabilities bug-free, fast, and delightful to use

- ...

- **Better support for viewing big datasets**. Currently, napari is fast when viewing on-disk datasets that can be naturally sliced along one axis (e.g. a time series) *and where loading one slice is fast*. However, when the loading is slow, the napari UI itself becomes slow, sometimes to the point of being unusable. We now have experimental support for asyncronous rendering for our images, and are in the process of adding support for an octree to better support multiscale tiled data for both 2D and 3D rendering.

- **Improving the performance of operations on in-memory data**. Even when data is loaded in memory, some operations, such as label and shape painting or slicing along large numbers of points can be slow. We will continue developing our [benchmark suite](https://github.com/napari/napari/blob/master/docs/developers/BENCHMARKS.md) and work to integrate it into our development process. See the [`performance` label](https://github.com/napari/napari/labels/performance) for a current list of issues related to performance.

- Add **physical coordinates**. We now have a world coordinate system and transforms that can move between data coordinates, world coordinates, and the canvas where things are rendered; however, we still don't have a concept of phyiscal units. See [#1701](https://github.com/napari/napari/issues/1701) for additional discussion.

- Add **linked multi-canvas support** ([#760](https://github.com/napari/napari/issues/760)) to allow orthogonal views, or linked views of two datasets, for example to select keypoints for image alignment, or simultaneous 2D slices with 3D rendering.

- Add **layer groups** [#970](https://github.com/napari/napari/issues/970), which allow operating on many layers simultaneously making the viewer easier to use for multispectral or multimodal data, or, in the context of multiple canvases, where one wants to assign different groups to different canvases.

- Complete **serialization of the viewer** [#851](https://github.com/napari/napari/pull/851) to enable sharing the entire viewer state, see [#1875](https://github.com/napari/napari/issues/1875) too.

- Improved **error handling and bug reporting**, see [#1090](https://github.com/napari/napari/issues/1090) for details.

- Support for persistent settings [#1183](https://github.com/napari/napari/pull/1183) to allow **saving of preferences** between launches of the viewer.

- Improve the **user interface and design** of the viewer to make it easier to use. We have conducted a product heuristics analysis to [identify design and usability issues](https://github.com/napari/product-heuristics-2020), and will now be working during the 0.4 series of releases to implement them. Also see the [`design` label](https://github.com/napari/napari/labels/design) for more information.

## Support **functional and interactive** plugins that enable complete image analysis workflows.

0.4.3 brought experimental support for functional plugins and interactive Qt
widget plugins. During the 0.4.x series of releases, we aim to work with our
community to strengthen that support, identify gaps in functionality, and fill
those gaps, either with new plugin types or by modifying the existing plugin
architecture to suit developer and user needs. Ideally, before 0.5.0,
functional and interactive plugins move out of experimental support and become
permanent features.

For more details, follow the [plugins label on
GitHub](https://github.com/napari/napari/labels/plugins).


## Provide accessible **documentation**, tutorials, and demos

- Improve our website [napari.org](https://napari.org) to provide easy access to all napari related materials, including the [**four types of documentation**](https://www.divio.com/blog/documentation/): learning-oriented tutorials, goal-oriented how-to-guides or galleries, understanding-oriented explanations (including developer resources), and a comprehensive API reference. See [#764](https://github.com/napari/napari/issues/764) and the [`documentation` label](https://github.com/napari/napari/labels/documentation) on the napari repository for more details.

- Support autogenerated screenshots and movies for our documentation to ensures it always stays up-to-date as we improve napari. These examples should also be runnable by our users to serve as training materials as they learn to use napari.

- Add a **napari human interface guide** for plugin developers, akin to [Apple's Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/). We want such a guide to promote best practices and ensure that plugins provide a consistent user experience.

## Work prioritized for future roadmaps

We’re also planning to prioritized the following work in future roadmaps:

- General support for undo / redo functionality [#474](https://github.com/napari/napari/issues/299), a history feature, and macro generation.

- Draggable and resizable layers [#299](https://github.com/napari/napari/issues/299) and [#989](https://github.com/napari/napari/pull/989).

- Linked 1D plots such as histograms, timeseries, or z-profiles [#823](https://github.com/napari/napari/pull/823) and [#675](https://github.com/napari/napari/pull/675).

- Support for using napari with remote computation.

- Asynchronous and multiscale support beyond the image layer.

## About this document

This document is meant to be a snapshot of tasks and features that the `napari` team is investing resources in during our 0.4 series of releases starting November 2020. This document should be used to guide napari core developers, encourage and inspire contributors, and provide insights to external developers who are interested in building for the napari ecosystem. It is not meant to limit what is being worked on within napari, and in accordance with our [values](MISSION_AND_VALUES.md#our-values) we remain **community-driven**, responding to feature requests and proposals on our [issue tracker](https://github.com/napari/napari/issues) and making decisions that are driven by our users’ requirements, not by the whims of the core team.

This roadmap is also designed to be in accordance with our stated [mission](MISSION_AND_VALUES.md#our-mission) to be the **multi-dimensional image viewer for Python** and to **provide graphical user interface (GUI) access to a plugin ecosystem of image analysis tools for scientists** to use in their daily work.

For more details on the high level goals and decision making processes within napari you are encouraged to read our [mission and values statement](MISSION_AND_VALUES.md) and look at our [governance model](GOVERNANCE.md). If you are interested in contributing to napari, we'd love to have your contributions, and you should read our [contributing guidelines](CONTRIBUTING.md) for information on how to get started.

Another good place to look for information around bigger-picture discussions within napari are our issues tagged with the [`long-term feature` label](https://github.com/napari/napari/labels/long-term%20feature).