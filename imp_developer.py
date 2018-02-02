# MIT License
#
# Copyright 2016-2017 Electric Imp
#
# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
# EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
# OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import base64
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import urllib.parse
import urllib.error
import socket
import select

import sublime
import sublime_plugin

# Import string resources
from .plugin_resources.strings import *
from .plugin_resources.node_locator import NodeLocator

# Import third party modules
from .modules.Sublime_AdvancedNewFile_1_0_0.advanced_new_file.commands import AdvancedNewFileNew

# Generic plugin constants
PL_IMPCENTRAL_API_URL_BASE = "https://api.electricimp.com"
PL_IMPCENTRAL_API_URL_V5 = PL_IMPCENTRAL_API_URL_BASE + "/v5/"
PL_SETTINGS_FILE         = "ImpDeveloper.sublime-settings"
PL_DEBUG_FLAG            = "debug"
PL_AGENT_URL             = "https://agent.electricimp.com/{}"
PL_WIN_PROGRAMS_DIR_32   = "C:\\Program Files (x86)\\"
PL_WIN_PROGRAMS_DIR_64   = "C:\\Program Files\\"
PL_ERROR_REGION_KEY      = "electric-imp-error-region-key"
PL_ACTION_STATUS_KEY     = "action-status-key"
PL_PRODUCT_STATUS_KEY    = "product-status-key"
PL_PLUGIN_STATUS_KEY     = "plugin-status-key"
PL_KEEP_ALIVE_TIMEOUT    = 35 # api timeout is 30 seconds
PL_LONG_POLL_TIMEOUT     = 5 # sec
PL_LOGS_UPDATE_LONG_PERIOD = 1000 # ms
PL_LOGS_UPDATE_SHORT_PERIOD = 300 # ms
PL_LOGS_MAX_PER_REQUEST  = 30

# Electric Imp project specific constants
PR_DEFAULT_PROJECT_NAME  = "electric-imp-project"
PR_TEMPLATE_DIR_NAME     = "project-template"
PR_PROJECT_FILE_TEMPLATE = "electric-imp.sublime-project"
PR_WS_FILE_TEMPLATE      = "electric-imp.sublime-workspace"
PR_SETTINGS_FILE         = "electric-imp.settings"
PR_AUTH_INFO_FILE        = "auth.info"
PR_SOURCE_DIRECTORY      = "src"
PR_SETTINGS_DIRECTORY    = "settings"
PR_BUILD_DIRECTORY       = "build"
PR_DEVICE_FILE_NAME      = "device.nut"
PR_AGENT_FILE_NAME       = "agent.nut"
PR_PREPROCESSED_PREFIX   = "preprocessed."

# Electric Imp settings and project properties
EI_LOGIN_KEY             = "login-key"
EI_ACCESS_TOKEN_SET      = "access-token-set"
EI_ACCESS_TOKEN          = "access_token"
EI_REFRESH_TOKEN         = "refresh_token"
EI_EXPIRES_AT            = "expires_at"
EI_PRODUCT_ID            = "product-id"
EI_DEVICEGROUP_ID        = "device-group-id"
EI_DEPLOYMENT_ID         = "deployment-id"

EI_DEPLOYMENT_NEW        = "deployment-new"

EI_DEVICE_FILE           = "device-file"
EI_AGENT_FILE            = "agent-file"

EI_DEVICE_ID             = "device-id"
EI_BUILDER_SETTINGS      = "builder-settings"
EI_ST_PR_NODE_PATH       = "node_path"
EI_ST_PR_BUILDER_CLI     = "builder_cli_path"
EI_GITHUB_USER           = "github-user"
EI_GITHUB_TOKEN          = "github-token"
EI_VARIABLE_DEFINES      = "variable-definitions"

# Global variables
plugin_settings = None
project_env_map = {}


class ProjectManager:
    """Electric Imp project specific fuctionality"""

    def __init__(self, window):
        self.window = window

    @staticmethod
    def get_settings_dir(window):
        project_file_name = window.project_file_name()
        if project_file_name:
            project_dir = os.path.dirname(project_file_name)
            return os.path.join(project_dir, PR_SETTINGS_DIRECTORY)

    @staticmethod
    def dump_map_to_json_file(filename, map):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(map, f, indent=4)

    @staticmethod
    def get_settings_file_path(window, filename):
        settings_dir = ProjectManager.get_settings_dir(window)
        if settings_dir and filename:
            return os.path.join(settings_dir, filename)

    @staticmethod
    def is_electric_imp_project_window(window):
        settings_filename = ProjectManager.get_settings_file_path(window, PR_SETTINGS_FILE)
        return settings_filename is not None and os.path.exists(settings_filename)

    def save_settings(self, filename, settings):
        self.dump_map_to_json_file(ProjectManager.get_settings_file_path(self.window, filename), settings)

    def load_settings_file(self, filename):
        path = ProjectManager.get_settings_file_path(self.window, filename)
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)

    def load_settings(self):
        return self.load_settings_file(PR_SETTINGS_FILE)

    def load_auth_settings(self):
        return self.load_settings_file(PR_AUTH_INFO_FILE)

    def get_access_token_set(self):
        auth_info = self.load_auth_settings()
        if auth_info:
            return auth_info.get(EI_ACCESS_TOKEN_SET)

    def get_access_token(self):
        auth_info = self.load_auth_settings()
        if auth_info:
            token = auth_info.get(EI_ACCESS_TOKEN_SET)
            if token and EI_ACCESS_TOKEN in token:
                return token[EI_ACCESS_TOKEN]

        return None

    def get_refresh_token(self):
        auth_info = self.load_auth_settings();
        if auth_info:
            token = auth_info.get(EI_ACCESS_TOKEN_SET)
            if token and EI_REFRESH_TOKEN in token:
                return token[EI_REFRESH_TOKEN]

        return None

    def get_github_auth_info(self):
        auth_info = self.load_settings_file(PR_SETTINGS_FILE)
        if auth_info and EI_BUILDER_SETTINGS in auth_info:
            builder_settings = auth_info[EI_BUILDER_SETTINGS]
            if builder_settings and EI_GITHUB_USER in builder_settings and EI_GITHUB_TOKEN in builder_settings:
                return builder_settings[EI_GITHUB_USER], builder_settings[EI_GITHUB_TOKEN]

        return None, None

    def get_project_directory_path(self):
        return os.path.dirname(self.window.project_file_name())

    def get_source_directory_path(self):
        return os.path.join(os.path.dirname(self.window.project_file_name()), PR_SOURCE_DIRECTORY)

    def get_build_directory_path(self):
        return os.path.join(os.path.dirname(self.window.project_file_name()), PR_BUILD_DIRECTORY)


class Env:
    """Window (project) specific environment object"""

    def __init__(self, window):
        # Link back to the window
        self.window = window

        # Plugin text area
        self.terminal = None

        # UI Manager
        self.ui_manager = UIManager(window)
        # Electric Imp Project manager
        self.project_manager = ProjectManager(window)
        # Preprocessor
        self.code_processor = Preprocessor()
        # Log Manager
        self.log_manager = LogManager(self)

        # Temp variables
        self.tmp_device_ids = None

    @staticmethod
    def For(window):
        global project_env_map
        return project_env_map.get(window.project_file_name())

    @staticmethod
    def get_existing_or_create_env_for(window):
        global project_env_map

        env = Env.For(window)
        if not env:
            env = Env(window)
            project_env_map[window.project_file_name()] = env
            log_debug(
                "  [ ] Adding new project window: " + str(window) +
                ", total windows now: " + str(len(project_env_map)))
        return env


class UIManager:
    """Electric Imp plugin UI manager"""

    STATUS_UPDATE_PERIOD_MS = 500
    __status_counter = 0

    def __init__(self, window):
        self.keep_updating_status = False
        self.window = window

    def create_new_console(self):
        env = Env.For(self.window)
        env.terminal = self.window.get_output_panel("textarea")

        env.log_manager.poll_url = None
        env.log_manager.last_shown_log = None

    def write_to_console(self, text):
        env = Env.For(self.window)
        terminal = env.terminal if hasattr(env, "terminal") else None
        if terminal:
            terminal.set_read_only(False)
            terminal.run_command("append", {"characters": text + "\n"})
            terminal.set_read_only(True)

    def init_tty(self):
        env = Env.For(self.window)
        if not env.terminal:
            self.create_new_console()
        self.show_console()

    def show_console(self):
        self.window.run_command("show_panel", {"panel": "output.textarea"})

    def show_path_selector(self, caption, default_path, on_path_selected):
        # TODO: Implement path selection autocomplete (CSE-70)
        self.window.show_input_panel(caption, default_path, on_path_selected, None, None)

    def set_status_message(self, key, message):
        views = self.window.views()
        for v in views:
            v.set_status(key=key, value=message)

    def erase_status_message(self, key):
        views = self.window.views()
        for v in views:
            v.erase_status(key)

    def show_action_value_in_status(self, status, action_name, formatted_string):
        env = Env.For(self.window)
        if action_name:
            env.ui_manager.set_status_message(
                status, formatted_string.format(action_name))
        else:
            env.ui_manager.erase_status_message(status)

    def show_settings_value_in_status(self, property_name, status_key, formatted_string):
        env = Env.For(self.window)
        settings = env.project_manager.load_settings()
        if settings and property_name in settings:
            property_value = settings.get(property_name)
            if property_value:
                log_debug("Setting status for property \"" + property_name + "\" value: " + property_value)
                env.ui_manager.set_status_message(status_key, formatted_string.format(property_value))
            else:
                log_debug("Property \"" + property_name + "\" has no value")
        else:
            log_debug("Property \"" + property_name + "\" is not found in the settings")

class HttpHeaders():
    DEFAULT = {
        "Content-Type": "application/vnd.api+json",
        "User-Agent" : "imp-developer/sublime"
    }
    STREAM = {
        "Content-Type": "text/event-stream",
        "User-Agent" : "imp-developer/sublime"
    }
    AUTH = {
        "Content-Type": "application/json",
        "User-Agent" : "imp-developer/sublime"
    }


