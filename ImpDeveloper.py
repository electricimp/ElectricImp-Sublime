import os
import sys
import sublime
import sublime_plugin
import json
import base64
import shutil
import sched
import time
import datetime
import urllib

# request-dists is the folder in our plugin
sys.path.append(os.path.join(os.path.dirname(__file__), "requests"))

import requests

# Plugin specific constants
PL_BUILD_API_URL         = "https://build.electricimp.com/v4/"
PL_SETTINGS_FILE         = "ImpDeveloper.sublime-settings"
PL_DEBUG_FLAG            = "debug"

# Electric Imp project specific constants
PR_DEFAULT_PROJECT_NAME  = "electric-imp-project"
PR_TEMPLATE_DIR_NAME     = "project-template"
PR_PROJECT_FILE_TEMPLATE = "_project_name_.sublime-project"
PR_SETTINGS_FILE         = "electric-imp.settings"
PR_BUILD_API_KEY_FILE    = "build-api.key"
PR_SOURCE_DIRECTORY      = "src"
PR_SETTINGS_DIRECTORY    = "settings"

# Electric Imp settings and project properties
EI_BUILD_API_KEY         = "build-api-key"
EI_MODEL_ID              = "model-id"
EI_DEVICE_FILE           = "device-file"
EI_AGENT_FILE            = "agent-file"
EI_DEVICE_ID             = "device-id"

# String constants that are visible for users
STR_SELECT_DEVICE        = "Please select a device to display the logs for"
STR_CODE_IS_ABSENT       = "Code files for agent or device are absent. Please check the project settings at {}"
STR_NEW_PROJECT_LOCATION = "New Electric Imp Project Location:"
STR_FOLDER_EXISTS        = "Something already exists at {}. Do you want to create project in that folder?"
STR_BUILD_API_KEY        = "Electric Imp Build API key:"
STR_INVALID_API_KEY      = "Build API key is invalid. Please try another one."
STR_SELECT_MODEL         = "Please select one of the available Models for the project"
STR_NO_MODELS_AVAILABLE  = "There are no models registered in the system. Please register one from the developer console and try again."

# Global variables
plugin_settings = None
project_windows = []

