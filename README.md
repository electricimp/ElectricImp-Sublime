Electric Imp Sublime Plug-in (Beta)
==================================

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


**The Electric Imp Sublime Plug-in supports [Sublime Text 3](https://www.sublimetext.com/3) only &mdash; no other versions are supported. Tested on macOS only.**

## Installation Steps

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

You can install the plug-in script with the following code in the Sublime Text terminal (``ctrl+` ``) 
which utilizes `git clone`. **Note** please make sure you have *git* installed on your system before trying this method.

```python
import os; path=sublime.packages_path(); (os.makedirs(path) if not os.path.exists(path) else None); window.run_command('exec', {'cmd': ['git', 'clone', 'https://github.com/electricimp/ElectricImp-Sublime.git', 'imp-developer'], 'working_dir': path}); window.run_command('exec', {'cmd': ['git', 'pull'], 'working_dir': os.path.join(path, "imp-developer")})
```

Alternatively, follow these steps to install the plug-in manually:

Download the full GitHub source repository or clone it from [https://github.com/electricimp/ElectricImp-Sublime](https://github.com/electricimp/ElectricImp-Sublime) into
    - macOS X: */Users/&lt;username&gt;/Library/Application Support/Sublime Text 3/Packages/*
    - Windows: *"%AppData%\Sublime Text 3\Packages\%"*

## Usage

### Creating a New Project

Your first step should be the creation of a new project. Do this by selecting the ‘Electric Imp’ > ‘Create Project’ menu item. You will then be asked to specify the project folder.

The  project folder will be set up with the following

```
-- <Project Name>
  |--> settings                           - Electric Imp settings folder
  .   |--> auth.info                      - SENSITIVE: Build API key and GitHub authentication information
  .   |--> electric-imp.settings          - Generic Electric Imp settings
  |--> src                                - Source folder 
  .   |--> <Model Name>.device.nut        - Device code
  .   |--> <Model Name>.agent.nut         - Agent code
  |--> .gitignore                         - .gitignore file to exclude Build API key from git repository
  |--> <Project Name>.sublime-project     - Sublime project file
```

**IMPORTANT** *settings/auth.info* **should not be put under a source control as it contains sensitive information!**

The *<Project Name>.electric-imp-settings* file contains:

- The model ID for the project
- Device and agent code file names
- Selected device ID

```
{
  "model-id"      : "my-model-id",
  "device-file"   : "device.nut",
  "agent-file"    : "agent.nut",
  "device-id"     : "my-selected-device-id"
}
```

When a project is created, empty device and agent code files (device.nut and agent.nut) are automatically created 
and stored in the *<Project Name>/src* folder.

If a project is created successfully, a new window with the project folder is opened. 

**Note** For the proper Squirrel language syntax highlighting, please make sure you have Squirrel (Electric Imp) 
languages selected under the ‘View’ > ‘Syntax’ menu item.

### Opening an Existing Project

To open an existing Electric Imp project, select the ‘Project’ > ‘Open Project...’ menu option and choose the 
*<Project Name>.sublime-project* file from your project folder.

**Note** The plug-in won’t properly detect Electric Imp project if it is not opened as described, ie. if it is opened
as a folder, not as a Text Sublime project.

### Building and Running

To build and deploy the application code, please select the ‘Electric Imp’ > ‘Build and Run’ menu item. This action uploads the agent and the device code to the server, and restarts all of the devices assigned to the model.

When you build code (or perform any other action that requires access to the impCloud&trade;) for the first time, you will be asked to provide:

- The path to the Node.js executable (if it is not automatically detected by the plug-in).
- The location of the Builder *cli.js* command line tool (if not automatically detected by the plug-in).
- Your Build API Key, which can be obtained at the [Electric Imp IDE](https://ide.electricimp.com/) by clicking on the ‘username’ > ‘Build API Keys’ menu item at the top right of the screen. 
- A model name. A model with this name will be created for the project, or if the name matches an existing model, that will be used instead.

**Note** To build and deploy your code it isn’t necessary to select a device for your project. Even if you don’t have a 
device selected, you can still work on the code and see compilation errors reported by the server.

If you want to have you code running on a specific device and view the logs from that device, you need to select a device using the ‘Electric Imp’ > ‘Model’ > ‘Device’ > ‘Select’ menu item.

### Model Management

Each Electric Imp project is associated with a particular model, ie. the device and agent code that define your application. You can create a new project model by selecting ‘Electric Imp’ > ‘Model’ > ‘Create’. 

You can also select an existing model and associate the project with it by using the ‘Electric Imp’ > ‘Model’ > ‘Select’ menu item.

**Important** The code which is deployed to the model is preprocessed and contains line control markers. When you select a model, the plug-in pulls down the model’s code, but it doesn’t transfer the project file/folder structure. So for collaborative work on the same project, please share the original Electric Imp plug-in project sources/structure 
via a source control.

### Logs Console

The Console can be popped up by selecting ‘Electric Imp’ > ‘Show Console’ menu item. The Console shows live logs
from the model and the selected device.

### Selecting a Device

Any device associated with the project model can be selected using the ‘Electric Imp’ > ‘Model’ > ‘Device’ > ‘Select’ menu item. The selected device will used as a source of logs for the Console.

### Adding a Device to the Model

You can add other devices enrolled into your account to the project model by selecting ‘Electric Imp’ > ‘Model’ > ‘Device’ > ‘Add’.The newly added device is automatically selected as the current one, which means the Console will show its logs.

### Removing a Device from the Model

Devices can be removed from the model by selecting ‘Electric Imp’ > ‘Model’ > ‘Device’ > ‘Remove’.

**Note** You can’t remove an active device (the one that is currently selected for logging).

### Retrieving a Device’s Agent URL

The URL of a device’s agent can be retrieved by selecting the ‘Electric Imp’ > ‘Get Agent URL’ menu item. The URL is saved in the clipboard.

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

Please use the project *<Project Name>/settings/auth.info* file to specify your Builder GitHub authentication information: 

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
        "variable-defines": {
            "key1": "value1", 
            "key2": "value2"
        },
        ...
    }
}
```

## Features Supported in the Current Version

- Push code to the server
- View live logs
- Copy the URL of the agent paired with the selected device
- An early version of the Squirrel language code highlighter (to be improved)
- An early version of API inline code suggestions (to be improved)
- [Builder](https://github.com/electricimp/Builder) preprocessor support

## Future Development Plans

- Improved compilation/runtime issues logs representation
- Improved highlighting and API suggestions
- Squirrel code linting and inline error highlighting
- Squirrel refactoring or advanced navigation features