class HTTP:
    """Implementation of all the Electric Imp connection functionality"""

    @staticmethod
    def __base64_encode(str):
        return base64.b64encode(str.encode()).decode()

    @staticmethod
    def get_http_headers(key, headers):
        if not headers:
            headers = {}
        if key:
            headers["Authorization"] = "Bearer " + key

        return headers

    @staticmethod
    def is_refresh_token_valid(token):
        if datetime.datetime.strptime(token.get(EI_EXPIRES_AT), "%Y-%m-%dT%H:%M:%S.%fZ") > datetime.now():
            return True
        request, code = HTTP.post({token:token.value}, PL_IMPCENTRAL_API_URL_V5 + "/auth/token")
        return code == 200


    @staticmethod
    def do_request(key, url, method, data=None, timeout=None, headers=None):
        if data:
            data = data.encode('utf-8')
        req = urllib.request.Request(url,
                                     headers=HTTP.get_http_headers(key, headers),
                                     data=data,
                                     method=method)

        result, code = None, None
        try:
            res = urllib.request.urlopen(req, timeout=None)
            code = res.getcode()
            pl = res.read().decode('utf-8')
            if pl:
                result = json.loads(pl)
        except socket.timeout:
            log_debug("Timeout error occurred for URL: " + url)
            result = code
        except urllib.error.HTTPError as err:
            code = err.code
            result = json.loads(err.read().decode('utf-8'))
        except urllib.error.URLError as err:
            code = 404
            result = {"error" : err.reason}
        except urllib.error.ContentTooShortError as err:
            code = 404
            result = {"error" : "Too short conent exception"}

        return result, code

    @staticmethod
    def get(key, url, timeout=None, data=None, headers=HttpHeaders.DEFAULT):
        return HTTP.do_request(key, url, "GET", timeout=timeout, data=data, headers=headers)

    @staticmethod
    def post(key, url, data=None, headers=HttpHeaders.DEFAULT):
        return HTTP.do_request(key, url, "POST", data, headers=headers)

    @staticmethod
    def put(key, url, data=None, headers=HttpHeaders.DEFAULT):
        return HTTP.do_request(key, url, "PUT", data, headers=headers)

    @staticmethod
    def delete(key, url, data=None, headers=HttpHeaders.DEFAULT):
        return HTTP.do_request(key, url, "DELETE", data, headers=headers)

    @staticmethod
    def is_response_code_valid(code):
        return code in [200, 201, 202, 204]

    @staticmethod
    def is_invalid_credentials(code, response):
        if code in [401]:
            errors = response.get("errors")
            if errors and len(errors) > 0:
                # it is possible to get more than one error
                # but usually it is only one error
                for error in errors:
                    if error.get("title") in ["'Invalid Credentials'"] or error.get("code") == "PX100":
                        return True
        return False

    @staticmethod
    def is_wrong_input(code, response):
        if code in [400, 409]:
            errors = response.get("errors")
            if errors and len(errors) > 0:
                # it is possible to get more than one error
                # but usually it is only one error
                for error in errors:
                    if error.get("detail"):
                        return error.get("detail"), error.get("title")
        return None, None

    @staticmethod
    def is_failure_request(response, code):
        failure = None
        if not HTTP.is_response_code_valid(code):
            if code == 404:
                return "\n There is no Internet connection.\n Or requested resource not avialble."
            errors = response.get("errors")
            if errors and len(errors) > 0:
                # take only first error to show
                failure = errors[0]["detail"]
        # return the failure message
        return failure

class ImpRequest():
    INVALID_CREDENTIALS = 1
    WRONG_INPUT = 2
    COMPILE_FAIL = 3
    FAILURE = 4

class ImpCentral:

    @staticmethod
    def auth(user_name, password):
        url = PL_IMPCENTRAL_API_URL_V5 + "auth"
        response, code = HTTP.post(None, url,
            '{"id": "' + user_name + '", "password": "' + password + '"}',
            headers=HttpHeaders.AUTH)

        error = ImpCentral.handle_http_response(response, code)
        return response, error

    @staticmethod
    def refresh_access_token(refresh_token):
        response, code = HTTP.post(None,
            PL_IMPCENTRAL_API_URL_V5 + "/auth/token",
            '{"token":"'+refresh_token+'"}',
            headers=HttpHeaders.AUTH)
        error = ImpCentral.handle_http_response(response, code)
        return response, error

    @staticmethod
    def account(token):
        response, code = HTTP.get(token,
            PL_IMPCENTRAL_API_URL_V5 + "/accounts/me")
        error = ImpCentral.handle_http_response(response, code)
        return response.get("data"), error


    @staticmethod
    def list_products(token, owner_id=None):
        ImpCentral.account(token)
        # TODO: list all products
        if owner_id:
            data='{"filter[owner.id]:"' + owner_id + '"}'
        else:
            data=None

        link = PL_IMPCENTRAL_API_URL_V5 + "products"
        products = []

        while link != None:
            response, code = HTTP.get(token, link, data=data)
            error = ImpCentral.handle_http_response(response, code)
            data = None

            if not error:
                for product in response.get("data"):
                    if product["relationships"]["owner"]["id"] == owner_id:
                        products.append(product)
                link = response["links"].get("next")
            else:
                return response, error

        return products, error

    @staticmethod
    def list_devicegroups(token, product_id):
        devicegroups = []
        link = PL_IMPCENTRAL_API_URL_V5 + "devicegroups"
        data = '{"filter[product.id]:"' + product_id + '"}'
        error = None

        while link != None:
            response, code = HTTP.get(token, link, data=data)
            error = ImpCentral.handle_http_response(response, code)
            data = None

            if not error:
                for devicegroup in response.get("data"):
                    if devicegroup["relationships"]["product"]["id"] == product_id:
                        devicegroups.append(devicegroup)
                    link = response["links"].get("next")
            else:
                return response, error

        return devicegroups, error

    @staticmethod
    def list_devices(token, devicegroup_id=None):
        link = PL_IMPCENTRAL_API_URL_V5 + "devices"
        devices = []
        # filter by group id or not
        if devicegroup_id:
            data='{"filter[devicegroup.id]": "' + devicegroup_id + '"}'
        else:
            data=None

        while link != None:
            response, code = HTTP.get(token, url=link, data=data)
            error = ImpCentral.handle_http_response(response, code)
            data = None
            if not error:
                for device in response.get('data'):
                    devgrp = device["relationships"].get("devicegroup")
                    if (devicegroup_id == None
                        or (devgrp and devgrp["id"] == devicegroup_id)):
                        devices.append(device)
                link = response["links"].get("next")
            else:
                return respone, error

        return devices, error

    @staticmethod
    def get_devicegroup(token, devicegroup_id):
        url = PL_IMPCENTRAL_API_URL_V5 + "devicegroups/" + devicegroup_id
        response, code = HTTP.get(token, url=url)
        error = ImpCentral.handle_http_response(response, code)
        return response.get("data"), error

    @staticmethod
    def get_deployment(token, deployment_id):
        url = PL_IMPCENTRAL_API_URL_V5 + "deployments/" + deployment_id
        response, code = HTTP.get(token, url=url)
        error = ImpCentral.handle_http_response(response, code)
        return response.get("data"), error

    @staticmethod
    def get_device(token, device_id):
        response, code = HTTP.get(token,
            PL_IMPCENTRAL_API_URL_V5 + "devices/" + device_id)
        error = ImpCentral.handle_http_response(response, error)
        return response, error


    @staticmethod
    def create_product(token, product_name):
        url = PL_IMPCENTRAL_API_URL_V5 + "products"
        data = json.dumps({
            "data": {
                "type": "product",
                "attributes": {
                    "name": product_name,
                    "description": "Product created from sublime plugin"
                }
            }
        })
        response, code = HTTP.post(token, url, data, headers=HttpHeaders.DEFAULT)

        error = ImpCentral.handle_http_response(response, code)

        return response.get("data"), error

    @staticmethod
    def create_devicegroup(token, product_id, devicegroup_name):
        url = PL_IMPCENTRAL_API_URL_V5 + "devicegroups"
        data = json.dumps({
            "data": {
                "type": "development_devicegroup",
                "attributes": {
                    "name": devicegroup_name,
                    "description": "Devicegroup created from sublime plugin"
                },
                "relationships": {
                    "product": {
                        "type": "product",
                        "id": product_id
                    }
                }
            }})

        response, code = HTTP.post(token, url, data)
        error = ImpCentral.handle_http_response(response, code)
        return response.get("data"), error

    @staticmethod
    def create_logstream(token):
        response, code = HTTP.post(token,
            url=PL_IMPCENTRAL_API_URL_V5 + "logstream")
        error = ImpCentral.handle_http_response(response, code)
        return response.get("data"), error

    @staticmethod
    def attach_device_to_logstream(token, logstream_id, device_id):
        response, code = HTTP.put(token,
            url=PL_IMPCENTRAL_API_URL_V5 + "logstream/" + logstream_id + "/" + device_id,
            data="{}")
        error = ImpCentral.handle_http_response(response, code)
        # Note: response in None in that case
        return response, error


    @staticmethod
    def open_logstream(token, logstream_id):
        response = None
        url = PL_IMPCENTRAL_API_URL_V5 + "logstream/" + logstream_id
        headers = HTTP.get_http_headers(token, HttpHeaders.STREAM)
        # open socket to start polling
        request = urllib.request.Request(
            url=url, headers=headers, method="GET")
        try:
            response = urllib.request.urlopen(request, timeout=None)
        except socket.timeout:
            # open url timeout
            response = None
        except urllib.error.HTTPError as err:
            # TODO: - handle expired access token
            #       - no internet connection
            response = None
        if not response:
            respone = None

        return response

    @staticmethod
    def create_deployment(token, devicegroup_id, agent_code, device_code):
        url = PL_IMPCENTRAL_API_URL_V5 + "deployments"
        data = ('{"data":{"type":"deployment",'
              ' "attributes": {'
              '  "description": "Sublime text"'
              ', "origin": "sublime"'
              ', "tags": []'
              ', "agent_code": ' + json.dumps(agent_code) +
              ', "device_code" : ' + json.dumps(device_code) +
              '},'
              '"relationships": {"devicegroup": {'
              ' "type": "development_devicegroup", "id": "' + devicegroup_id + '"}}'
              ' }}')
        ## create a new deployment
        response, code = HTTP.post(token, url=url, data=data)
        error = ImpCentral.handle_http_response(response, code)
        return response.get("data"), error

    @staticmethod
    def assign_device(token, devicegroup_id, device_id):
        url = PL_IMPCENTRAL_API_URL_V5 + "devicegroups/" + devicegroup_id + "/relationships/devices"
        data = json.dumps({
                "data" : [{
                    "type": "device",
                    "id": device_id
                }]
            })

        response, code = HTTP.post(token, url, data)
        error = ImpCentral.handle_http_response(response, code)
        return response, error

    @staticmethod
    def unassign_device(token, devicegroup_id, device_id):
        url = PL_IMPCENTRAL_API_URL_V5 + "devicegroups/" + devicegroup_id + "/relationships/devices"
        data = json.dumps({
                "data" : [{
                    "type": "device",
                    "id": device_id
                }]
            })
        # Append the selected device to the device group
        response, code = HTTP.delete(token, url, data)

        error = ImpCentral.handle_http_response(response, code)
        return response, error

    @staticmethod
    def conditional_restart(token, devicegroup_id):
        url = PL_IMPCENTRAL_API_URL_V5 + "devicegroups/" + devicegroup_id + "/conditional_restart"
        response, code = HTTP.post(token, url)

        error = ImpCentral.handle_http_response(response, code)
        return response, error

    @staticmethod
    def handle_http_response(response, code):
        if HTTP.is_response_code_valid(code):
            return None

        # Handle invalid credentials use-case
        if HTTP.is_invalid_credentials(code, response):
            return {"code": ImpRequest.INVALID_CREDENTIALS, "error": "Invalid Credentials"}

        # handle wrong input use-case
        error, title = HTTP.is_wrong_input(code, response)
        if error:
            # offer for the user to re-try current action
            return {"code" : ImpRequest.WRONG_INPUT, "message": error}

        # Handle failure use-case
        failure = HTTP.is_failure_request(response, code)
        if failure:
            return {"code": ImpRequest.FAILURE, "message": failure}

        return {"code": ImpRequest.FAILURE, "message": "Unhandled http error: " + str(code)}

    @staticmethod
    def read_logs(handler):
        return [], None

