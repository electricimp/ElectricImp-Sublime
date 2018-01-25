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
PL_BUILD_API_URL_BASE    = "https://api.electricimp.com"
PL_BUILD_API_URL_V5      = PL_BUILD_API_URL_BASE + "/v5/"
PL_SETTINGS_FILE         = "ImpDeveloper.sublime-settings"
PL_DEBUG_FLAG            = "debug"
PL_AGENT_URL             = "https://agent.electricimp.com/{}"
PL_WIN_PROGRAMS_DIR_32   = "C:\\Program Files (x86)\\"
PL_WIN_PROGRAMS_DIR_64   = "C:\\Program Files\\"
PL_ERROR_REGION_KEY      = "electric-imp-error-region-key"
PL_MODEL_STATUS_KEY      = "model-status-key"
PL_PLUGIN_STATUS_KEY     = "plugin-status-key"
PL_LONG_POLL_TIMEOUT     = 5 # sec
PL_LOGS_UPDATE_PERIOD    = 1000 # ms

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
EI_REFRESH_TOKEN         = "refresh-token"
EI_ACCEESS_TOKEN         = "access-token"
EI_PRODUCT_ID            = "product-id"
EI_DEVICEGROUP_ID        = "device-group-id"

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

    def get_access_token_set(self):
        auth_info = self.load_settings_file(PR_SETTINGS_FILE)
        if auth_info:
            return auth_info.get(EI_ACCEESS_TOKEN)

    def get_access_token(self):
        auth_info = self.load_settings_file(PR_SETTINGS_FILE)
        if auth_info:
            token = auth_info.get(EI_ACCEESS_TOKEN)
            if token and "access_token" in token:
                return token["access_token"]

        return None

    def get_refresh_token(self):
        auth_info = self.load_settings_file(PR_SETTINGS_FILE)
        if auth_info:
            token = auth_info.get(EI_ACCEESS_TOKEN)
            if token and "access_token" in token:
                return token["access_token"]

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
        self.tmp_model = None
        self.tmp_device_ids = None

        # Check settings callback
        self.tmp_check_settings_callback = None

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


