# Copyright (c) 2016 Electric Imp
# This file is licensed under the MIT License
# http://opensource.org/licenses/MIT

# String resources exposed to the users
STR_SELECT_DEVICE                    = "Please select a device of the Model to connect to"
STR_CODE_IS_ABSENT                   = "Code files for agent or device are absent. Please check the project settings at {}"
STR_NEW_PROJECT_LOCATION             = "New Electric Imp Project Location:"
STR_NODE_JS_PATH                     = "Node.js Binary Path:"
STR_PROVIDE_NODE_JS_PATH             = "Please provide path to the Node.js executable binary"
STR_INVALID_NODE_JS_PATH             = "Node.js path is invalid. Please try one more time"
STR_BUILDER_CLI_PATH                 = "Builder cli.js file location:"
STR_PROVIDE_BUILDER_CLI_PATH         = "Please provide path to the Builder cli.js executable binary (it should be located at node_modules/Builder/src/cli.js)"
STR_INVALID_BUILDER_CLI_PATH         = "Can't find the Builder cli.js at the path specified. Please provide a proper path"
STR_FOLDER_EXISTS                    = "The folder {} already exists. Do you want to create project in this folder? Existing project files will be overwritten. Existing sources will be left untouched"
STR_BUILD_API_KEY                    = "Electric Imp Build API key:"
STR_INVALID_API_KEY                  = "Build API key is invalid. Please try another one"
STR_AGENT_URL_COPIED                 = "The agent URL for the selected device {} is:\n{}\nIt is copied into the clipboard"
STR_NO_DEVICES_AVAILABLE             = "There are no other Imp devices registered in the system. Please register a new device and try again"
STR_FAILED_TO_GET_LOGS               = "An error returned for logs request."
STR_PROVIDE_BUILD_API_KEY            = "Please provide your Electric Imp Build API key. It can be found in the Developer Console (login into your account and click on the top right link with you user name and select \"Build API Keys\")"

STR_INVALID_CREDENTIALS              = "Invalid user name or password. Try again ?"
STR_USER_ID                          = "Username"
STR_PASSWORD                         = "Password"
STR_PROVIDE_USER_ID                  = "Please signin to get an access to the ElectricImp environment"

STR_PRODUCT_PROVIDE_NAME             = "Please, provide a unique product name and description"
STR_PRODUCT_NAME                     = "Product name:"
STR_PRODUCT_SERVER_ERROR             = "Failed to extract product list"
STR_PRODUCT_CREATE_NEW               = "Create a new product ..."
STR_PRODUCT_PROVIDE_NAME             = "Please provide a new product name"

STR_DEVICEGROUP_CREATE_NEW           = "Create a new Device Group ..."
STR_DEVICEGROUP_CONDITIONAL_RESTART  = "Requested the conditional restart for the device group to apply the deployed source code"
STR_DEVICEGROUP_PROVIDE_NAME         = "Please provide a unique device group name"
STR_DEVICEGROUP_NAME                 = "Device group name:"
STR_DEVICEGROUP_CONFIRM_PULLING_CODE = "Do you want to pull the latest code revision from the DeviceGroup? Local source files will be overwritten with the remote ones and all the local changes will be lost!"

STR_MODEL_HAS_NO_DEVICES             = "The model has no devices yet. Please add an existing device to the model (Tools -> Packages -> Electric Imp -> Add Device)"
STR_MODEL_FAILED_TO_CREATE           = "Failed to create the model"

STR_MODEL_ADD_DEVICE                 = "Please select a device to add to the model"
STR_MODEL_ADDING_DEVICE_FAILED       = "Adding device to the model failed"

STR_MODEL_IMP_REGISTERED             = "The Imp device is added to the Model and selected as active"
STR_MODEL_REMOVE_DEVICE              = "Select a device to remove from the Model"
STR_MODEL_NO_DEVICES_TO_REMOVE       = "The Model has no devices to remove"
STR_MODEL_CANT_REMOVE_ACTIVE_DEVICE  = "This device is currently selected as active. Can't remove it from the Model"
STR_MODEL_REMOVE_DEVICE_FAILED       = "Failed removing device from the Model"
STR_MODEL_DEVICE_REMOVED             = "The device is successfully removed from the Model"
STR_MODEL_NOT_ASSIGNED               = "The project doesn't have a model assigned. Please select or create one (Tools -> Packages -> Electric Imp -> Create/Select Model)."
STR_MODEL_NO_MODELS_FOUND            = "No models available on the account. Please create one (Tools -> Packages -> Electric Imp -> Create Model)"
STR_MODEL_SELECT_EXISTING_MODEL      = "Select existing Model"

STR_ERR_MESSAGE_LINE                 = "    ERROR: [CLICKABLE] {} ({}:{})\n"
STR_ERR_DEPLOY_FAILED_WITH_ERRORS    = "\nDeploy failed because of the following errors:\n"
STR_ERR_RUNTIME_ERROR                = "ERROR:   [CLICKABLE] at {} ({}:{})"
STR_ERR_CONSOLE_NOT_FOUND            = "Couldn't find console to print: {}"
STR_ERR_PREPROCESSING_ERROR          = "\nPreprocessing failed because of the following errors:\n    ERROR: [CLICKABLE] {}\n"

STR_STATUS_REVISION_UPLOADED         = "Revision uploaded: {}"
STR_STATUS_CREATING_PROJECT          = "Creating project at {}"
STR_STATUS_ACTIVE_PRODUCT            = "Product: {}"
STR_STATUS_ACTION                    = "Command: {}"

STR_INITIAL_SRC_CONTENT              = "// {} source code goes here\n\n"