class SourceType():
    AGENT = 0
    DEVICE = 1


class Preprocessor:
    """Preprocessor and Builder specific implementation"""

    def __init__(self):
        self.line_table = {SourceType.AGENT: None, SourceType.DEVICE: None}

    def preprocess(self, env):

        settings = env.project_manager.load_settings()
        dest_dir = env.project_manager.get_build_directory_path()
        proj_dir = env.project_manager.get_project_directory_path()

        source_agent_filename  = os.path.join(proj_dir, settings.get(EI_AGENT_FILE))
        result_agent_filename  = os.path.join(dest_dir, PR_PREPROCESSED_PREFIX + PR_AGENT_FILE_NAME)
        source_device_filename = os.path.join(proj_dir, settings.get(EI_DEVICE_FILE))
        result_device_filename = os.path.join(dest_dir, PR_PREPROCESSED_PREFIX + PR_DEVICE_FILE_NAME)

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        for code_files in [[
            source_agent_filename,
            result_agent_filename
        ], [
            source_device_filename,
            result_device_filename
        ]]:
            try:
                args = [
                    settings[EI_BUILDER_SETTINGS][EI_ST_PR_NODE_PATH],
                    settings[EI_BUILDER_SETTINGS][EI_ST_PR_BUILDER_CLI],
                    "-l",
                    code_files[0].replace("\\", "/")
                ]

                github_user, github_token = env.project_manager.get_github_auth_info()
                if github_user and github_token:
                    args.append("--github-user")
                    args.append(github_user)
                    args.append("--github-token")
                    args.append(github_token)

                settings = env.project_manager.load_settings()
                builder_settings = settings[EI_BUILDER_SETTINGS]

                variable_defines = builder_settings[EI_VARIABLE_DEFINES] \
                    if builder_settings and EI_VARIABLE_DEFINES in builder_settings else None

                if variable_defines:
                    for key in variable_defines:
                        args.append("-D" + key)
                        args.append(variable_defines[key])

                pipes = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                prep_out, prep_err = pipes.communicate()

                def strip_off_color_control_chars(str):
                    return str.replace("\x1B[31m", "").replace("\x1B[39m", "")

                if pipes.returncode != 0 or len(prep_err):
                    reported_error = strip_off_color_control_chars(prep_err.strip().decode("utf-8"))
                    env.ui_manager.write_to_console(STR_ERR_PREPROCESSING_ERROR.format(reported_error))
                    # Return on error
                    return None, None

                # Write the binary content to the file
                with open(code_files[1], "wb") as output:
                    output.write(prep_out)

                def substitute_string_in_file(filename, old_string, new_string):
                    with open(filename, encoding="utf-8") as f:
                        s = f.read()
                        if old_string not in s:
                            return
                    with open(filename, 'w', encoding="utf-8") as f:
                        s = s.replace(old_string, new_string)
                        f.write(s)

                # Change line number anchors format
                substitute_string_in_file(code_files[1], "#line", "//line")

            except subprocess.CalledProcessError as error:
                log_debug("Error running preprocessor. The process returned code: " + str(error.returncode))

        self.__build_line_table(env)
        return result_agent_filename, result_device_filename

    def __build_line_table(self, env):
        for source_type in self.line_table:
            self.line_table[source_type] = self.__build_line_table_for(source_type, env)

    def __build_line_table_for(self, source_type, env):
        # Setup the preprocessed file name based on the source type
        bld_dir = env.project_manager.get_build_directory_path()
        if source_type == SourceType.AGENT:
            preprocessed_file_path = os.path.join(bld_dir, PR_PREPROCESSED_PREFIX + PR_AGENT_FILE_NAME)
            orig_file = PR_AGENT_FILE_NAME
        elif source_type == SourceType.DEVICE:
            preprocessed_file_path = os.path.join(bld_dir, PR_PREPROCESSED_PREFIX + PR_DEVICE_FILE_NAME)
            orig_file = PR_DEVICE_FILE_NAME
        else:
            log_debug("Wrong source type")
            return

        # Parse the target file and build the code line table
        line_table = {}
        pattern = re.compile(r".*//line (\d+) \"(.+)\"")
        curr_line = 0
        orig_line = 0
        if os.path.exists(preprocessed_file_path):
            with open(preprocessed_file_path, 'r', encoding="utf-8") as f:
                while 1:
                    line_table[str(curr_line)] = (orig_file, orig_line)
                    line = f.readline()
                    if not line:
                        break
                    match = pattern.match(line)
                    if match:
                        orig_line = int(match.group(1)) - 1
                        orig_file = match.group(2)
                    orig_line += 1
                    curr_line += 1

        return line_table

    # Converts error location in the preprocessed code into the original filename and line number
    def get_error_location(self, source_type, line, env):
        if not self.line_table[source_type]:
            self.__build_line_table(env)
        code_table = self.line_table[source_type]
        return None if code_table is None else code_table[str(line)]


