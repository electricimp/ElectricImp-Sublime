# Copyright (c) 2016-2018 Electric Imp
# This file is licensed under the MIT License
# http://opensource.org/licenses/MIT

# String resources exposed to the users
STR_SELECT_DEVICE                       = "Please select a device"
STR_CODE_IS_ABSENT                      = "Cannot find source code files for the agent or the device. Please check the project settings at {}"
STR_NEW_PROJECT_LOCATION                = "New project location: "
STR_NODE_JS_PATH                        = "Node.js path: "
STR_PROVIDE_NODE_JS_PATH                = "Please provide the path to Node.js"
STR_INVALID_NODE_JS_PATH                = "Node.js can't be found at the path you entered. Please enter it again"
STR_BUILDER_CLI_PATH                    = "Builder cli.js file location: "
STR_PROVIDE_BUILDER_CLI_PATH            = "Please provide the path to the Builder cli.js file (it should be located at node_modules/Builder/src/cli.js)"
STR_INVALID_BUILDER_CLI_PATH            = "The Builder cli.js file can't be found at the path you entered. Please enter it again"
STR_FOLDER_EXISTS                       = "The folder {} already exists. Do you want to create a project in this folder? Existing project files will be overwritten, but existing source files will be left untouched"
STR_BUILD_API_KEY                       = "Electric Imp Build API key: "
STR_INVALID_API_KEY                     = "The Build API key you entered is invalid. Please enter it again"
STR_AGENT_URL_COPIED                    = "The agent URL for device ID {} has been copied to the clipboard:\n\n{}"
STR_FAILED_TO_GET_LOGS                  = "An error returned for logs request"

STR_INVALID_CREDENTIALS                 = "Your entered an invalid username and/or password. Please enter them again"
STR_USER_ID                             = "Username or email: "
STR_PASSWORD                            = "Password: "
STR_PROVIDE_USER_ID                     = "Please sign in to access the Electric Imp impCloud"
STR_PROVIDE_OTP                         = "One-time password (OTP): "

STR_PRODUCT_NAME                        = "Product name: "
STR_PRODUCT_SERVER_ERROR                = "Failed to get a list of Products"
STR_PRODUCT_CREATE_NEW                  = "> Create a new Product..."
STR_PRODUCT_PROVIDE_NAME                = "Please provide a new Product name"
STR_PRODUCT_DESCRIPTION                 = "Product created by the impWorks Sublime Text plugin"

STR_DEVICE_GROUP_NAME                   = "Device Group name: "
STR_DEVICE_GROUP_CREATE_NEW             = "Create a new Device Group..."
STR_DEVICE_GROUP_CONDITIONAL_RESTART    = "Requested the conditional restart of the Device Group to apply the deployed source code"
STR_DEVICE_GROUP_PROVIDE_NAME           = "Please provide a new Device Group name"
STR_DEVICE_GROUP_CONFIRM_PULLING_CODE   = "Do you want to download the latest code revision from the Device Group? Local source files will be overwritten and all local changes will be lost"
STR_DEVICE_GROUP_DESCRIPTION            = "Device Group created by the impWorks Sublime Text plugin"

STR_DEPLOYMENT_DESCRIPTION              = "Code uploaded by the impWorks Sublime Text plugin"

STR_REPLACE_CONFIG                      = """This plugin no longer supports the Build API.\n\n
Would you like to update your configuration to use the impCentral API?\n\n
Note: the old configuration will be replaced with a new one."""

STR_ERR_MESSAGE_LINE                    = "    ERROR: [CLICKABLE] {} ({}:{})\n"
STR_ERR_RUNTIME_ERROR                   = "ERROR: [CLICKABLE] at {} ({}:{})"
STR_ERR_CONSOLE_NOT_FOUND               = "Couldn't find the console to print: {}"
STR_ERR_PREPROCESSING_ERROR             = "Preprocessing failed because of the following errors:\n    ERROR: [CLICKABLE] {}\n"
STR_ERR_DEPLOY_FAILED_WITH_ERRORS       = "Failed to deploy code because of the following errors:\n"
STR_FAILED_CODE_DEPLOY                  = "Failed to deploy code because of the following error: {}"

STR_STATUS_REVISION_UPLOADED            = "Revision uploaded: {}"
STR_STATUS_CREATING_PROJECT             = "Creating project at {}"
STR_STATUS_ACTIVE_PRODUCT               = "Product: {}"
STR_STATUS_ACTION                       = "Command: {}"

