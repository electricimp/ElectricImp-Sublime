Electric Imp Sublime Plugin
=================================

**Electric Imp Sublime Plugin supports [Sublime Text 3](https://www.sublimetext.com/3) only, no other versions are supported (tested on OS X).**

## Installation (manual)

1. Download or checkout the plugin package from https://github.com/ElectricImp-CSE/ElectricImp-Sublime

2. Install the plugin by manally copying the package content into
  - (OS X): /Users/&lt;username&gt;/Library/Application Support/Sublime Text 3/Packages/
  - (Windows): "%AppData%\Sublime Text 3\Packages\%"

## Usage

#### Project creation

First step is creation of a project by selecting Electric Imp->Create Project menu item. On the new project creation the user is asked to:

- [X] Specify the project folder
- [X] Enter the Build API Key
- [X] Select Model the project will be associated with from the popup list

As the result of these actions the project folder is created at the specified location:

```
-- <Project Name>
  |--> <Project Name>.sublime-project     (Sublime project file)
  |--> src                                (Source folder) 
  .   |--> <Model Name>.device.nut        (Device code)
  .   |--> <Model Name>.agent.nut         (Agent code)
  |--> settings                           (Electric Imp settings folder)
  .   |--> build-api.key                  (SENSITIVE: Build API key stored for the project
  .   |--> electric-imp.settings          (Generic Electric Imp settings)
  |--> .gitignore                         (.gitignore file to exclude Build API key from git repository)
```

**IMPORTANT: settings/build-api.key should not be put under a source control as it contains sensitive information!**

<Project Name>.electric-imp-settings file contains:

- The Build API key for the project
- Imp Model ID for the project
- Device and Agent code file names
- Selected device id

```
{
  "model-id"      : "my-model-id",
  "device-file"   : "mymodel.device.nut",
  "agent-file"    : "mymodel.agent.nut",
  "device-id"     : "my-selected-device-id"
}
```

On a new project creation the device and agent code (device.nut and agent.nut) is automatically downloaded for the specified Model and is stored in the appropriated files inside the project folder.

If a project is created successfully, a new window with the project folder is opened. 

**To start working with the Electric Imp project one should either click on the <Project Name>.sublime-project in the file browser (assuming the appropriate file association is set up in the system). You may also open the project by selecting Project->Open Project... menu option and choosing your <Project Name>.sublime-project file.**

The plugin doesn't identify the Electric Imp project if it's not properly opened as described.

#### Pushing the Code to the Server

The code can be pushed to the server by selecting Electric Imp->Deploy menu item. This action uploads the agent and the device code to the server and restarts the model. When pushing the code the user may be asked to select a device to view the logs for.

#### The Server Logs Console

The console can be popped up by selecting Electric Imp->Console menu item. It shows the live logs for the selected device.

#### Device Selection

Device can be selected through the Electric Imp->Select Device menu item. The selected device is used as a source of logs for the Server Logs Console.

#### Retrieving Agent URL

Agent URL can be retrieved by selecting Electric Imp->Get Agent URL menu item.

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