class BaseElectricImpCommand(sublime_plugin.WindowCommand):
    """The base class for all the Electric Imp Commands"""

    def init_env_and_settings(self):
        if not ProjectManager.is_electric_imp_project_window(self.window):
            # Do nothing if it's not an EI project
            return

        if not hasattr(self, "env"):
            self.env = Env.get_existing_or_create_env_for(self.window)

        # Try to locate node and node modules
        settings = self.load_settings()
        if EI_BUILDER_SETTINGS not in settings:
            settings[EI_BUILDER_SETTINGS] = {
                EI_VARIABLE_DEFINES: {}
            }
        builder_settings = settings[EI_BUILDER_SETTINGS]

        settings_updated = False

        node_locator = NodeLocator(sublime.platform())
        node_path = node_locator.get_node_path()
        if (EI_ST_PR_NODE_PATH not in builder_settings or node_path != builder_settings[EI_ST_PR_NODE_PATH]) \
                and os.path.exists(node_path):
            settings_updated = True
            builder_settings[EI_ST_PR_NODE_PATH] = node_path

        builder_cli_path = node_locator.get_builder_cli_path()
        if (EI_ST_PR_BUILDER_CLI not in builder_settings or builder_cli_path != builder_settings[EI_ST_PR_BUILDER_CLI]) \
                and os.path.exists(builder_cli_path):
            settings_updated = True
            builder_settings[EI_ST_PR_BUILDER_CLI] = builder_cli_path

        if settings_updated:
            self.env.project_manager.save_settings(PR_SETTINGS_FILE, settings)

    def load_settings(self):
        return self.env.project_manager.load_settings()

    def load_auth_settings(self):
        return self.env.project_manager.load_settings_file(PR_AUTH_INFO_FILE)

    def on_action_complete(self, canceled=False):
        if not canceled and self.cmd_on_complete != None:
            self.window.run_command(self.cmd_on_complete)

    def run(self, cmd_on_complete=None):
        self.init_env_and_settings()
        self.env.ui_manager.init_tty()
        self.cmd_on_complete = cmd_on_complete

        # Setup pending callback
        if cmd_on_complete:
            # prevent an infinite loop in case of error
            if cmd_on_complete == self.name():
                return
            # perform command on completion
            self.action()
            return

        commands = [
            {"command":"imp_check_nodejs_path", "method": ImpCheckNodejsPathCommand.check},
            {"command":"imp_check_builder_path", "method": ImpCheckBuilderPathCommand.check},
            {"command":"imp_auth", "method": ImpAuthCommand.check},
            {"command":"imp_refresh_token", "method": ImpRefreshTokenCommand.check},
            {"command":"imp_create_new_product", "method": ImpCreateNewProductCommand.check},
            {"command":"imp_create_new_device_group", "method": ImpCreateNewDeviceGroupCommand.check},
            {"command":"imp_load_code", "method": ImpLoadCodeCommand.check}]

        for x in commands:
            self.show_action_status(x["command"])
            if x["command"] == self.name():
                break

            if not x["method"](self):
                self.window.run_command(x["command"], {"cmd_on_complete": self.name()})
                return
        # perform an action of the current command
        self.show_action_status(self.name())
        self.action()
        self.show_action_status()

    def update_settings(self, index, value):
        settings = self.load_settings()
        settings[index] = value
        self.env.project_manager.save_settings(PR_SETTINGS_FILE, settings)

    def update_auth_settings(self, index, value):
        settings = self.load_auth_settings()
        settings[index] = value
        self.env.project_manager.save_settings(PR_AUTH_INFO_FILE, settings)

    def print_to_tty(self, text):
        env = Env.For(self.window)
        if env:
            self.env.ui_manager.write_to_console(text)
        else:
            print(STR_ERR_CONSOLE_NOT_FOUND.format(text))

    def is_enabled(self):
        return ProjectManager.is_electric_imp_project_window(self.window)

    def update_status_message(self, query_data=True):
        self.env.ui_manager.show_settings_value_in_status(
            EI_PRODUCT_ID, PL_PRODUCT_STATUS_KEY, STR_STATUS_ACTIVE_PRODUCT)

    def show_action_status(self, action=None):
        self.env.ui_manager.show_action_value_in_status(
            PL_ACTION_STATUS_KEY, action, STR_STATUS_ACTION)

    # Check HTTP response and force an action
    # There are four use-cases are possible:
    # 1. Code valid
    # 2. Refresh token expired - invalid credentials
    # 3. Wrong input (for example product name already exists)
    # 4. All other failures
    # Check HTTP response and force an action
    # There are four use-cases are possible:
    # 1. Code valid
    # 2. Refresh token expired - invalid credentials
    # 3. Wrong input (for example product name already exists)
    # 4. All other failures
    def check_imp_error(self, error, str_failed, str_retry, should_retry=True):
        if not error:
            return False

        # Handle invalid credentials use-case
        if error["code"] == ImpRequest.INVALID_CREDENTIALS:
            # force token update and restart command
            auth = self.load_auth_settings()
            token = auth.get(EI_ACCESS_TOKEN_SET)

            if not token:
                if (not should_retry or
                    not sublime.ok_cancel_dialog(str_retry, "Try again")):
                    return True

            if token and EI_ACCESS_TOKEN in token:
                # reset access token to force an update
                token[EI_ACCESS_TOKEN] = None
                self.update_auth_settings(EI_ACCESS_TOKEN_SET, token)

            # use an original command to refresh credentials
            if self.cmd_on_complete:
                # run an ariginal command
                self.window.run_command(self.cmd_on_complete)
            else:
                # re-run current command
                self.window.run_command(self.name())
            return True

        # handle wrong input use-case
        if error["code"] == ImpRequest.WRONG_INPUT:
            # offer for the user to re-try current action
            if should_retry and sublime.ok_cancel_dialog(error["message"], "Try again"):
                if self.cmd_on_complete:
                    self.window.run_command(self.name(), {"cmd_on_complete" : self.cmd_on_complete})
                else:
                    self.window.run_command(self.name())
            return True

        # Handle failure use-case
        if error["code"] == ImpRequest.FAILURE:
            # offer for the user to re-try current action
            if (should_retry and str_failed
                and sublime.ok_cancel_dialog(str_failed + ":\n" + error["message"], "Try again")):
                if self.cmd_on_complete:
                    self.window.run_command(self.name(), {"cmd_on_complete" : self.cmd_on_complete})
                else:
                    self.window.run_command(self.name())

        return True

    # reset current credentials
    # which trigger login/pwd procedure on next command
    def reset_credentails(self):
        self.update_auth_settings(EI_ACCESS_TOKEN_SET, None)

###
### Configure the nodejs path
###
class ImpCheckNodejsPathCommand(BaseElectricImpCommand):
    @staticmethod
    def check(base):
        settings = base.load_settings()
        builder_settings = settings[EI_BUILDER_SETTINGS] if EI_BUILDER_SETTINGS in settings else {}
        result = EI_ST_PR_NODE_PATH not in builder_settings or not os.path.exists(builder_settings[EI_ST_PR_NODE_PATH])
        return not result

    def action(self, skip_dialog=False):
        if not skip_dialog and not sublime.ok_cancel_dialog(STR_PROVIDE_NODE_JS_PATH):
            self.on_action_complete(canceled=True)
            return
        AnfNewProject(self.window, STR_NODE_JS_PATH, self.on_node_js_path_provided).run("/")

    def on_node_js_path_provided(self, path):
        log_debug("Node.js path provided: " + path)
        if os.path.exists(path):
            log_debug("Node.js path is valid")
            settings = self.load_settings()
            if EI_BUILDER_SETTINGS not in settings:
                settings[EI_BUILDER_SETTINGS] = {}
            builder_settings = settings[EI_BUILDER_SETTINGS]
            builder_settings[EI_ST_PR_NODE_PATH] = path
            self.env.project_manager.save_settings(PR_SETTINGS_FILE, settings)
        else:
            if sublime.ok_cancel_dialog(STR_INVALID_NODE_JS_PATH):
                self.action(skip_dialog=True)

        # Loop back to the main settings check
        self.on_action_complete()

#
# Check the Builder path
# Builder uses for preprocessing libraries
#
class ImpCheckBuilderPathCommand(BaseElectricImpCommand):
    @staticmethod
    def check(base):
        settings = base.load_settings()
        builder_settings = settings[EI_BUILDER_SETTINGS] if EI_BUILDER_SETTINGS in settings else {}
        return EI_ST_PR_BUILDER_CLI in builder_settings and os.path.exists(
            builder_settings[EI_ST_PR_BUILDER_CLI])

    def action(self):
        if need_to_confirm and not sublime.ok_cancel_dialog(STR_PROVIDE_BUILDER_CLI_PATH):
            self.on_action_complete(canceled=True)
            return
        self.callback = callback
        AnfNewProject(self.window, STR_BUILDER_CLI_PATH, self.on_builder_cli_path_provided).run("/")

    def on_builder_cli_path_provided(self, path):
        log_debug("Builder CLI path provided: " + path)
        if os.path.exists(path):
            log_debug("Builder CLI path is valid")
            settings = self.load_settings()
            if EI_BUILDER_SETTINGS not in settings:
                settings[EI_BUILDER_SETTINGS] = {}
            builder_settings = settings[EI_BUILDER_SETTINGS]
            builder_settings[EI_ST_PR_BUILDER_CLI] = path
            self.env.project_manager.save_settings(PR_SETTINGS_FILE, settings)
        else:
            if sublime.ok_cancel_dialog(STR_INVALID_BUILDER_CLI_PATH):
                self.prompt_for_node_js_path(False)

        # Loop back to the main settings check
        self.on_action_complete()

###
### Check user credentials
###
class ImpAuthCommand(BaseElectricImpCommand):
    #
    # check if tokens are available
    #
    @staticmethod
    def check(base):
        token = base.env.project_manager.get_access_token_set()
        return token != None and token.get('refresh_token') != None

    def action(self):
        self.pwd = ""
        self.prompt_for_user_password()

    def prompt_for_user_password(self, need_to_confirm=True, user_name=None, password=None):
        if need_to_confirm and not sublime.ok_cancel_dialog(STR_PROVIDE_USER_ID): return
        if not user_name:
            self.window.show_input_panel(STR_USER_ID, "", self.on_user_id_provided, None, None)
        else:
            # enter pressed
            ufunc = lambda pwd: self.on_user_id_provided(user_name, pwd)
            # partial input
            pfunc = lambda pwd: self.on_user_id_provided(user_name, pwd, True)

            stars = ""
            if password != None:
                stars = "*" * len(password)
            self.window.show_input_panel(STR_PASSWORD, stars, ufunc , pfunc, None)

    def on_user_id_provided(self, user_name, password=None, is_partial=False):
        if not password or is_partial:
            if is_partial:
                chg = password.replace("*", "")

                if  len(password)-len(chg) < len(self.pwd):
                    self.pwd = self.pwd[:(len(password)-len(chg))] + chg
                else:
                    # work-around to prevent infinite recursion
                    if chg == "":
                        return
                    self.pwd = self.pwd + chg

            self.prompt_for_user_password(False, user_name, self.pwd)
        else:
            chg = password.replace("*", "")
            if  len(password)-len(chg) < len(self.pwd):
                self.pwd = self.pwd[:(len(password)-len(chg))] + chg
            else:
                self.pwd = self.pwd + chg
            sublime.set_timeout_async(lambda: self.request_credentials(user_name, self.pwd), 0)

    def request_credentials(self, user_name, password):
        response, error = ImpCentral.auth(user_name, password)
        self.on_login_complete(response, error)

    def on_login_complete(self, payload, error):
        if self.check_imp_error(error,
            STR_FAILED_TO_LOGIN, STR_INVALID_USER_OR_PASSWORD):
            return

        # save the access token in cache and refresh token in the settings file
        log_debug("Access token received")
        self.update_auth_settings(EI_ACCESS_TOKEN_SET, payload)
        # check setting again
        self.on_action_complete();

###
### check that token is not expired
### and try to update it
###
class ImpRefreshTokenCommand(BaseElectricImpCommand):

    ###
    ### Refresh access token if necessary
    ###
    @staticmethod
    def check(base):
        token = base.env.project_manager.get_access_token_set()
        if (not token or not EI_EXPIRES_AT in token
            or not EI_ACCESS_TOKEN in token or not token[EI_ACCESS_TOKEN]):
            return False
        expires = datetime.datetime.strptime(token.get(EI_EXPIRES_AT), "%Y-%m-%dT%H:%M:%S.%fZ")
        return expires > datetime.datetime.utcnow()

    def action(self):
        refresh_token = self.env.project_manager.get_refresh_token()
        # request to refresh an access token
        request, error = ImpCentral.refresh_access_token(refresh_token)
        # Failed to refresh token reset credentials
        # Do not need to show dialog which offer to refresh token
        if self.check_imp_error(error, None, None, False):
            self.update_auth_settings(EI_ACCESS_TOKEN_SET, None)
            self.on_action_complete()
            return
        else:
            # refresh token should not be updated during request
            if not EI_REFRESH_TOKEN in request:
                request[EI_REFRESH_TOKEN] = refresh_token
            self.update_auth_settings(EI_ACCESS_TOKEN_SET, request)

        # restart login process
        self.on_action_complete();

