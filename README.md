Electric Imp Sublime Plugin v0.1
=================================

**Electric Imp Sublime Plugin v0.1 supports [Sublime Text 3](https://www.sublimetext.com/3) only, no other versions are supported!**

## Installation (manual)

1. Download or checkout the plugin package from https://github.com/ElectricImp-CSE/ElectricImp-Sublime

2. Install the plugin by manally copying the package content into
  - (OS X): /Users/<username>/Library/Application Support/Sublime Text 3/Packages/
  - (Windows): "%AppData%\Sublime Text 3\Packages\% 

## Usage

#### Project creation

First step is creation of a project by selecting Electric Imp->Create Project menu item. On the new project creation the user is asked to:

- [X] Specify the project folder
- [X] Enter the Build API Key
- [X] Select Model the project will be associated with from the popup list

As the result of these actions the project folder is created at the specified location:

```
-- <Project Name>
  |-> <Project Name>.sublime-project        (Sublime project file)
  |-> <Project Name>.electric-imp-settings  (Electric Imp project specific settings)
  |-> <Model Name>.device.nut               (Device code)
  |-> <Model Name>.agent.nut                (Agent code)
 ```

<Project Name>.electric-imp-settings file contains:

- The Build API key for the project
- Imp Model ID for the project
- Device and Agent code file names 

```
{
	"build-api-key" : "09fc8b113fdscadcdff868daacf875017",
	"model-id"      : "UwIoEuX9to8Q",
	"device-file"   : "mymodel.device.nut",
	"agent-file"    : "mymodel.agent.nut"
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

### Key Shortcuts

**Electric Imp specific menu items are only available if an Electric Imp project is opened in the currently active window**

- Create Project: Ctrl + Shift + L
- Deploy project: Ctrl + Shift + D
- Show Logs Console: Ctrl + Shift + C
- Select Device: Ctrc + Shift + I


## Feature available in v0.1

- Push of the code to the server
- Live logs view
- An early version of the Squirrel language code highlighter (Alpha version, may not be accurate)
- An early version of the API inline code suggestions (Alpha version, may not be accurate)

## Restrictions in version v0.1

- No inline code compilation errors or code lintering is provided
- No multiple file support
- No refactoring or sophistiated navigation features (except those available in the editor out of the box)
- No way to change a model for the project

## Future Development Plans

- Multiple files support
- Squirrel code lintering and inline error highlighting
- Advanced Squirrel preprocessor support
- Refactoring or advanced navigation features
- Simple administrative functionality (managing Models, devices, migration of devices, etc.)