class BaseElectricImpCommand(sublime_plugin.WindowCommand):

	def __init__(self, window):
		self.window = window

	def base64_encode(self, str):
		return base64.b64encode(str.encode()).decode()

	def get_http_headers(self, key=None):
		build_api_key = key if key is not None else self.get_build_api_key()
		return {
			"Authorization" : "Basic " + self.base64_encode(build_api_key),
			"Content-Type" : "application/json"
		}

	def get_settings_dir(self):
		project_file_name = self.window.project_file_name()
		if project_file_name:
			project_dir = os.path.dirname(project_file_name)
			return os.path.join(project_dir, PR_SETTINGS_DIRECTORY)

	def get_settings_file_path(self, filename):
		settings_dir = self.get_settings_dir()
		if settings_dir and filename:
			return os.path.join(settings_dir, filename)

	def is_electric_imp_project(self):
		settings_filename = self.get_settings_file_path(PR_SETTINGS_FILE)
		return settings_filename is not None and os.path.exists(settings_filename)

	def init_tty(self):
		global project_windows
		if self.window not in project_windows and self.is_electric_imp_project():
			settings = self.load_settings(PR_SETTINGS_FILE)
			# Prompt for device if it wasn't selected yet
			if EI_DEVICE_ID not in settings:
				decision = sublime.ok_cancel_dialog(STR_SELECT_DEVICE)
				if decision:
					self.prompt_for_device()
				else:
					return
			self.window.terminal = self.window.get_output_panel("textarea")
			self.window.terminal.logs_timestamp = "2000-01-01T00:00:00.000+00:00"
			project_windows.append(self.window)
			self.log_debug("adding new project window: " + str(self.window) + ", total windows now: " + str(len(project_windows)))
		self.window.run_command("show_panel", {"panel": "output.textarea"})

	def tty(self, text):
		global project_windows
		if self.window in project_windows:
			terminal = self.window.terminal
			terminal.set_read_only(False)
			terminal.run_command("append", {"characters": text + "\n"})
			terminal.set_read_only(True)
		else:
			print(text);

	def get_build_api_key(self):
		api_key_map = self.load_settings(PR_BUILD_API_KEY_FILE)
		if api_key_map:
			return api_key_map.get(EI_BUILD_API_KEY)

	def prompt_for_device(self):
		url = PL_BUILD_API_URL + "models/" + self.load_settings(PR_SETTINGS_FILE).get(EI_MODEL_ID)
		response = requests.get(url, headers=self.get_http_headers()).json()
		self.__tmp_device_ids = response.get("model").get("devices")
		self.window.show_quick_panel(self.__tmp_device_ids, self.on_device_selected)

	def on_device_selected(self, index):
		settings = self.load_settings(PR_SETTINGS_FILE)
		settings[EI_DEVICE_ID] = self.__tmp_device_ids[index]
		self.save_settings(PR_SETTINGS_FILE, settings)
		# Clean up temporary variables
		self.__tmp_device_ids = None

	def dump_map_to_json_file(self, filename, map):
		with open(filename, "w") as file:
			json.dump(map, file)

	def save_settings(self, filename, settings):
		self.dump_map_to_json_file(self.get_settings_file_path(filename), settings)

	def load_settings(self, filename):
		path = self.get_settings_file_path(filename)
		if path:
			with open(path) as file:
				return json.load(file)

	def get_logs_timestamp(self):
		return self.window.terminal.logs_timestamp

	def set_logs_timestamp(self, timestamp):
		self.window.terminal.logs_timestamp = timestamp

	def log_debug(self, text):
		global plugin_settings
		if plugin_settings.get(PL_DEBUG_FLAG) == True:
			print("  [ElectricImp] " + text)

class ImpPushCommand(BaseElectricImpCommand):
	def run(self):
		self.init_tty()
		settings = self.load_settings(PR_SETTINGS_FILE)

		source_dir = os.path.join(os.path.dirname(self.window.project_file_name()), PR_SOURCE_DIRECTORY)
		agent_filename  = os.path.join(source_dir, settings.get(EI_AGENT_FILE))
		device_filename = os.path.join(source_dir, settings.get(EI_DEVICE_FILE))

		if not os.path.exists(agent_filename) or not os.path.exists(device_filename):
			self.log_debug("Can't find code files")
			sublime.message_dialog(STR_CODE_IS_ABSENT.format(self.get_settings_file_path(PR_SETTINGS_FILE)))

		agent_code  = self.read_file(agent_filename)
		device_code = self.read_file(device_filename)

		url = PL_BUILD_API_URL + "models/" + settings.get(EI_MODEL_ID) + "/revisions"
		data = '{"agent_code": ' + json.dumps(agent_code) + ', "device_code" : ' + json.dumps(device_code) + ' }'
		response = requests.post(url, data=data, headers=self.get_http_headers()).json()
		self.tty("Revision uploaded: " + str(response["revision"]["version"]))

		url = PL_BUILD_API_URL + "models/" + settings.get(EI_MODEL_ID) + "/restart"
		response = requests.post(url, headers=self.get_http_headers())

	def is_enabled(self):
		return self.is_electric_imp_project()

	def read_file(self, filename):
		with open(filename, 'r', encoding="utf-8") as f:
			s = f.read()
		return s

class ImpShowConsoleCommand(BaseElectricImpCommand):
	def run(self):
		self.init_tty()

	def is_enabled(self):
			return self.is_electric_imp_project()

class ImpSelectDeviceCommand(BaseElectricImpCommand):
	def run(self):
		self.prompt_for_device()

	def is_enabled(self):
			return self.is_electric_imp_project()