###
### Check the product setting
###
class ImpCreateNewProductCommand(BaseElectricImpCommand):
    @staticmethod
    def check(base):
        settings = base.load_settings()
        return settings.get(EI_PRODUCT_ID) != None

    def action(self):
        sublime.set_timeout_async(self.select_existing_product, 1)

    def on_create_new_product(self, show_dialog=True):
        # prompts a message_dialog
        if show_dialog and not sublime.ok_cancel_dialog(STR_PRODUCT_PROVIDE_NAME):
            return
        self.window.show_input_panel(STR_PRODUCT_NAME, "",
            self.on_new_product_name_provided_async, None, None)

    def on_new_product_name_provided_async(self, name):
        sublime.set_timeout_async(lambda: self.on_new_product_name_provided(name), 0)

    def on_new_product_name_provided(self, name):
        # request a new product creation
        product, error = ImpCentral.create_product(self.env.project_manager.get_access_token(), name)
        # handle possible errors, and force restart or show message dialog
        if self.check_imp_error(error,
            STR_FAILED_TO_CREATE_PRODUCT, STR_RETRY_CREATE_PRODUCT):
            return

        self.update_settings(EI_PRODUCT_ID, product["id"])
        self.update_settings(EI_DEVICEGROUP_ID, None)
        self.on_action_complete()


    def on_product_name_provided(self, index, names):
        # prevent wrong index which should never happened
        if (index < 0 or index > len(names)):
            return

        # Create new product
        if index == 0:
            # Handle a new product creation process
            self.on_create_new_product()
        else:
            # Save selected product in the settings file
            self.update_settings(EI_PRODUCT_ID, names[index-1][0])
            self.update_settings(EI_DEVICEGROUP_ID, None)
            self.on_action_complete()

    def select_existing_product(self):
        token = self.env.project_manager.get_access_token()
        # get current account details
        account, error = ImpCentral.account(token)
        if self.check_imp_error(error,
            STR_FAILED_TO_GET_ACCOUNT_DETAILS, STR_RETRY_SELECT_PRODUCT):
            return

        products, error = ImpCentral.list_products(token, account["id"])
        # Handle imp central request's error
        if self.check_imp_error(error,
            STR_FAILED_TO_GET_PRODUCTS, STR_RETRY_SELECT_PRODUCT):
            return

        # work-around for an absolutely new user
        # who do not have any products at all
        all_names = []
        details = []
        # check that response has some payload
        if products and len(products) > 0:
            all_names = [str(product["attributes"]["name"]) for product in products]
            details = [(product["id"], str(product["attributes"]["name"])) for product in products]

        # make a new product creation option as a part of the product select menu
        self.window.show_quick_panel([ STR_PRODUCT_CREATE_NEW ] + all_names, lambda id: self.on_product_name_provided(id, details))

###
### Check the device group or create a new one
###
class ImpCreateNewDeviceGroupCommand(BaseElectricImpCommand):
    @staticmethod
    def check(base):
        settings = base.load_settings();
        return EI_DEVICEGROUP_ID in settings and settings.get(EI_DEVICEGROUP_ID) != None
        # TODO: Check that project still available in the remote configuraiton

    def action(self):
        sublime.set_timeout_async(self.select_device_group, 0)

    def select_device_group(self):
        settings = self.load_settings()
        product_id = settings[EI_PRODUCT_ID]
        devicegroups, error = ImpCentral.list_devicegroups(
            self.env.project_manager.get_access_token(), product_id)

        # Check that code is correct
        # In common case it is expected error==failure only
        # But, if someone decide to drop product via IDE
        # when user is selecting product in this plugin
        # then the second error message should happen
        if self.check_imp_error(error,
            STR_FAILED_TO_GET_DEVICEGROUPS, STR_RETRY_TO_GET_DEVICEGROUPS):
            return

        # check that response has some payload
        all_names = []
        details = []
        if len(devicegroups) > 0:
            for dg in devicegroups:
                if dg["relationships"]["product"]["id"] == product_id:
                    all_names += [str(dg["attributes"]["name"])]
                    details += [(dg["id"], str(dg["attributes"]["name"]))]

        # make a new product creation option as a part of the product select menu
        self.window.show_quick_panel([ STR_DEVICEGROUP_CREATE_NEW ] + all_names,
            lambda id: self.on_devicegroup_name_provided_async(id, details))

    def on_devicegroup_name_provided_async(self, index, items):
        sublime.set_timeout_async(lambda: self.on_devicegroup_name_provided(index, items), 0)

    def on_devicegroup_name_provided(self, index, items):
        # prevent wrong index which should never happened
        if (index < 0 or index > len(items)):
            self.on_action_complete(canceled=True)
            return

        if index == 0:
            self.on_create_new_devicegroup()
        else:
            # the list of items does not contain the "new device group"
            # selection option which has index == 0
            id = items[index-1][0]
            self.update_settings(EI_DEVICEGROUP_ID, id)
            # Force to propose code loading from the web
            self.update_settings(EI_DEPLOYMENT_ID, None)
            self.on_action_complete()

    def on_create_new_devicegroup(self, show_dialog=True):
        # prompts a message_dialog
        if show_dialog and not sublime.ok_cancel_dialog(STR_DEVICEGROUP_PROVIDE_NAME):
            return
        self.window.show_input_panel(STR_DEVICEGROUP_NAME, "", self.on_new_devicegroup_name_provided, None, None)

    def on_new_devicegroup_name_provided(self, name):
        token = self.env.project_manager.get_access_token()
        settings = self.load_settings()
        # request a new device group creation
        devicegroup, error = ImpCentral.create_devicegroup(
            token, settings[EI_PRODUCT_ID], name)

        if self.check_imp_error(error,
            STR_FAILED_TO_GET_DEVICEGROUP,
            STR_RETRY_TO_GET_DEVICEGROUP):
            return

        self.update_settings(EI_DEVICEGROUP_ID, devicegroup["id"])
        self.update_settings(EI_DEPLOYMENT_ID, EI_DEPLOYMENT_NEW)
        self.on_action_complete()

###
### Request all registered devices and assign
### one of that devices to the device group
### Note: action should trigger logs restart
###
class ImpAssignDeviceCommand(BaseElectricImpCommand):

    def action(self):
        sublime.set_timeout_async(lambda: self.select_existing_device(), 0)

    def on_device_name_provided(self, index, devices):
        # prevent wrong index which
        # happen on cancel
        if (index < 0 or index >= len(devices)):
            return

        # there is no option for create new device
        # therefore index maps on the devices correctly
        device = devices[index]

        settings = self.load_settings()

        # Check that device is not in the device group yet
        # Note: devicegroup could be not defined
        #       if device was not assigned to any device group
        devgrp = device["relationships"].get("devicegroup")
        if devgrp and devgrp["id"] == settings.get(EI_DEVICEGROUP_ID):
            # trigger restart if user assign the same device
            sublime.set_timeout_async(lambda: self.env.log_manager.reset(is_restart=True), 0)
            return

        response, error = ImpCentral.assign_device(
            self.env.project_manager.get_access_token(),
            settings.get(EI_DEVICEGROUP_ID),
            device["id"])

        # handle the respond
        if self.check_imp_error(error,
            STR_FAILED_TO_ASSING_DEVICE, None):
            log_debug("Failed to add device to the group")
            return

        # Request log stream reset to add the devive to the log
        #
        # Note: for another hand it is possible to attach the device
        #       to the logstream without stream reset, but it is
        #       expected that user should not use assign/unassign
        #       devices frequently
        # Note: push reset to the background thread to prevent
        #       concurent access to the LogManager's fields
        sublime.set_timeout_async(lambda: self.env.log_manager.reset(is_restart=True), 0)
        # force log restart, but we need to reset current log first
        sublime.set_timeout_async(lambda: update_log_windows(False), 0)

    def select_existing_device(self):
        devices, error = ImpCentral.list_devices(self.env.project_manager.get_access_token())

        # Check that code is correct
        if self.check_imp_error(error,
            STR_FAILED_TO_GET_DEVICELIST, None):
            return

        if not devices or len(devices) == 0:
            sublime.message_dialog("The device list is empty, please register device first.")
            return

        # check that response has some payload
        # response should contain the list of devices
        if len(devices) > 0:
            all_names = [(str(device["attributes"].get("mac_address")) + " - " +
                str(device["attributes"].get("name"))) for device in devices]
            # make a new product creation option as a part of the product select menu
            self.window.show_quick_panel(all_names,
                lambda id: self.on_device_name_provided(id, devices))

