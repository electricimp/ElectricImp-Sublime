Electric Imp Sublime Plugin
=================================

**Electric Imp Sublime Plugin supports [Sublime Text 3](https://www.sublimetext.com/3) only, no other versions are 
supported. Tested on OS X only.**

## Installation (manual)

### Installing Node.js

The plugin requires Node.js to be installed on the machine. Please follow 
[instructions](https://nodejs.org/en/download/package-manager/) to install Node on your machine.
  
### Installing Builder Node.js Module

The plugin uses [Builder](https://github.com/electricimp/Builder) Node.js module for source code pre-processing. 
To install the Builder module, please use npm command:

```
npm i -g Builder
```

### Installing the Plugin

You can install the plugin script via the following command in the Sublime Text terminal (``ctrl+` ``) 
which utilizes `git clone`.

```python
import os; path=sublime.packages_path(); (os.makedirs(path) if not os.path.exists(path) else None); window.run_command('exec', {'cmd': ['git', 'clone', 'https://github.com/electricimp/ElectricImp-Sublime.git', 'imp-developer'], 'working_dir': path})
```

or follow the steps manually:

1. Download or checkout the plugin package from https://github.com/ElectricImp-CSE/ElectricImp-Sublime
2. Install the plugin by manally copying the package content into
    - (OS X): /Users/&lt;username&gt;/Library/Application Support/Sublime Text 3/Packages/
    - (Windows): "%AppData%\Sublime Text 3\Packages\%"

## Usage

### Creating a new Project

First step is creation of a project by selecting ``Electric Imp->Create Project`` menu item. On the new project creation 
the user is asked to specify the project folder.

As the result project is created at the specified location:

```
-- <Project Name>
  |--> settings                           - Electric Imp settings folder
  .   |--> build-api.key                  - SENSITIVE: Build API key stored for the project
  .   |--> electric-imp.settings          - Generic Electric Imp settings
  |--> src                                - Source folder 
  .   |--> <Model Name>.device.nut        - Device code
  .   |--> <Model Name>.agent.nut         - Agent code
  |--> .gitignore                         - .gitignore file to exclude Build API key from git repository
  |--> <Project Name>.sublime-project     - Sublime project file
```

**IMPORTANT: settings/build-api.key should not be put under a source control as it contains sensitive information!**

<Project Name>.electric-imp-settings file contains:

- Imp Model ID for the project
- Device and Agent code file names
- Selected device id

```
{
  "model-id"      : "my-model-id",
  "device-file"   : "device.nut",
  "agent-file"    : "agent.nut",
  "device-id"     : "my-selected-device-id"
}
```

### Opening an existing Project

To open an existing Electric Imp project, select the ``Project->Open Project...`` menu option and choose the 
<Project Name>.sublime-project file from your project directory.

**The plugin won't properly detect Electric Imp project if it's not opened as described, i.e. if it's opened
as a folder, not as a Text Sublime project!**

### Building the Code

To build and deploy the application code, please select ``Electric Imp->Build and Run`` menu item.

When one builds the code (or does any other action, that requires access to the imp server) for the first time, the user 
is asked to provide:

- [ ] Build API Key - can be obtained at the [Web IDE](https://ide.electricimp.com) by clicking on user name link at the 
top right corner and selecting the Build API Keys menu item 
- [ ] New Model name to be created for the project. Each Electric Imp project is associated with a particular Model, 
i.e. application code.

NOTE: to build and deploy your code it's not necessary to select a device for your project. Even if you don't have a 
device selected, you still can work on the code and receive compilation errors from the server.

If you want to have you code running on a specific device and see it's logs, you need to select a device 
(``Electric Imp->Device->Select`` Device).

When a project is created the empty device and agent code (device.nut and agent.nut) files are automatically created 
and stored in the ``src`` project folder.

If a project is created successfully, a new window with the project folder is opened. 

### Building and Running the Code

The code can be pushed to the Model by selecting ``Electric Imp->Build and Run`` menu item. 
This action uploads the agent and the device code to the server and restarts the model with all the devices attached.

### Logs Console

The Console can be popped up by selecting ``Electric Imp->Show Console`` menu item. The Console shows live logs
from the Model and the selected device.

### Selecting Device

Device can be selected through the ``Electric Imp->Device->Select Device`` menu item. The selected device is used as a 
source of logs for the Server Logs Console.

### Adding Device to the Model

To add a device to the project model, select ``Electric Imp->Device->Add Device`` menu item. The newly added device
is selected as the current one, which means the Console will show the logs for it.

### Removing Device from the Model

Devices can be removed from the model by selecting ``Electric Imp->Device->Remove Device``.

NOTE: one can't delete an active device (the one that is currently selected as current for the project).

### Retrieving Agent URL

Agent URL can be retrieved by selecting ``Electric Imp->Get Agent URL`` menu item. The URL is saved in the clipboard.

### Key Shortcuts

**Electric Imp specific menu items are only available if an Electric Imp project is opened in the currently active window**

- Create Project: Ctrl + Shift + L
- Deploy project: Ctrl + Shift + D
- Show Logs Console: Ctrl + Shift + C
- Select Device: Ctrc + Shift + I


## Features supported in the current Version

- Push of the code to the server
- Live logs view
- Generating a URL to the agent associated with the device
- An early version of the Squirrel language code highlighter (Alpha version, may not be accurate)
- An early version of the API inline code suggestions (Alpha version, may not be accurate)

## Existing restrictions

- No inline code compilation errors or code lintering is provided
- No multiple file support
- No refactoring or sophistiated navigation features (except those available in the editor out of the box)
- No way to change a model for the project

## Future Development Plans

- Improved highlighting and API suggestions
- Multiple files support
- Squirrel code lintering and inline error highlighting
- Advanced Squirrel preprocessor support
- Squirrel refactoring or advanced navigation features
- Simple administrative functionality (managing Models, devices, migration of devices, etc.)