class ImpCreateProjectCommand(BaseElectricImpCommand):
	def run(self):
		self.init_tty()
		self.default_project_path = self.get_default_project_path()
		self.window.show_input_panel(STR_NEW_PROJECT_LOCATION, self.default_project_path, self.on_project_path_entered, None, None)		

	def get_default_project_path(self):
		default_project_path_setting = settings.get("default_project_path")
		default_project_path = None
		if not default_project_path_setting:
			if sublime.platform() == "windows":
				default_project_path = os.path.expanduser("~\\" + PR_DEFAULT_PROJECT_NAME).replace("\\", "/")
			else:
				default_project_path = os.path.expanduser("~/" + PR_DEFAULT_PROJECT_NAME)
		else:
			default_project_path = default_project_path_setting
		return default_project_path 

	def on_project_path_entered(self, path):
		self.log_debug("Project path specified: " + path)
		self.__tmp_project_path = path

		if os.path.exists(path):
			if not sublime.ok_cancel_dialog(STR_FOLDER_EXISTS.format(path)):
				return
		self.prompt_build_api_key()

	def prompt_build_api_key(self):
		self.window.show_input_panel(STR_BUILD_API_KEY,
			"", self.on_build_api_key_entered, None, None)

	def on_build_api_key_entered(self, key):
		self.log_debug("build api key provided: " + key)
		if self.build_api_key_is_valid(key):
			self.log_debug("build API key is valid")
			self.__tmp_build_api_key = key
			self.prompt_for_model()
		else:
			if sublime.ok_cancel_dialog(STR_INVALID_API_KEY):
				self.prompt_build_api_key()

	def prompt_for_model(self):
		response = requests.get(PL_BUILD_API_URL + "models", headers=self.get_http_headers(self.__tmp_build_api_key)).json()
		if (len(response["models"]) > 0):
			if not sublime.ok_cancel_dialog(STR_SELECT_MODEL):
				return
			self.__tmp_all_model_names = [model["name"] for model in response["models"]]
			self.__tmp_all_model_ids = [model["id"] for model in response["models"]]
		else:
			sublime.message_dialog(STR_NO_MODELS_AVAILABLE)
			return

		self.window.show_quick_panel(self.__tmp_all_model_names, self.on_model_choosen)

	def on_model_choosen(self, index):
		self.__tmp_model_id = self.__tmp_all_model_ids[index]
		self.__tmp_model_name = self.__tmp_all_model_names[index]

		self.log_debug("model choosen (name, id): (" + self.__tmp_model_name + ", " + self.__tmp_model_id + ")")
		self.create_project()

	def create_project(self):
		source_dir = os.path.join(self.__tmp_project_path, PR_SOURCE_DIRECTORY)
		settings_dir = os.path.join(self.__tmp_project_path, PR_SETTINGS_DIRECTORY)

		self.log_debug("Creating project at:" + self.__tmp_project_path)
		if not os.path.exists(source_dir):
			os.makedirs(source_dir)
		if not os.path.exists(settings_dir):
			os.makedirs(settings_dir)

		self.copy_project_template_file(PR_PROJECT_FILE_TEMPLATE)

		# Create Electric Imp project settings file
		self.dump_map_to_json_file(os.path.join(settings_dir, PR_SETTINGS_FILE), {
			EI_MODEL_ID      : self.__tmp_model_id,
			EI_DEVICE_FILE   : self.__tmp_model_name + ".device.nut",
			EI_AGENT_FILE    : self.__tmp_model_name + ".agent.nut"
		})

		# Create Electric Imp project settings file
		self.dump_map_to_json_file(os.path.join(settings_dir, PR_BUILD_API_KEY_FILE), {
			EI_BUILD_API_KEY : self.__tmp_build_api_key
		})

		# Pull the latest code revision from the server
		self.pull_model_revision()

		# Open the project in the file browser
		self.window.run_command("open_dir", {"dir":self.__tmp_project_path})

		# Clean up all temporary variables
		self.__tmp_model_id = None
		self.__tmp_model_name = None
		self.__tmp_project_path = None
		self.__tmp_all_model_ids = None
		self.__tmp_build_api_key = None
		self.__tmp_all_model_names = None

	def copy_project_template_file(self, filename):
		src = os.path.join(self.get_template_dir(), filename)
		dst = os.path.join(self.__tmp_project_path, 
			filename.replace("_project_name_", os.path.basename(self.__tmp_project_path)))
		shutil.copy(src, dst)
   
	def pull_model_revision(self):
		source_dir  = os.path.join(self.__tmp_project_path, PR_SOURCE_DIRECTORY)
		agent_file  = os.path.join(source_dir, self.__tmp_model_name + ".agent.nut")
		device_file = os.path.join(source_dir, self.__tmp_model_name + ".device.nut")

		revisions = requests.get(
			PL_BUILD_API_URL + "models/" + self.__tmp_model_id + "/revisions", 
			headers=self.get_http_headers(self.__tmp_build_api_key)).json()
		if len(revisions["revisions"]) > 0:
			latest_revision_url = PL_BUILD_API_URL + "models/" + self.__tmp_model_id + "/revisions/" + \
								  str(revisions["revisions"][0]["version"]);
			code = requests.get(
				latest_revision_url, 
				headers=self.get_http_headers(self.__tmp_build_api_key)).json()
			with open(agent_file, "w", encoding="utf-8") as file:
				file.write(code["revision"]["agent_code"])
			with open(device_file, "w", encoding="utf-8") as file:
				file.write(code["revision"]["device_code"])
		else:
			# Create empty files
			open(agent_file,  'a').close()
			open(device_file, 'a').close()

	def get_template_dir(self):
		return os.path.join(os.path.dirname(os.path.realpath(__file__)), PR_TEMPLATE_DIR_NAME)

	def build_api_key_is_valid(self, key):
		return requests.get(PL_BUILD_API_URL + "models", 
			headers=self.get_http_headers(key)).status_code == 200