###
### Un-Assign device from the
### current device group
###
class ImpUnassignDeviceCommand(BaseElectricImpCommand):

    def action(self):
        self.select_existing_device()

    def on_device_name_provided(self, index, devices):
        # prevent wrong index which
        # happen on cancel
        if (index < 0 or index >= len(devices)):
            log_debug("There is no device selected")
            return
        # there is no option for create new device
        # therefore index maps on the names correctly
        device = devices[index]
        settings = self.load_settings()

        # Remove the selected device from the devicegroup
        response, error = ImpCentral.unassign_device(
            self.env.project_manager.get_access_token(),
            settings.get(EI_DEVICEGROUP_ID),
            device["id"])

        # handle the respond
        # the second error should happen if someone drop
        # the device group via IDE
        if self.check_imp_error(error,
            STR_FAILED_TO_REMOVE_DEVICE,
            STR_RETRY_TO_REMOVE_DEVICE):
            log_debug("Failed to remove device from the group")
            return

        # Request log stream reset to remove the devive from the log
        # Note: push to the background thread to prevent concurent access
        #       to the logManager's fields
        sublime.set_timeout_async(lambda: self.env.log_manager.reset(is_restart=True), 0)
        # force log restart, but we need to reset current log first
        if len(devices) > 1:
            sublime.set_timeout_async(lambda: update_log_windows(False), 0)

    def select_existing_device(self):
        settings = self.load_settings()

        # list devices for the current device group
        devices, error = ImpCentral.list_devices(
            self.env.project_manager.get_access_token(),
            settings[EI_DEVICEGROUP_ID])

        # Check that code is correct
        if self.check_imp_error(error,
            STR_FAILED_TO_GET_DEVICELIST, None):
            return

        # check that response has some payload
        # response should contain the list of devices
        if len(devices) > 0:
            # filter devices localy
            all_names = [(str(device["attributes"].get("mac_address")) + " - " +
                str(device["attributes"]["name"])) for device in devices]
            # make a new product creation option as a part of the product select menu
            self.window.show_quick_panel(all_names, lambda id: self.on_device_name_provided(id, devices))
        else:
            sublime.message_dialog("There is no assigned devices in the current device group")

class ImpBuildAndRunCommand(BaseElectricImpCommand):
    """Build and Run command implementation"""

    def action(self):
        # Clean up all the error marks first
        for view in self.window.views():
            view.erase_regions(PL_ERROR_REGION_KEY)

        # Save all the views first
        self.save_all_current_window_views()

        # Preprocess the sources
        agent_filename, device_filename = self.env.code_processor.preprocess(self.env)

        if not agent_filename and not device_filename:
            # Error happened during preprocessing, nothing to do.
            log_debug("Preprocessing failed. Please, check the Builder errors")
            return

        if not os.path.exists(agent_filename) or not os.path.exists(device_filename):
            log_debug("Can't find preprocessed agent or device code file")
            sublime.message_dialog(STR_CODE_IS_ABSENT.format(self.get_settings_file_path(PR_SETTINGS_FILE)))

        agent_code = self.read_file(agent_filename)
        device_code = self.read_file(device_filename)

        settings = self.load_settings()

        # post a new deployment into the current devicegroup
        deployment, error = ImpCentral.create_deployment(
            self.env.project_manager.get_access_token(),
            settings.get(EI_DEVICEGROUP_ID),
            agent_code,
            device_code)

        self.handle_deployment(deployment, error)

        self.update_status_message()
        self.on_action_complete()

    # Handle deployment errors more carefull
    def handle_deployment(self, deployment, error):
        settings = self.load_settings()

        # Update the logs first
        update_log_windows(False)

        if not error:
            # save the current deployment
            self.update_settings(EI_DEPLOYMENT_ID, deployment["id"])
            # print the deployment to the status
            self.print_to_tty(STR_STATUS_REVISION_UPLOADED.format(str(deployment["attributes"]["sha"])))
            # note user about conditionla restart request
            self.print_to_tty(STR_DEVICEGROUP_CONDITIONAL_RESTART)

            # Now it's time to restart code on agent and devices
            response, error = ImpCentral.conditional_restart(
                self.env.project_manager.get_access_token(), settings.get(EI_DEVICEGROUP_ID))

            if self.check_imp_error(error, STR_FAILED_CONDITIONAL_RESTART, None):
                return
        else:
            # {
            # 	'error': {
            # 		'message_short': 'Device code compile failed',
            # 		'details': {
            # 			'agent_errors': None,
            # 			'device_errors': [
            # 				{
            # 					'row': 3,
            # 					'error': 'expression expected',
            # 					'column': 24
            # 				}
            # 			]
            # 		},
            # 		'code': 'CompileFailed',
            # 		'message_full': 'Device code compile failed\nDevice Errors:\n3:24 expression expected'
            # 	},
            # 	'success': False
            # }
            def build_error_messages(errors, source_type, env):
                report = ""
                preprocessor = self.env.code_processor
                if errors is not None:
                    for e in errors:
                        log_debug("Original compilation error: " + str(e))
                        orig_file = "main"
                        orig_line = int(e["row"])
                        try:
                            orig_file, orig_line = \
                                preprocessor.get_error_location(source_type=source_type, line=(int(e["row"]) - 1),
                                                                env=env)
                        except Exception as exc:
                            log_debug("Error trying to find original error source: {}".format(exc))
                            pass  # Do nothing - use read values
                        report += STR_ERR_MESSAGE_LINE.format(e["error"], orig_file, orig_line)
                return report
            if error["code"] == ImpRequest.INVALID_CREDENTIALS:
                self.check_imp_error(error, None, None)
                return

            if error["code"] == ImpRequest.COMPILE_FAIL:
                error_message = STR_ERR_DEPLOY_FAILED_WITH_ERRORS
                error_message += build_error_messages(error["details"]["agent_errors"], SourceType.AGENT, self.env)
                error_message += build_error_messages(error["details"]["device_errors"], SourceType.DEVICE, self.env)
                self.print_to_tty(error_message)
            else:
                log_debug("Code deploy failed because of the error: {}".format(str(error["message"])))
                self.print_to_tty("Code deploy failed because of the error: {}".format(str(error["message"])))

    def save_all_current_window_views(self):
        log_debug("Saving all views...")
        self.window.run_command("save_all")

    @staticmethod
    def read_file(filename):
        with open(filename, 'r', encoding="utf-8") as f:
            s = f.read()
        return s


class ImpShowConsoleCommand(BaseElectricImpCommand):
    def action(self):
        self.update_status_message()
        #
        # Handle failure in the logs thread
        # when logs fail the corresponding
        # event should happen
        #
        if self.cmd_on_complete == "auth":
            self.cmd_on_complete = None
            auth = self.load_auth_settings()
            token = auth.get(EI_ACCESS_TOKEN_SET)

            if token and EI_ACCESS_TOKEN in token:
                # reset access token to force an update
                token[EI_ACCESS_TOKEN] = None
                self.update_settings(EI_ACCESS_TOKEN_SET, token)

            # run an ariginal command
            self.window.run_command(self.name())
            return
        # trigger the stream reset procedure
        sublime.set_timeout_async(lambda: self.env.log_manager.reset(is_restart=True), 0)
        # force stream open after restart
        sublime.set_timeout_async(lambda: update_log_windows(False), 0)


class ImpSelectDeviceCommand(BaseElectricImpCommand):
    def action(self):
        self.select_device()

class ImpGetAgentUrlCommand(BaseElectricImpCommand):
    def action(self):
        self.select_existing_device()

    def on_device_name_provided(self, index, devices):
        # prevent wrong index which
        # happen on cancel
        if (index < 0 or index >= len(devices)):
            log_debug("There is no device selected")
            return

        # get device by index in the list
        device = devices[index]

        agent_id = device["attributes"].get("agent_id")
        agent_url = PL_AGENT_URL.format(agent_id)
        sublime.set_clipboard(agent_url)
        sublime.message_dialog(STR_AGENT_URL_COPIED.format(device["id"], agent_url))

    def select_existing_device(self):
        settings = self.load_settings()

        # list devices for the current device group
        devices, error = ImpCentral.list_devices(
            self.env.project_manager.get_access_token(),
            settings[EI_DEVICEGROUP_ID])

        # Check that code is correct
        if self.check_imp_error(error,
            STR_FAILED_TO_GET_DEVICELIST, None):
            return

        # check that response has some payload
        # response should contain the list of devices
        if len(devices) > 0:
            # filter devices localy
            all_names = [(str(device["attributes"].get("mac_address")) + " - " +
                str(device["attributes"]["name"])) for device in devices]
            # make a new product creation option as a part of the product select menu
            if len(devices) == 1:
                self.on_device_name_provided(0, devices)
            else:
                self.window.show_quick_panel(all_names, lambda id: self.on_device_name_provided(id, devices))
        else:
            sublime.message_dialog("There is no assigned devices in the current device group")

