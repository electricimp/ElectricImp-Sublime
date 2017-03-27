Electric Imp Sublime Plug-in (Beta)
==================================

- [Overview](#overview)
- [Installation Steps](#installation-steps)
    - [Install Node.js](#install-nodejs)
    - [Install the Builder Node.js Module](#install-the-builder-nodejs-module)
    - [Install the Electric Imp Sublime Plug-in](#install-the-electric-imp-sublime-plug-in)
- [Usage](#usage)
    - [Creating a New Project](#creating-a-new-project)
    - [Opening an Existing Project](#opening-an-existing-project)
    - [Building and Running](#building-and-running)
    - [Model Management](#model-management)
    - [Logs Console](#logs-console)
    - [Selecting a Device](#selecting-a-device)
    - [Adding a Device to the Model](#adding-a-device-to-the-model)
    - [Removing a Device from the Model](#removing-a-device-from-the-model)
    - [Retrieving a Device’s Agent URL](#retrieving-a-devices-agent-url)
    - [Key Shortcuts](#key-shortcuts)
- [Preprocessor and Multi-File Support](#preprocessor-and-multi-file-support)
    - [Specifying GitHub Authentication Information](#specifying-github-authentication-information)
    - [Specifying Builder Preset Variable Definitions](#specifying-builder-preset-variable-definitions)
- [Features Supported in the Current Version](#features-supported-in-the-current-version)
- [Future Development Plans](#future-development-plans)

## Overview

The Plugin is designed to improve developer productivity and allows to rapidly build and maintain applications by 
providing:

* Code auto-completion for []Electric Imp Squirrel API](https://electricimp.com/docs/api/)
* Ability to use a source control system to manage application code and configuration
* Advanced Squirrel code highlighting
* Integration the [Builder](https://github.com/electricimp/Builder) to enable multi-file 
projects and code preprocessing
* Live logs with clickable stack traces for errors with navigation to the file and line in question
* Using key shortcuts for frequent operations (build and run, show console, etc)
* Leveraging the rich set of Sublime Text 3 Editor features.

The Plugin requires connection to the Internet as it leverages the 
[Electric Imp Build API]([Electric Imp Build API](https://electricimp.com/docs/buildapi/)) 
to work with the the [Electric Imp impCloud™](https://electricimp.com/platform/cloud/).

## Installation Steps

**NOTE**: Electric Imp Sublime Plugin supports [Sublime Text 3](https://www.sublimetext.com/3) only, no other versions are 
supported. Tested on OS X only.

### Install Node.js

**Note** The plug-in requires Node.js 4.0 or above.**

Please follow [these instructions](https://nodejs.org/en/download/package-manager/) to install Node on your machine.
  
### Install the Builder Node.js Module

The plug-in uses the [Builder](https://github.com/electricimp/Builder) Node.js module for source code pre-processing. 
To install Builder, please use Node Package Manage (NPM):

```
npm i -g Builder
```

### Install the Electric Imp Sublime Plug-in

You can install the plugin script via the following command in the Sublime Text terminal (`ctrl+` `) 
which utilizes `git clone`. 

**NOTE**: Please make sure you have git installed on your system when trying this method.

```python
import os; path=sublime.packages_path(); (os.makedirs(path) if not os.path.exists(path) else None); window.run_command('exec', {'cmd': ['git', 'clone', 'https://github.com/electricimp/ElectricImp-Sublime.git', 'imp-developer'], 'working_dir': path}); window.run_command('exec', {'cmd': ['git', 'pull'], 'working_dir': os.path.join(path, "imp-developer")})
```

Alternatively, follow these steps to install the plug-in manually:

Download the full GitHub source repository or clone it from 
[https://github.com/electricimp/ElectricImp-Sublime](https://github.com/electricimp/ElectricImp-Sublime) into

- **macOS**: */Users/&lt;username&gt;/Library/Application Support/Sublime Text 3/Packages/*
- **Windows**: *"%AppData%\Sublime Text 3\Packages\%"*


## Usage

### Creating a New Project

First step is creation of a project by selecting `Tools -> Packages -> Electric Imp -> Create Project` menu item. 
On the new project creation the user is asked to specify the project folder.

The  project folder will be set up with the following

```
-- <Project Name>
  |--> settings                           - Electric Imp settings folder
  .   |--> auth.info                      - SENSITIVE: Build API key and GitHub authentication information
  .   |--> electric-imp.settings          - Generic Electric Imp settings
  |--> src                                - Source folder 
  .   |--> device.nut                     - Device code
  .   |--> agent.nut                      - Agent code
  |--> .gitignore                         - .gitignore file to exclude Build API key from git repository
  |--> electric-imp.sublime-project       - Sublime project file
```

**IMPORTANT** *settings/auth.info* **should not be put under a source control as it contains sensitive information!**

The `electric-imp.settings` file contains:

- Imp Model ID for the project
- Selected device id
- Device and Agent code file names

```
{
  "model-id"      : "my-model-id",
  "device-id"     : "my-selected-device-id",
  "device-file"   : "src/device.nut",
  "agent-file"    : "src/agent.nut",
}
```

When a project is created, empty device and agent code (`device.nut` and `agent.nut`) files are automatically created 
and stored in the `src` project folder.

If a project is created successfully, a new window with the project folder is opened. 

**NOTE**: If you need to apply the Squirrel language syntax highlighting to files with extension other than `.nut`
please make sure you have Squirrel (Electric Imp) languages selected under the `View -> Syntax` menu item. 

### Opening an Existing Project

To open an existing Electric Imp project, select the `Project -> Open Project...` menu option and choose the 
<Project Name>.sublime-project file from your project directory.

**NOTE: The plugin won't properly detect Electric Imp project if it's not opened as described, i.e. if it's opened
as a folder, not as a Text Sublime project!**

### Building and Running

To build and deploy the application code, please select `Tools -> Packages -> Electric Imp -> Build and Run` menu item.
This action uploads the agent and the device code to the server and restarts the model with all the devices attached.

When one builds the code (or does any other action, that requires access to the imp server) for the first time, 
the user is asked to provide:

- Path to the Node.js executable (if not automatically detected by the plugin).
- Location of the Builder cli.js command line tool (if not automatically detected by the plugin).
- Build API Key - can be obtained at the [Web IDE](https://ide.electricimp.com) by clicking on user name link at the 
top right corner and selecting the Build API Keys menu item 
- New Model name to be created for the project or one of the existing ones to be selected. You can create you model 
at `Tools -> Packages -> Electric Imp -> Create Model`.

**NOTE**: to build and deploy your code it's not necessary to select a device for your project. Even if you don't have a 
device selected, you still can work on the code, see compilation errors reported by the server.

If you want to have you code running on a specific device and see view the logs from it, 
you need to add a device to the Model 
(`Tools -> Packages -> Electric Imp -> Add Device`).

### Model Management

Each Electric Imp project is associated with a particular Model, i.e. application code for device and agent.
One can create a new project Model by selecting `Tools -> Packages -> Electric Imp -> Create Model`. 

You can also select an existing Model and associate the project with it through 
`Tools -> Packages -> Electric Imp -> Select Model` menu item.

**IMPORTANT: The code which is deployed to the Model is preprocessed and contains line control markers in it. On the Model
selection the plugin pulls down the Model code, but it doesn't restore the original file/folder structure.
So for collaborative work on the same Model sources, please share the original Electric Imp plugin project 
sources/structure via a source control.**

### Logs Console

The Console can be popped up by selecting `Tools -> Packages -> Electric Imp -> Show Console` menu item. 
The Console shows live logs from the Model and the selected device.

You can add other devices enrolled into your account to the project model by selecting ‘Electric Imp’ > ‘Model’ > ‘Device’ > ‘Add’.The newly added device is automatically selected as the current one, which means the Console will show its logs.

To add a device to the project model, select `Tools -> Packages -> Electric Imp -> Add Device` menu item. 
The newly added device
is selected as the current one, which means the Console will show the logs for it.

### Selecting a Device

Device of the Model the project is associated with can be selected through the 
`Tools -> Packages -> Electric Imp -> Select Device` menu item. The selected device will used as a source of logs 
for the Logs Console.

### Removing a Device from the Model

Devices can be removed from the model by selecting `Tools -> Packages -> Electric Imp -> Remove Device`.

**NOTE**: you can't delete an active device (the one that is currently selected for the project).

### Retrieving a Device's Agent URL

Agent URL can be retrieved by selecting `Tools -> Packages -> Electric Imp -> Get Agent URL` menu item. 
The URL is saved in the clipboard.

### Key Shortcuts

**Note** Electric Imp-specific menu items are only available if an Electric Imp project is opened in the currently active window.

| Command | Keypress |
| ------- | -------- |
| Create Project | Ctrl + Shift + L|
| Build and Run | Ctrl + Shift + X |
| Show Logs Console | Ctrl + Shift + C |

## Preprocessor and Multi-File Support
 
Please refer to the [Builder documentation](https://github.com/electricimp/Builder) for more information on the preprocessor syntax that you can use in your Squirrel code.

### Specifying GitHub Authentication Information

Please use the project `<project folder>/settings/auth.info` file to specify your Builder GitHub authentication 
information: 
```
{
    ...
    "builder-settings": {
        "github-user": "GitHub user name", 
        "github-token": "Personal access token or password"
    }
}
```

### Specifying Builder Preset Variable Definitions

Please use the project `<project folder>/settings/electric-imp.settings` file to specify the Builder 
variables definitions: 
```
{
    "builder-settings": {
        ...
        "variable-definitions": {
            "key1": "value1", 
            "key2": "value2"
        },
        ...
    }
}
```

## License

The Electric Imp Sublime Plugin is licensed under the [MIT License](./LICENSE).