def plugin_loaded():
	global plugin_settings
	plugin_settings = sublime.load_settings(PL_SETTINGS_FILE)

def update_log_windows():
	global project_windows
	try:
		for window in project_windows:
			eiCommand = BaseElectricImpCommand(window)
			if not eiCommand.is_electric_imp_project():
				# It's not a windows that corresponds to an EI project, remove it from the list
				project_windows.remove(window)
				eiCommand.log_debug("Removing window from the windows project: " + str(window) + ", total windows now: " + str(len(project_windows)))
				continue
			device_id = eiCommand.load_settings(PR_SETTINGS_FILE).get(EI_DEVICE_ID)
			timestamp = eiCommand.get_logs_timestamp()
			build_key = eiCommand.get_build_api_key()
			if device_id is None or timestamp is None:
				# Device is not selected yet and the console is not setup for the project, nothing to do
				continue
			url = PL_BUILD_API_URL + "devices/" + device_id + "/logs?since=" + urllib.parse.quote(timestamp)
			response = requests.get(url, headers=eiCommand.get_http_headers(build_key)).json()
			log_size = len(response["logs"])
			if "logs" in response and log_size > 0:
				timestampt = response["logs"][log_size - 1]["timestamp"]
				eiCommand.set_logs_timestamp(timestampt)

				for log in response["logs"]:
					try:
						type = {
							"status"       : "[Status]",
							"server.log"   : "[Device]",
							"server.error" : "[Error]"
						} [log["type"]]
					except:
						eiCommand.log_debug("Unrecognized log type: " + log["type"])
						type = "[Log]"
					eiCommand.tty(log["timestamp"] + " " + type + " " + log["message"])
	finally:
		sublime.set_timeout_async(update_log_windows, 1000)

update_log_windows()