class ImpCreateProjectCommand(BaseElectricImpCommand):
    def run(self):
        AnfNewProject(self.window, STR_NEW_PROJECT_LOCATION, self.on_project_path_provided). \
            run(initial_path=self.get_default_project_path())

    @staticmethod
    def get_default_project_path():
        global plugin_settings
        default_project_path_setting = plugin_settings.get(PR_DEFAULT_PROJECT_NAME)
        if not default_project_path_setting:
            if sublime.platform() == "windows":
                default_project_path = os.path.expanduser("~\\" + PR_DEFAULT_PROJECT_NAME).replace("\\", "/")
            else:
                default_project_path = os.path.expanduser("~/" + PR_DEFAULT_PROJECT_NAME)
        else:
            default_project_path = default_project_path_setting
        return default_project_path

    def on_project_path_provided(self, path):
        log_debug("Project path specified: " + path)
        # self.__tmp_project_path = path
        if os.path.exists(path):
            if not sublime.ok_cancel_dialog(STR_FOLDER_EXISTS.format(path)):
                return
        self.create_project(path)
        # self.prompt_for_build_api_key()

    def create_project(self, path):
        source_dir = os.path.join(path, PR_SOURCE_DIRECTORY)
        settings_dir = os.path.join(path, PR_SETTINGS_DIRECTORY)

        log_debug("Creating project at: " + path)
        if not os.path.exists(source_dir):
            os.makedirs(source_dir)
        if not os.path.exists(settings_dir):
            os.makedirs(settings_dir)

        self.copy_template_resource(path, PR_WS_FILE_TEMPLATE)
        self.copy_template_resource(path, PR_PROJECT_FILE_TEMPLATE)
        self.copy_template_resource(path, ".gitignore")

        # Create Electric Imp project settings file
        ProjectManager.dump_map_to_json_file(os.path.join(settings_dir, PR_SETTINGS_FILE), {
            EI_AGENT_FILE: os.path.join(PR_SOURCE_DIRECTORY, PR_AGENT_FILE_NAME),
            EI_DEVICE_FILE: os.path.join(PR_SOURCE_DIRECTORY, PR_DEVICE_FILE_NAME)
        })

        # TODO: Pull the latest code revision from the server
        self.create_source_files_if_absent(path)

        try:
            # Try opening the project in the new window
            self.run_sublime_from_command_line(["-n", os.path.join(path, PR_PROJECT_FILE_TEMPLATE)])
        except:
            log_debug("Error executing sublime: {} ".format(sys.exc_info()[0]))
            # If failed, open the project in the file browser
            self.window.run_command("open_dir", {"dir": path})

    @staticmethod
    def get_sublime_path():
        platform = sublime.platform()
        if platform == "osx":
            return "/Applications/Sublime Text.app/Contents/SharedSupport/bin/subl"
        elif platform == "windows":
            path64 = PL_WIN_PROGRAMS_DIR_64 + "Sublime Text 3\\sublime_text.exe"
            path32 = PL_WIN_PROGRAMS_DIR_32 + "Sublime Text 3\\sublime_text.exe"
            if os.path.exists(path64):
                return path64
            elif os.path.exists(path32):
                return path32
        elif platform == "linux":
            return "/opt/sublime/sublime_text"
        else:
            log_debug("Unknown platform: {}".format(platform))

    def run_sublime_from_command_line(self, args):
        log_debug("Running Sublime...: " + self.get_sublime_path() + " " + str(args))
        args.insert(0, self.get_sublime_path())
        return subprocess.Popen(args)

    def copy_template_resource(self, dest_path, resource_name):
        plugin_dir_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        # extract plugin name from file with extention ".sublime-package":
        # Electric Imp Developer.sublime-package
        plugin_name, ext = os.path.splitext(plugin_dir_name)
        # see https://www.sublimetext.com/docs/3/api_reference.html:
        #       load_resource(name) - Loads the given resource.
        #       The name should be in the format Packages/Default/Main.sublime-menu.
        resource_path = '/'.join(["Packages", plugin_name, PR_TEMPLATE_DIR_NAME, resource_name])
        content = sublime.load_resource(resource_path)

        dest_path = os.path.join(dest_path, resource_name) if os.path.isdir(dest_path) else dest_path
        with open(dest_path, 'a', encoding="utf-8") as f:
            f.write(content)

    def create_source_files_if_absent(self, path):
        source_dir  = os.path.join(path, PR_SOURCE_DIRECTORY)
        agent_file  = os.path.join(source_dir, PR_AGENT_FILE_NAME)
        device_file = os.path.join(source_dir, PR_DEVICE_FILE_NAME)

        # Create empty files if they don't exist
        if not os.path.exists(agent_file):
            with open(agent_file, 'a', encoding="utf-8") as f:
                f.write(STR_INITIAL_SRC_CONTENT.format("Agent"))

        if not os.path.exists(device_file):
            with open(device_file, 'a', encoding="utf-8") as f:
                f.write(STR_INITIAL_SRC_CONTENT.format("Device"))

        return agent_file, device_file

    # Create Project menu item is always enabled regardless of the project type
    def is_enabled(self):
        return True

class ImpLoadCodeCommand(BaseElectricImpCommand):
    @staticmethod
    def check(base):
        settings = base.load_settings()
        return (EI_DEPLOYMENT_ID in settings
                and settings[EI_DEPLOYMENT_ID] != None)

    def action(self):
        if not sublime.ok_cancel_dialog(STR_DEVICEGROUP_CONFIRM_PULLING_CODE):
            self.update_settings(EI_DEPLOYMENT_ID, EI_DEPLOYMENT_NEW)
            self.on_action_complete()
            return

        settings = self.load_settings()
        devicegroup, error = ImpCentral.get_devicegroup(
            self.env.project_manager.get_access_token(), settings[EI_DEVICEGROUP_ID])

        if self.check_imp_error(error,
            STR_FAILED_TO_EXTRACT_CODE, STR_RETRY_TO_EXTRACT_CODE):
            return

        # Handle the use-case when there is no any deployment yet
        # for example for a newly created group via IDE
        if not "current_deployment" in devicegroup["relationships"]:
            sublime.message_dialog("There is no any deployment yet")
            # mark that there is no more deployments yet, to prevent
            # permanent deployments requests
            self.update_settings(EI_DEPLOYMENT_ID, EI_DEPLOYMENT_NEW)
            self.on_action_complete()
            return

        deployment = devicegroup["relationships"]["current_deployment"]["id"]

        # for a one hand it is the same revision as should be
        # in the local file but for another hand
        # local files could be changed and user wants to revert them
        # to the latest revision
        #
        # Note: There is no way to select the deployment version
        #       only the latest version available for user
        if deployment == settings.get(EI_DEPLOYMENT_ID):
            log_debug("Everything up to date")

        url = PL_IMPCENTRAL_API_URL_V5 + "deployments/" + deployment
        deployment, error = ImpCentral.get_deployment(
            self.env.project_manager.get_access_token(), deployment)

        if self.check_imp_error(error,
            STR_FAILED_TO_GET_DEPLOYMENT, None):
            return

        # Pull the latest code from the devicegroup
        source_dir = self.env.project_manager.get_source_directory_path()
        agent_file = os.path.join(source_dir, PR_AGENT_FILE_NAME)
        device_file = os.path.join(source_dir, PR_DEVICE_FILE_NAME)

        if deployment and deployment["attributes"]:
            with open(agent_file, "w", encoding="utf-8") as file:
                file.write(deployment["attributes"]["agent_code"])
            with open(device_file, "w", encoding="utf-8") as file:
                file.write(deployment["attributes"]["device_code"])
            # save the latest deployment id
            self.update_settings(EI_DEPLOYMENT_ID, deployment["id"])
        # trigger an original event on complete
        # it could be build and run or assign/unassing device
        self.on_action_complete()

class AnfNewProject(AdvancedNewFileNew):
    def __init__(self, window, capture="", on_path_provided=None):
        super(AnfNewProject, self).__init__(window)
        self.on_path_provided = on_path_provided
        self.window = window
        self.capture = capture

    def input_panel_caption(self):
        return self.capture

    def entered_file_action(self, path):
        if self.on_path_provided:
            self.on_path_provided(path)

    def update_status_message(self, creation_path):
        self.window.active_view().set_status(PL_PLUGIN_STATUS_KEY, STR_STATUS_CREATING_PROJECT.format(creation_path))

    def clear(self):
        self.window.active_view().erase_status(PL_PLUGIN_STATUS_KEY)


# This is a helper class to implement text substitution in the file path command line
class AnfReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, content):
        self.view.replace(edit, sublime.Region(0, self.view.size()), content)


class ImpErrorProcessor(sublime_plugin.EventListener):
    CLICKABLE_CP_ERROR_PATTERN = r".*\s*ERROR:\s*\[CLICKABLE\]\s.*\((.*)\:(\d+)\)"
    CLICKABLE_RT_ERROR_PATTERN = r".*\s*ERROR:\s*\[CLICKABLE\]\s*(?:\S*)\s*(?:at|from)\s*.*\s+\((\S*):(\d+)\)\s*"

    def on_post_text_command(self, view, command_name, args):
        window = view.window()
        env = Env.For(window)
        if not env or view != env.terminal:
            # Not a console window - nothing to do
            return
        selected_line = view.substr(view.line(view.sel()[0]))

        cp_error_pattern = re.compile(self.CLICKABLE_CP_ERROR_PATTERN)
        rt_error_pattern = re.compile(self.CLICKABLE_RT_ERROR_PATTERN)

        orig_file = None
        orig_line = None

        cp_match = cp_error_pattern.match(selected_line)
        if cp_match:  # Compilation error message
            orig_file = cp_match.group(1)
            orig_line = int(cp_match.group(2)) - 1
        else:
            rt_match = rt_error_pattern.match(selected_line)
            if rt_match:  # Runtime error message
                orig_file = rt_match.group(1)
                orig_line = int(rt_match.group(2)) - 1

        log_debug("Selected line: " + selected_line + ", original file name: " +
                  str(orig_file) + " orig_line: " + str(orig_line))

        if orig_file is not None and orig_line is not None:

            source_dir = os.path.join(os.path.dirname(window.project_file_name()), PR_SOURCE_DIRECTORY)
            file_name = os.path.join(source_dir, orig_file)

            if not os.path.exists(file_name):
                return

            file_view = window.open_file(file_name)

            def select_region():
                if file_view.is_loading():
                    sublime.set_timeout_async(select_region, 0)
                    return
                # First, erase all previous error marks
                file_view.erase_regions(PL_ERROR_REGION_KEY)
                # Create a new error mark
                pt = file_view.text_point(orig_line, 0)
                error_region = sublime.Region(pt)
                file_view.add_regions(PL_ERROR_REGION_KEY,
                                      [error_region],
                                      scope="keyword",
                                      icon="circle",
                                      flags=sublime.DRAW_SOLID_UNDERLINE)
                file_view.show(error_region)

            attempt = 0
            max_attempts = 3
            while attempt < max_attempts:
                attempt += 1
                sublime.set_timeout(select_region, 100)
                if not file_view.is_loading():
                    break

    def __update_status(self, view):
        window = view.window()
        if not ProjectManager.is_electric_imp_project_window(window):
            # Do nothing if it's not an EI project
            return

        # If there is no existing env for the window, create one
        env = Env.For(window)
        if not env:
            env = Env.get_existing_or_create_env_for(window)
        env.ui_manager.show_settings_value_in_status(EI_PRODUCT_ID, PL_PRODUCT_STATUS_KEY, STR_STATUS_ACTIVE_PRODUCT)

    def on_new(self, view):
        self.__update_status(view)

    def on_load(self, view):
        self.__update_status(view)


def log_debug(text):
    global plugin_settings
    if plugin_settings and plugin_settings.get(PL_DEBUG_FLAG):
        print("  [EI::Debug] " + text)


def plugin_loaded():
    global plugin_settings
    plugin_settings = sublime.load_settings(PL_SETTINGS_FILE)
    update_log_windows()