STR_INITIAL_SRC_CONTENT                 = "// {} source code goes here\n\n"

STR_FAILED_TO_LOGIN                     = "Failed to login: "
STR_INVALID_USER_OR_PASSWORD            = "Your entered an invalid username and/or password. Please enter them again"

STR_FAILED_TO_CREATE_PRODUCT            = "Failed to create Product: "
STR_RETRY_CREATE_PRODUCT                = "Try to create the Product again?"

STR_FAILED_TO_GET_ACCOUNT_DETAILS       = "Failed to get account details: "
STR_FAILED_TO_GET_PRODUCTS              = "Failed to get the list of Products: "
STR_RETRY_SELECT_PRODUCT                = "Try to get the list of Products again?"

STR_FAILED_TO_GET_DEVICE_GROUPS         = "Failed to get the list of Device Groups: "
STR_RETRY_TO_GET_DEVICE_GROUPS          = "Try to get the list of Device Groups again?"

STR_FAILED_TO_GET_DEVICE_GROUP          = "Failed to create Device Group: "
STR_RETRY_TO_GET_DEVICE_GROUP           = "Your entered an invalid Device Group ID. Please enter it again"

STR_FAILED_TO_ASSIGN_DEVICE             = "Failed to assign device: "
STR_FAILED_TO_GET_DEVICELIST            = "Failed to get the list of devices: "

STR_FAILED_TO_REMOVE_DEVICE             = "Failed to remove the device from the Device Group: "
STR_RETRY_TO_REMOVE_DEVICE              = "Try to remove the device from the Device Group again?"

STR_FAILED_CONDITIONAL_RESTART          = "Failed to perform the conditional restart"
STR_FAILED_TO_GET_DEVICE_AGENT_URL      = "Failed to get the device's agent URL"

STR_FAILED_TO_EXTRACT_CODE              = "Failed to download the source code"
STR_RETRY_TO_EXTRACT_CODE               = "Try to download the source code again?"

STR_FAILED_TO_GET_DEPLOYMENT            = "Failed to download the latest deployment: "

STR_FAILED_TOO_SHORT_CONTENT            = "That field cannot be empty"
STR_FAILED_RESOURCE_NOT_AVAILABLE       = "There is no Internet connection, or the requested resource is not available."

STR_UNHANDLED_HTTP_ERROR                = "Unhandled HTTP error: {}"
STR_TRY_AGAIN                           = "Try again"

STR_PROVIDE_IMPCENTRAL_API_URL          = "Please enter the impCentral API URL.\nNote: always use the default, unless you use an Electric Imp Private impCloud"
STR_IMPCENTRAL_API_URL                  = "Electric Imp impCentral API URL: "
STR_PLEASE_CHECK_URL                    = "Failed to access the {} API. Please check the impCentral API URL"

STR_MESSAGE_ASSIGN_DEVICE               = "There are no devices in the current Device Group. Please assign a device to start logging"
STR_MESSAGE_DEVICE_LIST_EMPTY           = "The account has no devices. Please register a device first"
STR_MESSAGE_DEPLOYMENT_EMPTY            = "No code has been deployed to the current Device Group"
STR_MESSAGE_LOG_STREAM_REQUESTED        = "Log stream start requested"
STR_MESSAGE_LOG_STREAM_RESTART          = "Real-time logging restart requested"
STR_MESSAGE_LOG_STREAM_STARTED          = "Logstream started"
STR_MESSAGE_LOG_STREAM_STOPPED          = "Real-time logging has stopped. Please refresh to re-enable logging"
STR_MESSAGE_LOG_STREAM_NOT_STARTED      = "Real-time logging not started. Please refresh to enable logging"
STR_MESSAGE_NO_DEVICE_IN_DEVICE_GROUP   = "There are no devices in the current Device Group"

STR_FAILED_TO_EXTRACT_COLLABORATORS     = "Failed to get the list of collaborators"
STR_FAILED_TO_EXTRACT_GRANTS            = "Failed to get the account permissions for collaborator \"{}\""
STR_SELECT_COLLABORATOR                 = "> Choose a collaborator's project"
STR_DEVICE_MOVING_FROM_CONFIRMATION     = "Do you really want to move the device from Product \"{}\" and Device Group \"{}\"?"
STR_DEVICE_SUCCESSFULLY_ASSIGNED        = "The device was successfully assigned"
STR_DEVICE_SUCCESSFULLY_UNASSIGNED      = "The device was successfully unassigned"
