# OSeMOSYS-Flextool
Integrating OSeMOSYS and IRENA FlexTool energy system models. Includes transforming a OSeMOSYS model to FlexTool through INES specification (https://github.com/ines-tools/ines-spec) and running OSeMOSYS as capacity expansion model and passing these results to FlexTool, where the flexibility of the new system can be tested.

For this workflow, two transformations were added to the INES-tools. These are OSeMOSYS to INES specification:
https://github.com/ines-tools/ines-osemosys and from INES specification to FlexTool https://github.com/ines-tools/ines-flextool. Additionally, some generic functions are needed from INES-tools (https://github.com/ines-tools/ines-tools).

This uses Spine-Toolbox for the database and workflow management (https://github.com/spine-tools/Spine-Toolbox)

For running the OSeMOSYS separately in Spine Toolbox go to: 
https://github.com/OSeMOSYS-FlexTool-integration/OSeMOSYS-SpineToolbox

# Status

NOT FUNCTIONAL!

Still missing Osemosys to ines transformation parameters and result passing between models.
Better documentation is done, once the workflow is functional.

# Installation

Git clone this repository.

Additionally, git clone these three repositorys to parrallel folders:

- INES-OSEMOSYS: https://github.com/ines-tools/ines-osemosys
- INES-FlexTool: https://github.com/ines-tools/ines-flextool
- INES-tools: https://github.com/ines-tools/ines-tools


The workflow is done using Spine-Toolbox. Read the installation instructions from:
https://github.com/spine-tools/Spine-Toolbox