class LogManager:
    def __init__(self, env):
        self.env = env
        self.poll_url = None
        self.last_shown_log = None
        self.sock = None
        self.devices = []
        self.has_logs = False
        # Suported states:
        self.IDLE = 0
        self.INIT = 1
        self.POLL = 2
        self.FAIL = 3
        # set initial state
        self.state = self.IDLE
        # prevent multiple requests when http is pending
        self.update_log_started = False
        # no timer on start-up
        self.keep_alive = None

    def start(self):
        if self.state == self.IDLE:
            self.state = self.INIT
            self.write_to_console("Log stream start requested ...\n")
        else:
            log_debug("Unexpected log manger state")

    def stop(self, is_restart=False):
        if self.state == self.POLL:
            if is_restart:
                self.write_to_console("Realtime logging restart requested.")
                # set current state to idle
                self.state = self.IDLE
                # and then trigger log start
                sublime.set_timeout_async(lambda: update_log_windows(False), 0)
                return
            # stop logs
            self.write_to_console("Realtime logging has stopped. Please refresh to enable it again.")
        elif self.state == self.INIT:
            self.write_to_console("Realtime logging not started. Please refresh to enable it again.")

        # change current state depends on initial
        self.state = self.IDLE
    #
    def check_imp_error(self, error):
        if not error:
            return False

        # Handle invalid credentials use-case only
        # the following string should restart logs via command
        # which lead to access token renew
        if error["code"] == ImpRequest.INVALID_CREDENTIALS:
            sublime.set_timeout_async(
                lambda: self.env.window.run_command("imp_show_console", {"cmd_on_complete": "auth"}), 0)

        return True


    def __read_logs(self):
        if self.sock and type(self.sock) != None and self.sock.fp != None:
            next_log = False
            next_cmd = False
            logs = []
            count = PL_LOGS_MAX_PER_REQUEST
            while count > 0:
                # lets read no more than coun logs per one loop
                rd, wd, ed = select.select([self.sock], [], [], 0)
                if not rd:
                    break
                else:
                    for line in self.sock:
                        if next_log:
                            next_log = False
                            logs.append(line.decode("utf-8"))
                        elif next_cmd:
                            next_cmd = False
                            if line == b'data: closed\n':
                                self.reset()
                                logs.appned("Stream was closed by server event.\n")
                                return logs
                            if line == b'data: opened\n':
                                self.keep_alive = datetime.datetime.now()
                                return logs
                            if line != b'\n':
                                logs.append(line.decode("utf-8"))

                        elif line == b'event: message\n':
                            count -= 1
                            next_log = True

                        elif line == b'event: state_change\n':
                            count -= 1
                            next_cmd = True
                        elif line == b'\n':
                            next_cmd = False
                            next_log = False
                            break
                        elif line == b': keep-alive\n':
                            self.keep_alive = datetime.datetime.now()
                        else:
                            log_debug("Unhandled command:" + str(line.decode("utf-8")))

            # check that stream was not dropped
            if self.keep_alive != None and len(logs) == 0:
                delta = datetime.datetime.now() - self.keep_alive
                if delta.seconds > PL_KEEP_ALIVE_TIMEOUT:
                    log_debug("Did not get keep alive ontime. Trigger log reset.")
                    self.reset(is_restart=True)

            return logs

    def query_logs(self):
        log_request_time = False

        # check if it is polling procedure
        if self.sock and type(self.sock) != None and self.sock.fp != None:
            result = {"logs": self.__read_logs()}
            return result

        ###
        ### Initialize logstream for the device group
        ###
        devicegroup_id = self.env.project_manager.load_settings().get(EI_DEVICEGROUP_ID)
        self.error = None

        if not devicegroup_id:
            # Nothing to do yet
            self.error = "No device group"
            return None

        logs = []
        token = self.env.project_manager.get_access_token()

        # Request the list of the devices for the device group
        # on first connection and cache it for future
        if not self.poll_url:
            log_debug("Request devices")
            devices, error = ImpCentral.list_devices(token, devicegroup_id)

            # Suppose that there is no logs if there is no device
            if self.check_imp_error(error):
                return None

            #if len(devices) == 0:
            #    self.write_to_console("There is no devices in current device group. Please assign some device to start logging.")
            #    return None

            # cache device list
            # it could be re-use on the next connection
            # and uses for smart log output
            self.devices = devices

        log_debug("Request logstream")
        # request a new logstream instance
        logstream, error = ImpCentral.create_logstream(token)

        if self.check_imp_error(error):
            return None

        self.poll_url = logstream["id"]

        log_debug("Open stream")
        self.sock = ImpCentral.open_logstream(token, self.poll_url)

        # something went wrong, reset current state
        if not self.sock:
            return None

        log_debug("Attach devices")
        # attache the devices from the device group to the logstream
        for device in self.devices:
            if ("devicegroup" in device["relationships"]
                and devicegroup_id == device["relationships"]["devicegroup"]["id"]):

                response, error = ImpCentral.attach_device_to_logstream(
                    token, self.poll_url, device["id"])

                if self.check_imp_error(error):
                    return None

        log_debug("Logstream config done, start polling")

        self.state = self.POLL
        self.write_to_console("Logstream started.")

        start = None
        if log_request_time:
            start = datetime.datetime.now()

        if log_request_time:
            elapsed = datetime.datetime.now() - start
            log_debug("Time spent in calling the url: " + url + " is: " + str(elapsed))

        return {"logs": []}

    @staticmethod
    def logs_are_equal(first, second):
        return first == second

    def update_logs(self):
        def __update_logs():
            self.update_log_started = True

            logs_json = self.query_logs()
            # no logs available
            if not logs_json:
                self.reset()
                self.update_log_started = False
                return

            logs_list = logs_json["logs"]

            i = len(logs_list) if logs_list else 0
            while i > 0:
                i -= 1
                log = logs_list[i]
                if self.last_shown_log and LogManager.logs_are_equal(self.last_shown_log, log):
                    i += 1
                    break
            while i < len(logs_list):
                log = logs_list[i]
                i += 1
                # skip empty logs
                if not log:
                    continue

                self.write_to_console(log)
                self.last_shown_log = log
            self.update_log_started = False

        if not self.update_log_started:
            sublime.set_timeout_async(__update_logs, 0)

    def convert_line_numbers(self, log):
        message = log["message"]
        if log["type"] in ["server.error", "agent.error"]:
            # agent/device runtime errors
            preprocessor = self.env.code_processor
            pattern = re.compile(r"ERROR:\s*(?:at|from|in)\s+(\w+)\s*(?:\w*):(\d+)")
            match = pattern.match(log["message"])
            log_debug(("[RECOGNIZED]  " if match else "[UNRECOGNIZED]") +
                      "  [ ] Original runtime error: " + log["message"])
            if match:
                func_name = match.group(1)
                line_read = int(match.group(2)) - 1
                try:
                    (orig_file, orig_line) = preprocessor.get_error_location(
                        SourceType.AGENT if log["type"] == "agent.error" else SourceType.DEVICE, line_read, self.env)
                    message = STR_ERR_RUNTIME_ERROR.format(func_name, orig_file, orig_line)
                except:
                    pass  # Use original message if failed to translate the error location
        return message

    def __parse_log(self, log):
        res = {}
        ms = log.split(" ")
        # is some case we could get wrong log format
        # the following code is attemtion to handle such case
        if len(ms) < 5 or ms.pop(0) != "data:":
            res["device"] = "sublime"
            res["dt"] = datetime.datetime.now()
            res["type"] = "sublime.log"
            res["deployment"] = ""
            res["message"] = log[:-1]
        else:
            # date: deviceId timestamp deployment type log-string
            res["device"] = ms.pop(0)
            res["dt"] = datetime.datetime.strptime(ms.pop(0), "%Y-%m-%dT%H:%M:%S.%fZ")
            res["deployment"] = ms.pop(0)
            res["type"] = ms.pop(0)
            res["message"] = " ".join(ms)[:-1]

        return res

    def write_to_console(self, log):
        # parse log string
        # to extract log details
        item = self.__parse_log(log)

        # maps the error details to the corresponding
        # filename and line numbers
        item["message"] = self.convert_line_numbers(item)
        # impCentral provides its own format of the logs
        # but it is not comfortable for user to read such logs
        # therefore the following line just re-format the same log
        self.env.ui_manager.write_to_console(
            item["dt"].strftime('%Y-%m-%d %H:%M:%S%z')
            + " [" + item["device"] + "] " + item["type"] + " " + item["message"])

    def reset(self, is_restart=False):
        # this action should force to close the log stream
        # but on the next request of logs stream should be
        # instatiated
        if self.sock:
            self.sock.close()
        self.sock = None
        # reset poll url to reopen socket
        self.poll_url = None
        # last shown log could be different after device assing
        # that's why log could be suplicated in the console
        # after device assign/an-assign
        self.last_shown_log = None
        # stop traking timer
        self.keep_alive = None
        # reset current state to idle
        self.stop(is_restart)


def update_log_windows(restart_timer=True):
    global project_env_map
    time_start = datetime.datetime.now()
    has_logs = False
    try:
        for (project_path, env) in list(project_env_map.items()):
            # Clean up project windows first
            if not ProjectManager.is_electric_imp_project_window(env.window):
                # It's not a windows that corresponds to an EI project, remove it from the list
                del project_env_map[project_path]
                log_debug("Removing project window: " + str(env.window) + ", total #: " + str(len(project_env_map)))
                continue

            # there are two use-cases when it is possible to get logs
            # on first start on transition from (IDLE -> INIT -> POLL)
            # and on  POLL
            if env.log_manager.state == env.log_manager.POLL:
                env.log_manager.update_logs()
                has_logs = True
            elif env.log_manager.state == env.log_manager.IDLE and not restart_timer:
                env.log_manager.start()
                env.log_manager.update_logs()
                has_logs = True
            # skip logs request for the IDLE and FAIL states
    finally:
        if restart_timer:
            # keep on reading logs while logs are available
            # and keep on log polling once per second
            ms = PL_LOGS_UPDATE_LONG_PERIOD
            if has_logs:
                ms = PL_LOGS_UPDATE_SHORT_PERIOD

            sublime.set_timeout(update_log_windows, ms)
    return True