class HTTP:
    """Implementation of all the Electric Imp connection functionality"""

    @staticmethod
    def __base64_encode(str):
        return base64.b64encode(str.encode()).decode()

    @staticmethod
    def __get_http_headers(key, headers):
        if headers:
            headers["User-Agent"] = "imp-developer/sublime"
            if key:
                headers["Authorization"] = "Bearer " + key
            return headers

        if not key:
            return {
                "Content-Type": "application/json",
                "User-Agent": "imp-developer/sublime"
            }

        return {
            "Authorization": "Bearer " + key, # HTTP.__base64_encode(key),
            "Content-Type": "application/vnd.api+json",
            "User-Agent": "imp-developer/sublime"
        }

    @staticmethod
    def is_login_key_valid(key):
        request, code = HTTP.get({type: "login_key", login_key: key}, PL_BUILD_API_URL_V5 + "/auth/token")
        return code == 200

    @staticmethod
    def is_refresh_token_valid(token):
        if datetime.datetime.strptime(token.expires_at, "%Y-%m-%dT%H:%M:%S.%fZ") > datetime.now():
            return True
        request, code = HTTP.post({token:token.value}, PL_BUILD_API_URL_V5 + "/auth/token")
        return code == 200


    @staticmethod
    def do_request(key, url, method, data=None, timeout=None, headers=None):
        if data:
            data = data.encode('utf-8')
        req = urllib.request.Request(url,
                                     headers=HTTP.__get_http_headers(key, headers),
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
            result = json.loads(err.reason.decode('utf-8'))
        except urllib.error.ContentTooShortError as err:
            code = 404
            result = "Too short conent exception"

        return result, code

    @staticmethod
    def get(key, url, timeout=None, data=None, headers=None):
        return HTTP.do_request(key, url, "GET", timeout=timeout, data=data, headers=headers)

    @staticmethod
    def post(key, url, data=None, headers={"Content-Type": "application/json"}):
        return HTTP.do_request(key, url, "POST", data, headers=headers)

    @staticmethod
    def put(key, url, data=None, headers={"Content-Type": "application/vnd.api+json"}):
        return HTTP.do_request(key, url, "PUT", data, headers=headers)

    @staticmethod
    def is_response_code_valid(code):
        return code in [200, 201, 202]


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

    def check_settings(self, callback=None, selecting_or_creating_model=None):
        # Setup pending callback
        if callback:
            self.env.tmp_check_settings_callback = callback
        else:
            callback = getattr(self.env, "tmp_check_settings_callback", None)

        if selecting_or_creating_model is not None:
            self.env.tmp_selecting_or_creating_model = selecting_or_creating_model
        else:
            selecting_or_creating_model = getattr(self.env, "tmp_selecting_or_creating_model", None)

        token = self.env.project_manager.get_access_token_set()

        # Perform the checks and prompts for appropriate settings
        #
        # Check the nodejs path which is required for the Builder
        #
        if self.is_missing_node_js_path():
            self.prompt_for_node_js_path()
        #
        # Check the Builder path
        # Builder uses for preprocessing libraries
        #
        elif self.is_missing_builder_cli_path():
            self.prompt_for_builder_cli_path()
        #
        # check if tokens are available
        #
        elif not token or not token['refresh_token']:
            self.prompt_for_user_password()
        #
        # check that token is not expired
        # and try to update it
        #
        elif self.is_access_token_expired(token):
            self.refresh_access_token(token)
        #
        # is product selected and available yet
        #
        elif self.is_missing_product():
            self.select_existing_product()
        #
        # is device group is selected and available yet
        #
        elif self.is_missing_device_group():
            self.select_existing_device_group()
        #
        # Perform an original callback
        # TODO: check if it is possible to save callback in the env
        #       probably we can get troubles with parallel requests
        #
        else:
            # All the checks passed, invoke the callback now
            if callback:
                callback()
            self.env.tmp_check_settings_callback = None
            self.env.tmp_selecting_or_creating_model = None

    ###
    ### Configure the nodejs path
    ###

    def is_missing_node_js_path(self):
        settings = self.load_settings()
        builder_settings = settings[EI_BUILDER_SETTINGS] if EI_BUILDER_SETTINGS in settings else {}
        return EI_ST_PR_NODE_PATH not in builder_settings or not os.path.exists(builder_settings[EI_ST_PR_NODE_PATH])

    def prompt_for_node_js_path(self, need_to_confirm=True):
        if need_to_confirm and not sublime.ok_cancel_dialog(STR_PROVIDE_NODE_JS_PATH): return
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
                self.prompt_for_node_js_path(False)

        # Loop back to the main settings check
        self.check_settings()

    ###
    ### Configure the Builder cli.js
    ###

    def is_missing_builder_cli_path(self):
        settings = self.load_settings()
        builder_settings = settings[EI_BUILDER_SETTINGS] if EI_BUILDER_SETTINGS in settings else {}
        return EI_ST_PR_BUILDER_CLI not in builder_settings or not os.path.exists(
            builder_settings[EI_ST_PR_BUILDER_CLI])

    def prompt_for_builder_cli_path(self, need_to_confirm=True):
        if need_to_confirm and not sublime.ok_cancel_dialog(STR_PROVIDE_BUILDER_CLI_PATH): return
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
        self.check_settings()

    ###
    ### Check user credentials
    ###

    def prompt_for_user_password(self, need_to_confirm=True, user_name=None):
        if need_to_confirm and not sublime.ok_cancel_dialog(STR_PROVIDE_USER_ID): return
        if not user_name:
            self.window.show_input_panel(STR_USER_ID, "", self.on_user_id_provided, None, None)
        else:
            ufunc = lambda pwd: self.on_user_id_provided(user_name, pwd)
            self.window.show_input_panel(STR_PASSWORD, "", ufunc , None, None)

    def on_user_id_provided(self, user_name, password=None):
        if not password:
            self.prompt_for_user_password(False, user_name)
        else:
            url = PL_BUILD_API_URL_V5 + "auth"
            response, code = HTTP.post(None, url, '{"id": "' + user_name + '", "password": "' + password + '"}')
            self.on_login_complete(code, response)

    def on_login_complete(self, code, payload):
        if not HTTP.is_response_code_valid(code):
            # check if user wants to re-enter urename and password
            # TODO: check the reason more carefully:
            # 1. Invalid credentials
            # 2. No internet access or internal server error
            if need_to_confirm and not sublime.ok_cancel_dialog(STR_INVALID_CREDENTIALS): return
            # try to re-enter login/password
            self.prompt_for_user_password();
        else:
            # save the access token in cache and refresh token in the settings file
            log_debug("Access token received")
            settings = self.load_settings()
            settings[EI_ACCEESS_TOKEN] = payload
            self.env.project_manager.save_settings(PR_SETTINGS_FILE, settings)
            # check setting again
            self.check_settings();

    def reset_credentails(self):
        settings = self.load_settings()
        settings[EI_ACCEESS_TOKEN] = None
        self.env.project_manager.save_settings(PR_SETTINGS_FILE, settings)

    def _update_settings(self, index, value):
        settings = self.load_settings()
        settings[index] = value
        self.env.project_manager.save_settings(PR_SETTINGS_FILE, settings)

    ###
    ### Refresh access token if necessary
    ###
    def is_access_token_expired(self, token):
        return datetime.datetime.strptime(token["expires_at"], "%Y-%m-%dT%H:%M:%S.%fZ") <= datetime.datetime.now()

    def refresh_access_token(self, token):
        refresh_token = token["refresh_token"]
        request, code = HTTP.post(token["access_token"], PL_BUILD_API_URL_V5 + "/auth/token", '{"token":'+refresh_token+'}')
        # Failed to refresh token reset credentials
        if not HTTP.is_response_code_valid(code):
            print("FAILED TO REFRESH TOKEN")
            self._update_settings(EI_ACCEESS_TOKEN, None)
        else:
            # refresh token should not be updated during request
            print("NEW TOKEN IS:")
            print(request)
            if not request["refresh_token"]:
                request["refresh_token"] = refresh_token
            self._update_settings(EI_ACCEESS_TOKEN, request)

        # restart login process
        self.check_settings();

    ###
    ### Check the product setting
    ###
    def is_missing_product(self):
        settings = self.load_settings();
        if EI_PRODUCT_ID not in settings or settings.get(EI_PRODUCT_ID) is None:
            return True
        # TODO: Check that project still available in the remote configuraiton
        return False

    def on_create_new_product(self, need_to_confirm=True):
        print("HANDLE NEW PRODUCT CREATION")

    def on_product_name_provided(self, index, names):
        # prevent wrong index which should never happened
        if (index < 0 or index > len(names)):
            return

        # Create new product
        if index == 0:
            # Handle a new product creation process
            self.window.show_input_panel(STR_PRODUCT_NAME, "", self.on_create_new_product, None, None)
        else:
            # Save selected product in the settings file
            self._update_settings(EI_PRODUCT_ID, names[index-1][0])
            self.check_settings()


    def select_existing_product(self):
        response, code = HTTP.get(self.env.project_manager.get_access_token(), PL_BUILD_API_URL_V5 + "products")
        # Check that code is correct
        if not HTTP.is_response_code_valid(code):
            sublime.message_dialog(STR_PRODUCT_SERVER_ERROR + response["errors"][0]["detail"])
            if code == 401:
                self.reset_credentails()
                self.check_settings()
            return

        # check that response has some payload
        if len(response['data']) > 0:
            all_names = [product["attributes"]["name"] for product in response['data']]
            self.__tmp_all_models = [(product["id"], product["attributes"]["name"]) for product in response['data']]

        # make a new product creation option as a part of the product select menu
        self.window.show_quick_panel([ STR_PRODUCT_CREATE_NEW ] + all_names, lambda id: self.on_product_name_provided(id, self.__tmp_all_models))

    def is_missing_device_group(self):
        settings = self.load_settings();
        if EI_DEVICEGROUP_ID not in settings or settings.get(EI_DEVICEGROUP_ID) is None:
            return True
        # TODO: Check that project still available in the remote configuraiton
        return False

    def on_devicegroup_name_provided(self, index, items):
        # prevent wrong index which should never happened
        if (index < 0 or index > len(items)):
            return

        if index == 0:
            print("CREATE NEW DEVICE GROUP")
        else:
            id = items[index-1][0]
            self._update_settings(EI_DEVICEGROUP_ID, id)
            self.check_settings()

    def select_existing_device_group(self):
        settings = self.load_settings()
        response, code = HTTP.get(self.env.project_manager.get_access_token(), PL_BUILD_API_URL_V5 + "devicegroups", '{"filter[product.id]": "'+settings[EI_PRODUCT_ID]+'"}')

        # Check that code is correct
        if not HTTP.is_response_code_valid(code):
            sublime.message_dialog(STR_PRODUCT_SERVER_ERROR + response["errors"][0]["detail"])
            if code == 401:
                self.reset_credentails()
                self.check_settings()
            return

        # check that response has some payload
        if len(response['data']) > 0:
            all_names = []
            self.__tmp_all_models = []
            for product in response['data']:
                if product["relationships"]["product"]["id"] == settings[EI_PRODUCT_ID]:
                    self.__tmp_all_models += [(product["id"], product["attributes"]["name"])]
                    all_names += [product["attributes"]["name"]]

        # make a new product creation option as a part of the product select menu
        self.window.show_quick_panel([ STR_DEVICEGROUP_CREATE_NEW ] + all_names, lambda id: self.on_devicegroup_name_provided(id, self.__tmp_all_models))

    def is_missing_model(self):
        settings = self.load_settings()
        return EI_MODEL_ID not in settings or settings.get(EI_MODEL_ID) is None

    def create_new_model(self, need_to_confirm=True):
        if need_to_confirm and not sublime.ok_cancel_dialog(STR_MODEL_PROVIDE_NAME): return
        self.window.show_input_panel(STR_MODEL_NAME, "", self.on_model_name_provided, None, None)

    def on_model_name_provided(self, name):
        response, code = HTTP.post(self.env.project_manager.get_access_token(),
                                   PL_BUILD_API_URL_V5 + "models/", '{"name" : "' + name + '" }')

        if not HTTP.is_response_code_valid(code) \
                and sublime.ok_cancel_dialog(STR_MODEL_NAME_EXISTS):
            self.create_new_model(False)
            return
        elif not HTTP.is_response_code_valid(code):
            sublime.message_dialog(STR_MODEL_FAILED_TO_CREATE)
            return

        # Save newly created model to the project settings
        settings = self.load_settings()
        settings[EI_MODEL_ID] = response.get("model").get("id")
        settings[EI_MODEL_NAME] = response.get("model").get("name")
        self.env.project_manager.save_settings(PR_SETTINGS_FILE, settings)

        self.update_status_message(query_data=False)

        # Reset the logs
        self.env.log_manager.reset()

        # Check settings
        self.check_settings(selecting_or_creating_model=True)

    def is_missing_device(self):
        settings = self.load_settings()
        return EI_DEVICE_ID not in settings or settings.get(EI_DEVICE_ID) is None

    def load_devices(self, input_device_ids=None, exclude_device_ids=None):
        device_ids = input_device_ids if input_device_ids else []
        device_names = []

        response, code = HTTP.get(self.env.project_manager.get_access_token(),
                                  PL_BUILD_API_URL_V5 + "devices/")
        all_devices = response.get("devices")

        if exclude_device_ids is None:
            exclude_device_ids = []

        def get_device_display_name(device):
            name = d.get("name")
            return name if name else device.get("id")

        if input_device_ids:
            for d_id in input_device_ids:
                for d in all_devices:
                    if d.get("id") == d_id and d_id not in exclude_device_ids:
                        device_names.append(get_device_display_name(d))
                        break
        else:
            for d in all_devices:
                if d.get("id") not in exclude_device_ids:
                    device_ids.append(d.get("id"))
                    device_names.append(get_device_display_name(d))

        return device_ids, device_names

    def on_device_to_add_selected(self, index):
        # Selection was canceled, just return
        if index == -1:
            return

        model = self.env.tmp_model
        device_id = self.env.tmp_device_ids[index]

        response, code = HTTP.put(self.env.project_manager.get_access_token(),
                                  PL_BUILD_API_URL_V5 + "devices/" + device_id,
                                  '{"model_id": "' + model.get("id") + '"}')
        if not HTTP.is_response_code_valid(code):
            sublime.message_dialog(STR_MODEL_ADDING_DEVICE_FAILED)

        # Once the device is registered, select this device
        self.on_device_selected(index)

        sublime.message_dialog(STR_MODEL_IMP_REGISTERED)

        self.env.tmp_model = None
        self.env.tmp_device_ids = None

    def load_this_model(self):
        # We assume the model is set up already
        model_id = self.load_settings().get(EI_MODEL_ID)
        response, code = HTTP.get(self.env.project_manager.get_access_token(),
                                  PL_BUILD_API_URL_V5 + "models/" + str(model_id))
        if HTTP.is_response_code_valid(code):
            return response.get("model")

    def select_device(self, need_to_confirm=True):
        model = self.load_this_model()
        if not model:
            sublime.message_dialog(STR_MODEL_NOT_ASSIGNED)
            return

        device_ids = model.get("devices")
        if not device_ids or not len(device_ids):
            sublime.message_dialog(STR_MODEL_HAS_NO_DEVICES)
            return

        if need_to_confirm and not sublime.ok_cancel_dialog(STR_SELECT_DEVICE): return
        (Env.For(self.window).tmp_device_ids, device_names) = self.load_devices(input_device_ids=device_ids)
        self.window.show_quick_panel(device_names, self.on_device_selected)

    def add_device(self, need_to_confirm=True):
        model = self.load_this_model()
        if not model:
            sublime.message_dialog(STR_MODEL_NOT_ASSIGNED)
            return

        if need_to_confirm and not sublime.ok_cancel_dialog(STR_MODEL_ADD_DEVICE): return

        device_ids = model.get("devices")
        (device_ids, device_names) = self.load_devices(exclude_device_ids=device_ids)

        if len(device_ids) == 0:
            sublime.message_dialog(STR_NO_DEVICES_AVAILABLE)
            return

        self.env.tmp_model = model
        self.env.tmp_device_ids = device_ids
        self.window.show_quick_panel(device_names, self.on_device_to_add_selected)

    def on_device_selected(self, index):
        # Selection was canceled, just return
        if index == -1:
            return
        settings = self.load_settings()
        new_device_id = Env.For(self.window).tmp_device_ids[index]
        old_device_id = None if EI_DEVICE_ID not in settings else settings.get(EI_DEVICE_ID)
        if new_device_id != old_device_id:
            log_debug("New device selected: saving new settings file and restarting the console...")
            # Update the device id
            settings[EI_DEVICE_ID] = Env.For(self.window).tmp_device_ids[index]
            self.env.project_manager.save_settings(PR_SETTINGS_FILE, settings)
            # Clean up the terminal window
            self.env.ui_manager.create_new_console()
            self.env.ui_manager.show_console()
        else:
            log_debug("Newly selected device is the same as the old one. Nothing to do.")
        # Clean up temporary variables
        self.env.tmp_device_ids = None
        # Loop back to the main settings check
        self.check_settings()
        # Reset the logs
        self.env.log_manager.reset()

    def print_to_tty(self, text):
        env = Env.For(self.window)
        if env:
            self.env.ui_manager.write_to_console(text)
        else:
            print(STR_ERR_CONSOLE_NOT_FOUND.format(text))

    def is_enabled(self):
        return ProjectManager.is_electric_imp_project_window(self.window)

    def update_status_message(self, query_data=True):
        self.env.ui_manager.show_settings_value_in_status(EI_PRODUCT_ID, PL_MODEL_STATUS_KEY, STR_STATUS_ACTIVE_MODEL)


class ImpBuildAndRunCommand(BaseElectricImpCommand):
    """Build and Run command implementation"""

    def run(self):
        self.init_env_and_settings()
        self.env.ui_manager.init_tty()
        # Clean up all the error marks first
        for view in self.window.views():
            view.erase_regions(PL_ERROR_REGION_KEY)

        def check_settings_callback():
            if self.env.project_manager.get_access_token() is None:
                log_debug("The build API file is missing, please check the settings")
                return

            # Save all the views first
            self.save_all_current_window_views()

            # Preprocess the sources
            agent_filename, device_filename = self.env.code_processor.preprocess(self.env)

            if not agent_filename and not device_filename:
                # Error happened during preprocessing, nothing to do.
                return

            if not os.path.exists(agent_filename) or not os.path.exists(device_filename):
                log_debug("Can't find code files")
                sublime.message_dialog(STR_CODE_IS_ABSENT.format(self.get_settings_file_path(PR_SETTINGS_FILE)))

            agent_code = self.read_file(agent_filename)
            device_code = self.read_file(device_filename)

            settings = self.load_settings()
            url = PL_BUILD_API_URL_V5 + "deployments"
            data = ('{"data":{"type":"deployment",'
                  ' "attributes": {'
                  '  "description": "Sublime text"'
                  ', "origin": "sublime"'
                  ', "tags": []'
                  ', "agent_code": ' + json.dumps(agent_code) +
                  ', "device_code" : ' + json.dumps(device_code) +
                  '},'
                  '"relationships": {"devicegroup": {'
                  ' "type": "development_devicegroup", "id": "' + settings.get(EI_DEVICEGROUP_ID) + '"}}'
                  ' }}')
            response, code = HTTP.post(key=self.env.project_manager.get_access_token(), url=url, data=data, headers={"Content-Type": "application/vnd.api+json"})
            self.handle_response(response, code)

        self.check_settings(callback=check_settings_callback)
        self.update_status_message()

    def handle_response(self, response, code):
        settings = self.load_settings()

        # Update the logs first
        update_log_windows(False)

        if HTTP.is_response_code_valid(code):
            self.print_to_tty(STR_STATUS_REVISION_UPLOADED.format(str(response["data"]["attributes"]["sha"])))
            self.print_to_tty(STR_DEVICEGROUP_CONDITIONAL_RESTART)

            # Not it's time to restart the code
            url = PL_BUILD_API_URL_V5 + "devicegroups/" + settings.get(EI_DEVICEGROUP_ID) + "/conditional_restart"
            HTTP.post(self.env.project_manager.get_access_token(), url)
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
            if "error" in response:
                error = response["error"]
            else:
                error = "Unknown error"
            if error and error["code"] == "CompileFailed":
                error_message = STR_ERR_DEPLOY_FAILED_WITH_ERRORS
                error_message += build_error_messages(error["details"]["agent_errors"], SourceType.AGENT, self.env)
                error_message += build_error_messages(error["details"]["device_errors"], SourceType.DEVICE, self.env)
                self.print_to_tty(error_message)
            else:
                log_debug("Code deploy failed because of the error: {}".format(str(response["error"]["code"])))

    def save_all_current_window_views(self):
        log_debug("Saving all views...")
        self.window.run_command("save_all")

    @staticmethod
    def read_file(filename):
        with open(filename, 'r', encoding="utf-8") as f:
            s = f.read()
        return s


class ImpShowConsoleCommand(BaseElectricImpCommand):
    def run(self):
        self.init_env_and_settings()
        self.env.ui_manager.init_tty()
        self.check_settings()
        self.update_status_message()
        update_log_windows(False)


class ImpSelectDeviceCommand(BaseElectricImpCommand):
    def run(self):
        self.init_env_and_settings()
        self.check_settings(callback=self.select_device)

class ImpGetAgentUrlCommand(BaseElectricImpCommand):
    def run(self):
        self.init_env_and_settings()

        def check_settings_callback():
            settings = self.load_settings()
            if EI_DEVICE_ID in settings:
                device_id = settings.get(EI_DEVICE_ID)
                response, code = HTTP.get(self.env.project_manager.get_access_token(),
                                          PL_BUILD_API_URL_V5 + "devices/" + device_id)
                agent_id = response.get("device").get("agent_id")
                agent_url = PL_AGENT_URL.format(agent_id)
                sublime.set_clipboard(agent_url)
                sublime.message_dialog(STR_AGENT_URL_COPIED.format(device_id, agent_url))

        self.check_settings(callback=check_settings_callback)

class ImpCreateNewProductCommand(BaseElectricImpCommand):
    def run(self):
        print("Create new product")


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

        # Pull the latest code revision from the server
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


class ImpCreateModel(BaseElectricImpCommand):
    def run(self):
        self.init_env_and_settings()

        def check_settings_callback():
            self.create_new_model()

        self.check_settings(callback=check_settings_callback, selecting_or_creating_model=True)


class ImpSelectModel(BaseElectricImpCommand):
    def run(self):
        self.init_env_and_settings()

        def check_settings_callback():
            self.select_existing_model()

        self.check_settings(callback=check_settings_callback, selecting_or_creating_model=True)

    def select_existing_model(self, need_to_confirm=True):
        response, code = HTTP.get(self.env.project_manager.get_access_token(), PL_BUILD_API_URL_V5 + "models")
        if len(response["models"]) > 0:
            if need_to_confirm and not sublime.ok_cancel_dialog(STR_MODEL_SELECT_EXISTING_MODEL):
                return
            all_model_names = [model["name"] for model in response["models"]]
            self.__tmp_all_models = [(model["id"], model["name"]) for model in response["models"]]
        else:
            sublime.message_dialog(STR_MODEL_NO_MODELS_FOUND)
            return

        self.window.show_quick_panel(all_model_names, self.on_model_selected)

    def on_model_selected(self, index):
        # Selection was canceled, nothing to do here
        if index == -1:
            return

        model_id, model_name = self.__tmp_all_models[index]

        self.__tmp_all_models = None  # We don't need it anymore
        log_debug("Model selected id: " + model_id)

        # Save newly created model to the project settings
        settings = self.load_settings()
        settings[EI_MODEL_ID] = model_id
        settings[EI_MODEL_NAME] = model_name
        self.env.project_manager.save_settings(PR_SETTINGS_FILE, settings)

        # Reset the logs
        self.env.log_manager.reset()

        # Update the Model name in the status bar
        self.update_status_message(query_data=False)

        if not sublime.ok_cancel_dialog(STR_MODEL_CONFIRM_PULLING_MODEL_CODE):
            return

        # Pull the latest code from the Model
        source_dir = self.env.project_manager.get_source_directory_path()
        agent_file = os.path.join(source_dir, PR_AGENT_FILE_NAME)
        device_file = os.path.join(source_dir, PR_DEVICE_FILE_NAME)

        revisions, code = HTTP.get(self.env.project_manager.get_access_token(),
                                   PL_BUILD_API_URL_V5 + "models/" + model_id + "/revisions")
        if len(revisions["revisions"]) > 0:
            latest_revision_url = PL_BUILD_API_URL_V5 + "models/" + model_id + "/revisions/" + \
                                  str(revisions["revisions"][0]["version"])
            source, code = HTTP.get(self.env.project_manager.get_access_token(), latest_revision_url)
            with open(agent_file, "w", encoding="utf-8") as file:
                file.write(source["revision"]["agent_code"])
            with open(device_file, "w", encoding="utf-8") as file:
                file.write(source["revision"]["device_code"])
        else:
            # Create initial source files
            with open(agent_file, "w", encoding="utf-8") as file:
                file.write(STR_INITIAL_SRC_CONTENT.format("Agent"))
            with open(device_file, "w", encoding="utf-8") as file:
                file.write(STR_INITIAL_SRC_CONTENT.format("Device"))


class ImpAddDeviceToModel(BaseElectricImpCommand):
    def run(self):
        self.init_env_and_settings()

        def check_settings_callback():
            self.add_device(need_to_confirm=False)

        self.check_settings(callback=check_settings_callback)


class ImpRemoveDeviceFromModel(BaseElectricImpCommand):
    def run(self):
        self.init_env_and_settings()
        self.check_settings(callback=self.prompt_model_to_remove_device)

    def prompt_model_to_remove_device(self, need_to_confirm=True):
        if need_to_confirm and not sublime.ok_cancel_dialog(STR_MODEL_REMOVE_DEVICE): return

        model = self.load_this_model()
        device_ids = model.get("devices") if model else None

        if not device_ids or len(device_ids) == 0:
            sublime.message_dialog(STR_MODEL_NO_DEVICES_TO_REMOVE)
            return

        (Env.For(self.window).tmp_device_ids, device_names) = self.load_devices(input_device_ids=device_ids)
        self.window.show_quick_panel(device_names, self.on_remove_device_selected)

    def on_remove_device_selected(self, index):
        device_id = self.env.tmp_device_ids[index]
        active_device_id = self.load_settings().get(EI_DEVICE_ID)

        if device_id == active_device_id:
            sublime.message_dialog(STR_MODEL_CANT_REMOVE_ACTIVE_DEVICE)
            return

        response, code = HTTP.put(self.env.project_manager.get_access_token(),
                                  PL_BUILD_API_URL_V5 + "devices/" + device_id,
                                  '{"model_id": ""}')
        if not HTTP.is_response_code_valid(code):
            sublime.message_dialog(STR_MODEL_REMOVE_DEVICE_FAILED)
            return

        sublime.message_dialog(STR_MODEL_DEVICE_REMOVED)

        self.env.tmp_model = None
        self.env.tmp_device_ids = None


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
        # env.ui_manager.show_settings_value_in_status(EI_MODEL_NAME, PL_MODEL_STATUS_KEY, STR_STATUS_ACTIVE_MODEL)

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

    def __read_logs(self):
        if self.sock and type(self.sock) != None and self.sock.fp != None:
            next_log = False
            next_cmd = False
            logs = []
            while True:
                rd, wd, ed = select.select([self.sock], [], [], 1)
                if not rd:
                    break
                else:
                    for line in self.sock:
                        if next_log:
                            next_log = False
                            logs.append(line.decode("utf-8"))
                        if next_cmd:
                            next_cmd = False
                            if line == b'data: closed\n':
                                self.sock.close()
                                self.sock = None
                                logs.append("Connection closed ...")
                                break

                        if line == b'event: message\n':
                            next_log = True

                        if line == b'event: state_change\n':
                            next_cmd = True
                        if line == b'\n':
                            break
            return logs


    def query_logs(self):
        log_request_time = False
        devicegroup_id = self.env.project_manager.load_settings().get(EI_DEVICEGROUP_ID)

        if not devicegroup_id:
            # Nothing to do yet
            return None

        if self.sock and type(self.sock) != None and self.sock.fp != None:
            return {"logs": self.__read_logs()}

        logs = []

        # Request the list of the devices for the device group
        # on first connection and cache it for future
        if not self.poll_url:
            devices, rcode = HTTP.get(key=self.env.project_manager.get_access_token(),
                url=PL_BUILD_API_URL_V5 + "devices",
                data='{"filter": "'+ devicegroup_id +'"}',
                headers={"Content-Type": "application/vnd.api+json"})

            # Suppose that there is no logs if there is no device
            if not HTTP.is_response_code_valid(rcode) or len(devices["data"]) == 0:
                print(devices)
                return None

            # cache device list
            # it could be re-use on the next connection
            # and uses for smart log output
            self.devices = devices["data"]

        # request a new logstream instance
        response, code = HTTP.post(key=self.env.project_manager.get_access_token(), url=PL_BUILD_API_URL_V5 + "logstream", headers={"Content-Type": "application/vnd.api+json"})

        if HTTP.is_response_code_valid(code):
            self.poll_url = response["data"]["id"]
            url = PL_BUILD_API_URL_V5 + "logstream/" + self.poll_url
        else:
            # TODO: handle connection error or access-token expired
            return None

        hdr = {"Authorization": "Bearer " + self.env.project_manager.get_access_token(),
            "Content-Type": "text/event-stream",
            "User-Agent": "imp-developer/sublime"}

        req1 = urllib.request.Request(url=url, headers=hdr, method="GET")
        try:
            self.sock = urllib.request.urlopen(req1, timeout=None)
            logs = self.__read_logs()
        except socket.timeout:
            # open url timeout
            self.sock = None
        except urllib.error.HTTPError as err:
            # TODO: - handle expired access token
            #       - no internet connection
            self.sock = None

        # attache the devices from the device group to the logstream
        for device in self.devices:
            response, code = HTTP.put(key=self.env.project_manager.get_access_token(),
                url=PL_BUILD_API_URL_V5 + "logstream/" + self.poll_url + "/" + device["id"],
                data="{}")
        start = None
        if log_request_time:
            start = datetime.datetime.now()

        if log_request_time:
            elapsed = datetime.datetime.now() - start
            log_debug("Time spent in calling the url: " + url + " is: " + str(elapsed))

        logs = logs + (self.__read_logs());
        return {"logs": logs}


    @staticmethod
    def get_poll_url(logs_json):
        return self.poll_url

    @staticmethod
    def logs_are_equal(first, second):
        return first == second

    @staticmethod
    def logs_are_equal2(first, second):
        return first["type"] == second["type"] and \
               first["message"] == second["message"] and \
               first["timestamp"] == second["timestamp"]

    def update_logs(self):
        def __update_logs():
            logs_json = self.query_logs()
            # no logs available
            if not logs_json:
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

        if len(ms) < 5 or ms.pop(0) != "data:":
            res["device"] = "sublime"
            res["dt"] = datetime.datetime.now()
            res["type"] = "sublime.log"
            res["deployment"] = ""
            res["message"] = log
        else:
            res["device"] = ms.pop(0)
            res["dt"] = datetime.datetime.strptime(ms.pop(0), "%Y-%m-%dT%H:%M:%S.%fZ")
            res["deployment"] = ms.pop(0)
            res["type"] = ms.pop(0)
            res["message"] = " ".join(ms)[:-1]

        return res

    def write_to_console(self, log):
        message = self.__parse_log(log)
        if not message:
            return

        # self.convert_line_numbers(log)
        self.env.ui_manager.write_to_console(message["dt"].strftime('%Y-%m-%d %H:%M:%S%z')
            + " [" + message["device"] + "] " + message["type"] + " " + message["message"])

    def reset(self):
        self.poll_url = None
        self.last_shown_log = None

def update_log_windows(restart_timer=True):
    global project_env_map
    try:
        for (project_path, env) in list(project_env_map.items()):
            # Clean up project windows first
            if not ProjectManager.is_electric_imp_project_window(env.window):
                # It's not a windows that corresponds to an EI project, remove it from the list
                del project_env_map[project_path]
                log_debug("Removing project window: " + str(env.window) + ", total #: " + str(len(project_env_map)))
                continue
            env.log_manager.update_logs()
    finally:
        if restart_timer:
            sublime.set_timeout_async(update_log_windows, PL_LOGS_UPDATE_PERIOD)
