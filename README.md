Electric Imp impCentral Sublime Plug-in (Beta)
==================================

[Sublime Text 3](https://www.sublimetext.com/3) plug-in for [Electric Imp](https://electricimp.com) applications development.

- [Overview](#overview)
- [Installation](#installation)
    - [Install Node.js](#1-install-nodejs)
    - [Install the Builder Node.js Module](#2-install-the-builder-nodejs-module)
    - [Install Sublime Text](#3-install-sublime-text)
    - [Install the Electric Imp Sublime Plug-in](#4-install-the-electric-imp-sublime-plug-in)
- [Sublime Text Plug-in Usage](#sublime-text-plug-in-usage)
    - [Creating a New Project](#creating-a-new-project)
    - [Opening an Existing Project](#opening-an-existing-project)
    - [Building and Running](#building-and-running)
    - [Project Creation](#project-creation)
    - [Logs Console](#logs-console)
    - [Adding a Device to the Project Device Group](#adding-a-device-to-the-project-device-group)
    - [Removing a Device from the Project Device Group](#removing-a-device-from-the-project-device-group)
    - [Retrieving a Device’s Agent URL](#retrieving-a-devices-agent-url)
    - [Keyboard Shortcuts](#keyboard-shortcuts)
- [Preprocessor and Multi-File Support](#preprocessor-and-multi-file-support)
    - [Specifying GitHub Authentication Information](#specifying-github-authentication-information)
    - [Specifying Builder Preset Variable Definitions](#specifying-builder-preset-variable-definitions)

## Overview ##

The Plug-in is designed to improve developer productivity. It allows you to rapidly build and maintain applications by
providing:

* Code auto-completion for [Electric Imp’s imp API](https://developer.electricimp.com/api)
* The ability to use a source control system to manage application code and configuration
* Advanced Squirrel code highlighting
* Integration with [impWorks™ Builder](https://github.com/electricimp/Builder) to enable multi-file
projects and code pre-processing
* Live logs with clickable stack traces for errors, including navigation to the file and line in question
* Key shortcuts for frequent operations (build and run, show console, etc.)
* Leverages Sublime Text 3’s rich set of features.

The Plug-in requires connection to the Internet as it leverages the
[Electric Imp impCentral™ API](https://developer.electricimp.com/tools/impcentralapi)
to work with the [Electric Imp impCloud™](https://electricimp.com/platform/cloud/).

## Installation ##

**Note** The Electric Imp Sublime Plug-in supports [Sublime Text 3](https://www.sublimetext.com/3) only. No other versions are
supported. Tested on macOS only.

### 1. Install Node.js ###

**Note** The plug-in requires Node.js 4.0 or above.

Please follow [these instructions](https://nodejs.org/en/download/package-manager/) to install Node on your machine.

### 2. Install the Builder Node.js Module ###

The plug-in uses the [Builder](https://github.com/electricimp/Builder) Node.js module for source code pre-processing.
To install Builder, please use Node Package Manager (NPM):

```bash
npm i -g Builder
```

### 3. Install Sublime Text ###

Sublime Text 3 can be downloaded for a variety of platforms, [here](https://www.sublimetext.com/3).

### 4. Install the Electric Imp Sublime Plug-in ###

#### Using Package Control ####

If you already have [Package Control](http://wbond.net/sublime_packages/package_control/) installed in Sublime Text:

* Select `Install Package` from the Command Palette: <kbd>Ctrl+Shift+P</kbd> on Windows and Linux or <kbd>⌘⇧P</kbd> on macOS
* Search for **Electric Imp Developer** and click <kbd>Enter</kbd>
* Restart Sublime Text 3

#### Using the Sublime Text Terminal ####

You can install the plug-in with the following command in the Sublime Text terminal (``ctrl+` ``) which utilizes `git clone`.

**Note** Please make sure you have *git* installed on your system when trying this method.

```python
import os; path=sublime.packages_path(); ie_plugin_path=os.path.join(path, 'imp-developer'); (os.makedirs(path) if not os.path.exists(path) else None); window.run_command('exec', {'cmd': ['git', 'clone', 'https://github.com/electricimp/ElectricImp-Sublime.git', 'imp-developer'], 'working_dir': path}) if not os.path.exists(ie_plugin_path) else window.run_command('exec', {'cmd': ['git', 'pull'], 'working_dir': ie_plugin_path})
```

#### Manual Installation ####

Alternatively, follow these steps to install the plug-in manually:

1. Create the plug-in folder:
    - **macOS** */Users/&lt;username&gt;/Library/Application Support/Sublime Text 3/Packages/imp-developer*
    - **Windows** *"%AppData%\Sublime Text 3\Packages\imp-developer%"*

2. Do *one* of the following:
    - Download the full GitHub source [repository](https://github.com/electricimp/ElectricImp-Sublime) as a .zip file and extract its contents into the plug-in folder (*Sublime Text 3/Packages/imp-developer*) or
    - Clone the contents of the source repository [ElectricImp-Sublime](https://github.com/electricimp/ElectricImp-Sublime) into the plugin folder (*Sublime Text 3/Packages/imp-developer*)
    - Restart Sublime Text 3

## Sublime Text Plug-in Usage ##

### Creating a New Project ###

Your first step should be the creation of a new project. Do this by selecting the ‘Tools’ > ‘Packages’ > ‘Electric Imp’ > ‘Create Project’ menu item. You will then be asked to specify the project folder.

The project folder will be set up with the following:

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

**Important** `settings/auth.info` **should not be put under source control as it contains sensitive information**

The `electric-imp.settings` file contains:

- A unique project identifier.
- A unique Device Group identifier.
- The most recent deployment made by the plug-in.
- Device and agent code file names.
- [Builder](https://github.com/electricimp/builder) preprocessor configuration
- The impCentral API base URL (can be changed to work with private impClouds) 

#### Example ####

```
{ "product-id"    : "<product id>",
  "devicegroup-id": "<device group id>",
  "deployment-id" : "<deployment id>",
  "device-file"   : "<path to device source file, src/device.nut by default>",
  "agent-file"    : "<path to agent source file, src/agent.nut by default>",
  "cloud-url"     : "<impCentral base endpoint URL>",
  "builder-settings": { "variable-definitions": {<Builder variable definitions>}, 
                        "builder_cli_path": "<Path to the Builder's cli.js>", 
                        "node_path": "<path to Node.js (node) executable>" },  
}
```

When a project is created, empty device and agent code files (`device.nut` and `agent.nut`) are automatically created
and stored in the `<Project Name>/src` folder.

If a project is created successfully, a new window with the project folder is opened.

**Note** If you need to apply the Squirrel language syntax highlighting to files with extension other than `.nut`, please make sure you have ‘Squirrel (Electric Imp)’ language selected under the ‘View’ > ‘Syntax’ menu item.

### Opening an Existing Project ###

To open an existing Electric Imp project, select the ‘Project’ > ‘Open Project...’ menu option and choose the
`<Project Name>.sublime-project` file from your project folder.

**Note** The plug-in won’t properly detect an Electric Imp project if it is not opened as described, ie. if it is opened
as a folder (‘File’ > ‘Open...’), not as a Sublime Text project.

### Building and Running ###

To build and deploy code, please select the ‘Tools’ > ‘Packages’ > ‘Electric Imp’ > ‘Build and Run’
menu item. This action uploads the agent and the device code to the server, and restarts all of the devices assigned to the target Device Group.

When you first build code (or perform any other action that requires access to the impCloud), you will be asked to provide:

- The impCentral API base URL. The default value should be used, unless you are working with an Electric Imp Private impCloud.
- The path to the Node.js executable (if not automatically detected by the plug-in).
- The location of the Builder *cli.js* command line tool (if not automatically detected by the plug-in).
- Your Electric Imp account user name and password.
- Whether the tool should create a new project or open an existing one.
- A Product that belongs to another user who has granted your appropriate [collaborator roles](https://developer.electricimp.com/tools/impcentral/collaboratoractions).
- Whether the tool should create a new Device Group or select an existing one.
- You may also be offered the opportunity to download the latest deployment if you select an existing Product and Device Group.

If you want to have you code running on a specific devices and view the logs from that devices, you need 
to select them using the ‘Tools’ > ‘Packages’ > ‘Electric Imp’ > ‘Assign Device’ menu item. The ‘Unassign Device’ menu item removes a device from the project’s Device Group.

**Note** To build and deploy your code it isn’t necessary to assign a device to the Device Group. If you don’t have a device assigned, you can still work on the code and see compilation errors reported by the server.

### Project Creation ###

Each project is associated with an Electric Imp Product and a specific Device Group. You can create a new project by selecting ‘Tools’ > ‘Packages’ > ‘Electric Imp’ > ‘Create New Project’.

**Important** The code which is deployed to the Device Group is preprocessed and contains line control markers. When you select an existing Device Group, the plug-in pulls down the code, but it doesn’t transfer the project file/folder structure. So for collaborative work on the same project, please share the original Electric Imp plug-in project sources/structure via a source control system.

### Logs Console ###

The Console can be popped up by selecting ‘Tools’ > ‘Packages’ > ‘Electric Imp’ > ‘Show Console’ menu item. The Console shows live logs streamed from the current Device Group if the group contains at least one device.

### Adding a Device to the Project Device Group ###

To assign devices to the project’s Device Group, go to the ‘Tools’ > ‘Packages’ > ‘Electric Imp’ > ‘Assign Device’ menu item and select a device from the list. The newly added device is automatically attached to the console log stream.

### Removing a Device from the Project Device Group ###

Devices can be removed from the project’s Device Group by selecting the ‘Tools’ > ‘Packages’ > ‘Electric Imp’ > ‘Unassign Device’.

**Note** The log will be restarted when a device is unassigned.

### Retrieving a Device’s Agent URL ###

The URL of a device’s agent can be retrieved by selecting the ‘Tools’ > ‘Packages’ > ‘Electric Imp’ > ‘Get Agent URL’ menu item. The URL is saved to the clipboard.

### Keyboard Shortcuts ###

**Note** Electric Imp-specific menu items are only available if an Electric Imp project is opened in the currently active window.

| Command | Keypress |
| ------- | -------- |
| Create Project | Ctrl + Shift + Y |
| Build and Run | Ctrl + Shift + X |
| Show Logs Console | Ctrl + Shift + C |

## Preprocessor and Multi-File Support ##

Please refer to the [Builder documentation](https://developer.electricimp.com/tools/builder) for more information on the preprocessor syntax that you can use in your Squirrel code.

### Specifying GitHub Authentication Information ###

Please use the project `<Project Name>/settings/auth.info` file to specify your Builder GitHub authentication information:

```
{ ...
  "builder-settings": { "github-user": "GitHub user name",
                        "github-token": "Personal access token or password" }
}
```

### Specifying Builder Preset Variable Definitions ###

Please use the project `<Project Name>/settings/electric-imp.settings` file to specify the Builder variables definitions:

```
{ "builder-settings": { ...
                        "variable-definitions": { "key1": "value1",
                                                  "key2": "value2" },
                        ... }
}
```

## License ##

The Electric Imp Sublime Plug-in is licensed under the [MIT License](./LICENSE).
