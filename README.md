# Electric Imp impCentral Sublime Plug-in #

- [Overview](#overview)
    - [Requirements](#requirements)
- [Installation](#installation)
    - [Install Node.js](#1-install-nodejs)
    - [Install The Builder Node.js Module](#2-install-the-builder-nodejs-module)
    - [Install Sublime Text](#3-install-sublime-text)
    - [Install The Sublime Text Plug-in](#4-install-the-sublime-text-plug-in)
- [Sublime Text Plug-in Usage](#sublime-text-plug-in-usage)
    - [Create A New Project](#create-a-new-project)
    - [Open An Existing Project](#open-an-existing-project)
    - [Build And Run](#build-and-run)
    - [The Log Console](#the-log-console)
    - [Add A Device To The Project Device Group](#add-a-device-to-the-project-device-group)
    - [Remove A Device From The Project Device Group](#remove-a-device-from-the-project-device-group)
    - [Retrieve An Agent URL](#retrieve-an-agent-url)
    - [Keyboard Shortcuts](#keyboard-shortcuts)
- [Pre-processor And Multiple File Support](#pre-processor-and-multiple-file-support)
    - [Specify GitHub Authentication Information](#specify-github-authentication-information)
    - [Specify Builder Preset Variable Definitions](#specify-builder-preset-variable-definitions)

## Overview ##

This [Sublime Text 3](https://www.sublimetext.com/3) Plug-in for [Electric Imp](https://electricimp.com) applications development is designed to improve developer productivity. It allows you to rapidly build and maintain applications by providing: 

* Code auto-completion for [Electric Imp’s imp API](https://developer.electricimp.com/api).
* The ability to use a source control system to manage application code and configuration.
* Advanced Squirrel code highlighting.
* Integration with [impWorks™ Builder](https://developer.electricimp.com/tools/builder) to enable multi-file projects and code pre-processing.
* Live logs with clickable stack traces for errors, including navigation to the file and line in question.
* Key shortcuts for frequent operations (build and run, show console, etc.).
* Leverages Sublime Text 3’s rich set of features.

### Requirements ###

For operation, the Extension requires a connection to the Internet. It also requires Node.js, impWorks Builder and Sublime Text 3.

**IMPORTANT** The Electric Imp Sublime Plug-in supports Sublime Text 3 **only**. No other versions are supported. Tested on macOS only.

## Installation ##

### 1. Install Node.js ###

**Note** The Plug-in requires Node.js 4.0 or above.

Please follow [these instructions](https://nodejs.org/en/download/package-manager/) to install Node on your machine.

### 2. Install The Builder Node.js Module ###

The Plug-in uses the [Builder](https://developer.electricimp.com/tools/builder) Node.js module for source code pre-processing. To install Builder, please use Node Package Manager (NPM):

```bash
npm i -g Builder
```

### 3. Install Sublime Text ###

Sublime Text 3 can be [downloaded for a variety of platforms here](https://www.sublimetext.com/3).

### 4. Install The Sublime Text Plug-in ###

#### Using Package Control ####

If you already have [Package Control](http://wbond.net/sublime_packages/package_control/) installed in Sublime Text:

* Select **Install Package** from the Command Palette: <kbd>Ctrl+Shift+P</kbd> on Windows and Linux, or <kbd>⌘⇧P</kbd> on macOS.
* Search using `"Electric Imp Developer"` and click <kbd>Enter</kbd>.
* Restart Sublime Text 3.

#### Using The Sublime Text Terminal ####

You can install the Plug-in with the following command in the Sublime Text terminal (<kbd>Ctrl+\`</kbd>) which utilizes `git clone`.

**Note** Please make sure you have *git* installed on your system before trying this method.

```python
import os; path=sublime.packages_path(); ie_plugin_path=os.path.join(path, 'imp-developer'); (os.makedirs(path) if not os.path.exists(path) else None); window.run_command('exec', {'cmd': ['git', 'clone', 'https://github.com/electricimp/ElectricImp-Sublime.git', 'imp-developer'], 'working_dir': path}) if not os.path.exists(ie_plugin_path) else window.run_command('exec', {'cmd': ['git', 'pull'], 'working_dir': ie_plugin_path})
```

#### Manual Installation ####

Alternatively, follow these steps to install the Plug-in manually:

1. Create the Plug-in folder:
    - **macOS** */Users/&lt;username&gt;/Library/Application Support/Sublime Text 3/Packages/imp-developer*
    - **Windows** *"%AppData%\Sublime Text 3\Packages\imp-developer%"*

2. Do *one* of the following:
    - Download the full GitHub source [repository](https://github.com/electricimp/ElectricImp-Sublime) as a .zip file and extract its contents into the Plug-in folder (*Sublime Text 3/Packages/imp-developer*) or
    - Clone the contents of the source repository [ElectricImp-Sublime](https://github.com/electricimp/ElectricImp-Sublime) into the Plug-in folder (*Sublime Text 3/Packages/imp-developer*)

3. Restart Sublime Text 3.

## Sublime Text Plug-in Usage ##

### Create A New Project ###

Your first step should be the creation of a new project. Do this by selecting the **Tools > Packages > Electric Imp > Create Project** menu item. You will then be asked to specify the project directory.

The project directory will be set up with the following:

```
-- <project directory>
  |----> settings                         - Plug-in settings directory
  .   |--> auth.info                      - SENSITIVE impCentral™ API tokens and 
  .   |                                     GitHub authentication information
  .   |--> electric-imp.settings          - Generic Electric Imp settings
  .
  |----> src                              - Source code directory
  .   |--> device.nut                     - Device code file
  .   |--> agent.nut                      - Agent code file
  .
  |----> .gitignore                       - .gitignore file to exclude auth.info file 
  |                                         from the git repository
  |----> electric-imp.sublime-project     - Sublime project file
```

**IMPORTANT** The `settings/auth.info` file should not be put under source control as it contains sensitive information. A `.gitignore` file is included automatically to prevent this.

The `electric-imp.settings` file contains:

- A unique project identifier.
- A unique Device Group identifier.
- The most recent deployment made by the Plug-in.
- Device and agent code file names.
- [Builder](https://developer.electricimp.com/tools/builder) settings.
- The impCentral API base URL (can be changed to work with private impClouds™) 

#### Example ####

```json
{ "product-id"      : "<product id>",
  "devicegroup-id"  : "<device group id>",
  "deployment-id"   : "<deployment id>",
  "device-file"     : "<path to device source file, src/device.nut by default>",
  "agent-file"      : "<path to agent source file, src/agent.nut by default>",
  "cloud-url"       : "<impCentral base endpoint URL>",
  "builder-settings": { "variable-definitions": {<Builder variable definitions>}, 
                        "builder_cli_path"    : "<Path to Builder's cli.js>", 
                        "node_path"           : "<path to Node.js executable>" }}
```

When a project is created, empty device and agent code files (`device.nut` and `agent.nut`, respectively) are automatically created and stored in the project directory’s `src` sub-directory.

If a project is created successfully, a new window with the project directory is opened.

#### Important Notes ####

- If you need to apply the Squirrel language syntax highlighting to files with an extension other than `.nut`, please make sure you have **Squirrel (Electric Imp)** language selected under **View > Syntax**.
- The code which is deployed to the Device Group is pre-processed and contains line control markers.
- When you select an existing Device Group, the Plug-in pulls down the code, but it doesn’t transfer the project file/folder structure. 
- If you are working with collaborators on a project, please share the original Electric Imp Plug-in project sources/structure via a source control system.

### Open an Existing Project ###

To open an existing Electric Imp project, select **Project > Open Project...** and choose the
`<project directory>.sublime-project` file from your project directory.

**Note** The Plug-in won’t detect an Electric Imp project if it is opened as a folder (**File > Open...**) rather than as a Sublime Text project.

### Build And Run ###

To build and deploy code, select **Tools > Packages > Electric Imp > Build and Run**. This action uploads the agent and the device code to the server, and restarts all of the devices assigned to the target Device Group.

When you first build code (or perform any other action that requires access to the impCloud), you will be asked to provide:

- The impCentral API base URL. The default value should be used, unless you are working with a Private impCloud.
- The path to the Node.js executable (if not automatically detected by the Plug-in).
- The location of the Builder *cli.js* command line tool (if not automatically detected by the Plug-in).
- Your Electric Imp account user name and password.
- A one-time password (OTP) if required by your account.
- An indication as to whether the tool should create a new project or open an existing one.
- A Product that belongs you to to another user who has granted your appropriate [collaborator roles](https://developer.electricimp.com/tools/impcentral/collaboratoractions).
- An indication as to whether the tool should create a new Device Group or select an existing one.

You may also be offered the opportunity to download the latest deployment if you select an existing Product and Device Group.

If you want to have you code running on a specific devices and view the logs from those devices, you need to select them using **Tools > Packages > Electric Imp > Assign Device**. The **Unassign Device** menu item removes a device from the project’s Device Group.

**Note** To build and deploy your code it isn’t necessary to assign a device to the Device Group. If you don’t have a device assigned, you can still work on the code and see compilation errors reported by the server.

### The Log Console ###

The Console can be popped up by selecting **Tools > Packages > Electric Imp > Show Console**. The Console shows live logs streamed from the current Device Group if the group contains at least one device.

### Add A Device To the Project Device Group ###

To assign devices to the project’s Device Group, go to **Tools > Packages > Electric Imp > Assign Device** menu item and select a device from the list. The newly added device is automatically attached to the Console log stream.

### Remove A Device From The Project Device Group ###

Devices can be removed from the project’s Device Group by selecting **Tools > Packages > Electric Imp > Unassign Device**.

**Note** The log will be restarted when a device is unassigned.

### Retrieve An Agent URL ###

The URL of a device’s agent can be retrieved by selecting **Tools > Packages > Electric Imp > Get Agent URL**. The URL is saved to the clipboard.

### Keyboard Shortcuts ###

**Note** Electric Imp-specific menu items are only available if an Electric Imp project is opened in the currently active window.

| Command | Shortcut |
| ------- | -------- |
| Create Project | Ctrl + Shift + Y |
| Build and Run | Ctrl + Shift + X |
| Show Logs Console | Ctrl + Shift + C |

## Pre-processor And Multiple File Support ##

Please refer to the [Builder documentation](https://developer.electricimp.com/tools/builder) for more information on the pre-processor syntax that you can use in your Squirrel code.

### Specify GitHub Authentication Information ###

Please use the `<project directory>/settings/auth.info` file to specify your Builder GitHub authentication information:

```json
{ ...
  "builder-settings": { "github-user" : "GitHub user name",
                        "github-token": "Personal access token or password" }}
```

### Specify Builder Preset Variable Definitions ###

Please use the `<project directory>/settings/electric-imp.settings` file to specify Builder variable definitions (as [described here](https://developer.electricimp.com/tools/builder#builder-expressions)):

```json
{ "builder-settings": { ...,
                        "variable-definitions": { "key1": "value1",
                                                  "key2": "value2" },
                        ... }}
```

## License ##

The Electric Imp Sublime Plug-in is licensed under the [MIT License](./LICENSE).
