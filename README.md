ImpDeveloper Sublime plugin v0.1
=================================

## Installation (manual)

1. Download the plugin package from our internal web site <LINK>

2. User installs the plugin by manally copying the package into the /Users/<username>/Library/Application Support/Sublime Text 3/Packages/ folder.

## Usage

First step is creation of a project by selecting ElectricImp->Create Project menu item.

User is asked to:

	- Specify the project location
	- Enter the Build API Key
	- Select device model the project is associated with from the popup list (requested by the plugin from the server).

As the result of this action:

	a) The project folder with a sublime project file are created at the specified location

		-- ImpProjectName
		  |-> model.device.nut                      (device code)
		  |-> model.agent.nut                       (agent code)
		  |-> ImpProjectName.electric-imp-settings  (electric imp specific settings)
		  |-> ImpProjectName.sublime-project        (sublime project file)

	b) The ElectricImp project file is created, that is used to store store:
		BuildAPIKey, Model name/id, device/agent file names, project specific settings (debug logging enabled, etc)

		ImpProjectName.electric-imp-settings: 

		{
			"build-api-key" : "09fc8b113fdscadcdff868daacf875017",
			"model-id"      : "UwIoEuX9to8Q",
			"model-name"    : "MyModel",
			"device-file"   : "mymodel.device.nut",
			"agent-file"    : "mymodel.agent.nut",
			"debug"         : true
		}

	c) The project is set up:

		- The server versions of device.nut and agent.nut are automatically downloaded to the project folder
		- Both files are opened in the Sublime editor
		- The side bar shows the project folder to nativate through

## Feature available in v0.1

	- A draft highligher for Squirrel language (based on JS, may not be accurate) is available
	- The project can be deployed to the server by selecting Electric Imp->Deploy (Ctrl+Shift+D) menu item
	- IDE logs are shown in the Console

## Restrictions in version v0.1

	- No inline code compilation errors or code lintering is provided
	- No multifile support
	- No refactoring or sophistiated navigation features (except those available in the editor out of the box)
	- No way to change a model for the project

## Next steps:

	- Address the feedback from the team
	- Multiple files support (preprocessor)
	- Refactoring or sophistiated navigation features