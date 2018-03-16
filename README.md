Electric Imp impCentral Sublime Plug-in (Beta)
==================================

[Sublime Text 3](https://www.sublimetext.com/3) plug-in for [Electric Imp](https://electricimp.com) applications development.

- [Overview](#overview)
- [Installation Steps](#installation-steps)
    - [Install Node.js](#install-nodejs)
    - [Install the Builder Node.js Module](#install-the-builder-nodejs-module)
    - [Install the Electric Imp Sublime Plug-in](#install-the-electric-imp-sublime-plug-in)
- [Usage](#usage)
    - [Creating a New Project](#creating-a-new-project)
    - [Opening an Existing Project](#opening-an-existing-project)
    - [Building and Running](#building-and-running)
    - [Project Management](#project-management)
    - [Logs Console](#logs-console)
    - [Selecting a Device](#selecting-a-device)
    - [Adding a Device to the DeviceGroup](#adding-a-device-to-the-devicegroup)
    - [Removing a Device from the DeviceGroup](#removing-a-device-from-the-devicegroup)
    - [Retrieving a Device’s Agent URL](#retrieving-a-devices-agent-url)
    - [Key Shortcuts](#key-shortcuts)
- [Preprocessor and Multi-File Support](#preprocessor-and-multi-file-support)
    - [Specifying GitHub Authentication Information](#specifying-github-authentication-information)
    - [Specifying Builder Preset Variable Definitions](#specifying-builder-preset-variable-definitions)
- [Features Supported in the Current Version](#features-supported-in-the-current-version)
- [Future Development Plans](#future-development-plans)

## Overview

The Plug-in is designed to improve developer productivity and allows to rapidly build and maintain applications by
providing:

* Code auto-completion for [Electric Imp Squirrel API](https://electricimp.com/docs/api/)
* Ability to use a source control system to manage application code and configuration
* Advanced Squirrel code highlighting
* Integration the [Builder](https://github.com/electricimp/Builder) to enable multi-file
projects and code preprocessing
* Live logs with clickable stack traces for errors with navigation to the file and line in question
* Using key shortcuts for frequent operations (build and run, show console, etc)
* Leveraging the rich set of Sublime Text 3 Editor features.

The Plug-in requires connection to the Internet as it leverages the
[Electric Imp impCentral API V5](https://developer.electricimp.com/tools/impcentralapi/)
to work with the [Electric Imp impCloud™](https://electricimp.com/platform/cloud/).

## Installation Steps

**NOTE**: Electric Imp Sublime Plug-in supports [Sublime Text 3](https://www.sublimetext.com/3) only, no other versions are
supported. Tested on macOS only.

### Install Node.js

**NOTE**: The plug-in requires Node.js 4.0 or above.

Please follow [these instructions](https://nodejs.org/en/download/package-manager/) to install Node on your machine.

### Install the Builder Node.js Module

The plug-in uses the [Builder](https://github.com/electricimp/Builder) Node.js module for source code pre-processing.
To install Builder, please use Node Package Manage (NPM):

```
npm i -g Builder
```

### Install the Electric Imp Sublime Plug-in

#### Package Control

If you already have [Package Control](http://wbond.net/sublime_packages/package_control/) installed in Sublime Text:

* Select `Install Package` from the Command Palette: <kbd>Ctrl+Shift+P</kbd> on Windows and Linux or <kbd>⇧⌘P</kbd> on macOS
* Search for **Electric Imp Developer** and click <kbd>enter</kbd>.

#### From Sublime Text Terminal

You can install the plug-in script via the following command in the Sublime Text terminal (``ctrl+` ``) which utilizes `git clone`.

**NOTE**: Please make sure you have git installed on your system when trying this method.

```python
import os; path=sublime.packages_path(); ie_plugin_path=os.path.join(path, 'imp-developer'); (os.makedirs(path) if not os.path.exists(path) else None); window.run_command('exec', {'cmd': ['git', 'clone', 'https://github.com/electricimp/ElectricImp-Sublime.git', 'imp-developer'], 'working_dir': path}) if not os.path.exists(ie_plugin_path) else window.run_command('exec', {'cmd': ['git', 'pull'], 'working_dir': ie_plugin_path})
```
#### Manual

Alternatively, follow these steps to install the plug-in manually:

1. Create the *plug-in folder*:
    - **macOS**: */Users/&lt;username&gt;/Library/Application Support/Sublime Text 3/Packages/imp-developer*
    - **Windows**: *"%AppData%\Sublime Text 3\Packages\imp-developer%"*

2. Do one of the following:
    - Download the full GitHub source [repository](https://github.com/electricimp/ElectricImp-Sublime) as a zip file and extract it's content into the *plug-in folder* (`Sublime Text 3/Packages/imp-developer`) or
    - Clone the contents of the source repository [https://github.com/electricimp/ElectricImp-Sublime](https://github.com/electricimp/ElectricImp-Sublime) into the *plugin folder* (`Sublime Text 3/Packages/imp-developer`).

## Usage

### Creating a New Project

Your first step should be the creation of a new project.
Do this by selecting the `Tools` > `Packages` > `Electric Imp` > `Create Project` menu item.
You will then be asked to specify the project folder.

The  project folder will be set up with the following

```
-- <Project Name>
  |--> settings                           - Electric Imp settings folder
  .   |--> auth.info                      - SENSITIVE: impCentral API tokens and GitHub authentication information
  .   |--> electric-imp.settings          - Generic Electric Imp settings
  |--> src                                - Source folder
  .   |--> device.nut                     - Device code
  .   |--> agent.nut                      - Agent code
  |--> .gitignore                         - .gitignore file to exclude auth.info file from git repository
  |--> electric-imp.sublime-project       - Sublime project file
```

**IMPORTANT: `settings/auth.info` should not be put under a source control as it
contains sensitive information!**

The `electric-imp.settings` file contains:

- Unique project identifier
- Unique device group identifier
- The latest deployment which was done via plug-in
- Device and Agent code file names

```
{
  "product-id"    : "my-product-id",
  "devicegroup-id": "my-device-group-id",
  "deployment-id" : "deployment-new" or "my-deployment-id"
  "device-file"   : "src/device.nut",
  "agent-file"    : "src/agent.nut"
}
```

When a project is created, empty device and agent code files (`device.nut` and `agent.nut`) are automatically created
and stored in the `<Project Name>/src` folder.

If a project is created successfully, a new window with the project folder is opened.

**NOTE**: If you need to apply the Squirrel language syntax highlighting to files with extension other than `.nut`
please make sure you have Squirrel (Electric Imp) language selected under the `View` > `Syntax` menu item.

### Opening an Existing Project

To open an existing Electric Imp project, select the `Project` > `Open Project...` menu option and choose the
`<Project Name>.sublime-project` file from your project folder.

**NOTE: The plug-in won't properly detect Electric Imp project if it is not opened as described, ie. if it is opened
as a folder, not as a Text Sublime project!**

### Building and Running

To build and deploy the application code, please select the `Tools` > `Packages` > `Electric Imp` > `Build and Run`
menu item. This action uploads the agent and the device code to the server,
and restarts all of the devices assigned to the model.

When you build code (or perform any other action that requires access to the impCloud&trade;)
for the first time, you will be asked to provide:

- The path to the Node.js executable (if it is not automatically detected by the plug-in).
- The location of the Builder *cli.js* command line tool (if not automatically detected by the plug-in).
- User name and password, which you use for the [Electric Imp impCentral](https://impcentral.electricimp.com/)
- Create a new project or select an existing one
- Create a new device group or select an existing one
- You could be offered to download the latest deployment if you select an existing product and devicegroup

**NOTE**: To build and deploy your code for a newly created device group it isn’t necessary to select a device for your project. Even if you don’t have a device selected, you can still work on the code and see compilation errors reported by the server.

If you want to have you code running on a specific devices and view the logs from that devices, you need to select them using the `Tools` > `Packages` > `Electric Imp` > `Assign Device` menu item and 'Unassign Device' to remove all device which you are not interested in

### Project Management

Each Electric Imp project is associated with a particular device group, i.e. the device and agent code that define your
application. You can create a new project by selecting `Tools` > `Packages` > `Electric Imp` > `Create New Project`.


**Important** The code which is deployed to the device group is preprocessed and contains line control markers.
When you select an existing device group, the plug-in pulls down the code, but it doesn’t transfer the project
file/folder structure. So for collaborative work on the same project, please share the original Electric
Imp plug-in project sources/structure via a source control system.

### Logs Console

The Console can be popped up by selecting `Tools` > `Packages` > `Electric Imp` > `Show Console` menu item.
The Console shows live logs from the current device group if it is contain at least one device.

### Adding a Device to the DeviceGroup

To assign devices to the project's device group please go to
`Tools` > `Packages` > `Electric Imp` > `Assign Device` and select a device from the list.
The newly added device is automatically added to the console log stream.

### Removing a Device from the DeviceGroup

Devices can be removed from the project's device group by selecting `Tools` > `Packages` > `Electric Imp` > `Unassign Device`.

**NOTE**: log will be restarted on device unassign.

### Retrieving a Device’s Agent URL

The URL of a device’s agent can be retrieved by selecting the
`Tools` > `Packages` > `Electric Imp` > `Get Agent URL` menu item.
The URL is saved in the clipboard.

### Key Shortcuts

**Note** Electric Imp-specific menu items are only available if an Electric Imp project is opened in the currently active window.

| Command | Keypress |
| ------- | -------- |
| Create Project | Ctrl + Shift + Y |
| Build and Run | Ctrl + Shift + X |
| Show Logs Console | Ctrl + Shift + C |

## Preprocessor and Multi-File Support

Please refer to the [Builder documentation](https://github.com/electricimp/Builder)
for more information on the preprocessor syntax that you can use in your Squirrel code.

### Specifying GitHub Authentication Information

Please use the project *<Project Name>/settings/auth.info* file to specify your Builder
GitHub authentication information:

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

Please use the project *<Project Name>/settings/electric-imp.settings* file to specify the Builder variables definitions:

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

The Electric Imp Sublime Plug-in is licensed under the [MIT License](./LICENSE).
