# Copyright (c) 2016 Electric Imp
# This file is licensed under the MIT License
# http://opensource.org/licenses/MIT

# String resources exposed to the users
STR_SELECT_DEVICE                    = "Please select a device to assign to"
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
STR_AGENT_URL_COPIED                 = "The agent URL is copied into the clipboard:\n\n Device :  {}\n\n Url :  {}"
STR_NO_DEVICES_AVAILABLE             = "There are no other Imp devices registered in the system. Please register a new device and try again"
STR_FAILED_TO_GET_LOGS               = "An error returned for logs request."
STR_PROVIDE_BUILD_API_KEY            = "Please provide your Electric Imp Build API key. It can be found in the Developer Console (login into your account and click on the top right link with you user name and select \"Build API Keys\")"

STR_INVALID_CREDENTIALS              = "Invalid user name or password. Try again ?"
STR_USER_ID                          = "Username"
STR_PASSWORD                         = "Password"
STR_PROVIDE_USER_ID                  = "Please sign-in to get an access to the ElectricImp environment"

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

STR_FAILED_TO_LOGIN                    = "Failed to login: "
STR_INVALID_USER_OR_PASSWORD         = "Invalid user-name or password. Try again?"

STR_FAILED_TO_CREATE_PRODUCT         = "Failed to create new product: "
STR_RETRY_CREATE_PRODUCT             = "Try to create product again ?"

STR_FAILED_TO_GET_ACCOUNT_DETAILS    = "Failed to get account details: "
STR_FAILED_TO_GET_PRODUCTS           = "Failed to get the list of products: "
STR_RETRY_SELECT_PRODUCT             = "Try to load list of products again?"

STR_FAILED_TO_GET_DEVICEGROUPS       = "Failed to extract the device group list: "
STR_RETRY_TO_GET_DEVICEGROUPS        = "Something wend wrong, retry to extract the list of devicegroups ?"

STR_FAILED_TO_GET_DEVICEGROUP        = "Failed to create device group: "
STR_RETRY_TO_GET_DEVICEGROUP         = "Wrong device group id. Type again ?"

STR_FAILED_TO_ASSIGN_DEVICE          = "Failed to assign device: "
STR_FAILED_TO_GET_DEVICELIST         = "Failed to extract list of devices: "

STR_FAILED_TO_REMOVE_DEVICE          = "Failed to remove device from the group: "
STR_RETRY_TO_REMOVE_DEVICE           = "Something went wrong with device unassing from the device group.\n\n Try again ?"

STR_FAILED_CONDITIONAL_RESTART       = "Failed to perform the conditional restart"
STR_FAILED_TO_GET_DEVICE_AGENT_URL   = "Failed to get agent url for some device"

STR_FAILED_TO_EXTRACT_CODE           = "Failed to extract source code"
STR_RETRY_TO_EXTRACT_CODE            = "Try to download code again ?"

STR_FAILED_TO_GET_DEPLOYMENT         = "Failed to load the latest deployment: "
