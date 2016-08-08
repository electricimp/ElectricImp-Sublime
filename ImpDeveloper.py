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

EI_BUILD_URL          = "https://build.electricimp.com/v4/"
PLUGIN_SETTINGS_FILE  = "ImpDeveloper.sublime-settings"
DEBUG_FLAG            = "debug"

EI_BUILD_API_KEY      = "build-api-key"
EI_MODEL_ID           = "model-id"
EI_DEVICE_FILE        = "device-file"
EI_AGENT_FILE         = "agent-file"
EI_DEVICE_ID          = "device-id"

DEFAULT_PROJECT_NAME  = "ei-project"
TEMPLATE_DIR_NAME     = "project-template"
PROJECT_FILE_TEMPLATE = "_project_name_.sublime-project"

settings = None
project_windows = []

class BaseElectricImpCommand(sublime_plugin.WindowCommand):

	def __init__(self, window):
		self.window = window

	def base64_encode(self, str):
		return base64.b64encode(str.encode()).decode()

	def get_http_headers(self, build_api_key):
		return {
			"Authorization" : "Basic " + self.base64_encode(build_api_key),
			"Content-Type" : "application/json"
		}

	def get_ei_settings_file_name(self):
		project_file_name = self.window.project_file_name()
		if project_file_name:
			project_dir = os.path.dirname(project_file_name)
			settings_file_name = os.path.join(
				project_dir, 
				os.path.basename(os.path.splitext(project_file_name)[0]) + ".electric-imp-settings")
			return settings_file_name
		return None

	def is_electric_imp_project(self):
		settings_file_name = self.get_ei_settings_file_name()
		return settings_file_name is not None and os.path.exists(settings_file_name)

	def init_tty(self):
		global project_windows
		if self.window not in project_windows and self.is_electric_imp_project():
			ei_settings = self.load_ei_settings()
			# Prompt for device if it wasn't selected yet
			if EI_DEVICE_ID not in ei_settings:
				decision = sublime.ok_cancel_dialog("Please select a device to display the logs for")
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

	def prompt_for_device(self):
		ei_settings = self.load_ei_settings()
		url = EI_BUILD_URL + "models/" + ei_settings.get(EI_MODEL_ID)
		response = requests.get(url, headers=self.get_http_headers(ei_settings.get(EI_BUILD_API_KEY))).json()
		self.device_ids = response.get("model").get("devices")
		self.window.show_quick_panel(self.device_ids, self.on_device_selected)

	def on_device_selected(self, index):
		ei_settings = self.load_ei_settings()
		ei_settings[EI_DEVICE_ID] = self.device_ids[index]
		self.save_ei_settings(ei_settings)

	def save_ei_settings(self, ei_settings):
		with open(self.get_ei_settings_file_name(), "w") as settings_file:
			json.dump(ei_settings, settings_file)

	def load_ei_settings(self):
		file_name = self.get_ei_settings_file_name()
		if file_name:
			with open(file_name) as file:    
				return json.load(file)

	def get_logs_timestamp(self):
		return self.window.terminal.logs_timestamp

	def set_logs_timestamp(self, timestamp):
		self.window.terminal.logs_timestamp = timestamp

	def log_debug(self, text):
		global settings
		if settings.get(DEBUG_FLAG) == True:
			print("  [ElectricImp] " + text)

class ImpPushCommand(BaseElectricImpCommand):
	def run(self):
		self.init_tty()
		ei_settings = self.load_ei_settings()
		project_dir = os.path.dirname(self.window.project_file_name())

		agent_file_name  = os.path.join(project_dir, ei_settings.get(EI_AGENT_FILE))
		device_file_name = os.path.join(project_dir, ei_settings.get(EI_DEVICE_FILE))

		if not os.path.exists(agent_file_name) or not os.path.exists(device_file_name):
			self.log_debug("Can't find code files")
			sublime.message_dialog("Code files for agent and device are absent. Please check the project settings: " + 
				self.get_ei_settings_file_name())

		agent_code  = self.read_file(agent_file_name)
		device_code = self.read_file(device_file_name)

		url = EI_BUILD_URL + "models/" + ei_settings.get(EI_MODEL_ID) + "/revisions"
		data = '{"agent_code": ' + json.dumps(agent_code) + ', "device_code" : ' + json.dumps(device_code) + ' }'
		response = requests.post(url, data=data, headers=self.get_http_headers(ei_settings.get(EI_BUILD_API_KEY))).json()
		self.tty("Revision uploaded: " + str(response["revision"]["version"]))

		url = EI_BUILD_URL + "models/" + ei_settings.get(EI_MODEL_ID) + "/restart"
		response = requests.post(url, headers=self.get_http_headers(ei_settings.get(EI_BUILD_API_KEY)))

	def is_enabled(self):
		return self.is_electric_imp_project()

	def read_file(self, filename):
		with open(filename) as f: s = f.read()
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
		self.window.show_input_panel("New Electric Imp Project Location:", 
			self.default_project_path, self.on_project_path_entered, None, None)		

	def get_default_project_path(self):
		default_project_path_setting = settings.get("default_project_path")
		default_project_path = None
		if not default_project_path_setting:
			if sublime.platform() == "windows":
				default_project_path = os.path.expanduser("~\\" + DEFAULT_PROJECT_NAME).replace("\\", "/")
			else:
				default_project_path = os.path.expanduser("~/" + DEFAULT_PROJECT_NAME)
		else:
			default_project_path = default_project_path_setting
		return default_project_path 

	def on_project_path_entered(self, path):
		self.log_debug("Project path specified: " + path)
		self.project_path = path

		if os.path.exists(path):
			if not sublime.ok_cancel_dialog(
				"Something already exists at " + path + ". Do you want to create project in that folder?"):
				return
		self.prompt_build_api_key()

	def prompt_build_api_key(self):
		self.window.show_input_panel("Electric Imp Build API key:", 
			"", self.on_build_api_key_entered, None, None)		
	
	def on_build_api_key_entered(self, key):
		self.log_debug("build api key entered: " + key)
		self.build_api_key = key
		if self.build_api_key_is_valid(key):
			self.log_debug("build API key is valid")
			self.prompt_for_model()
		else:
			if sublime.ok_cancel_dialog("Build API key is invalid. Try another one?"):
				self.prompt_build_api_key()

	def prompt_for_model(self):
		response = requests.get(EI_BUILD_URL + "models", headers=self.get_http_headers(self.build_api_key)).json()
		if (len(response["models"]) > 0):
			if not sublime.ok_cancel_dialog("Please select one of the available Models for the project"):
				return
			self.all_model_names = [model["name"] for model in response["models"]]
			self.all_model_ids = [model["id"] for model in response["models"]]
		else:
			sublime.message_dialog(
				"There are no models registered in the system. " +
				"Please register one from the developer console and try again."
			)
			return

		self.window.show_quick_panel(self.all_model_names, self.on_model_choosen)

	def on_model_choosen(self, index):
		self.model_id = self.all_model_ids[index]
		self.model_name = self.all_model_names[index]

		self.log_debug("model choosen (name, id): (" + self.model_name + ", " + self.model_id + ")")
		self.create_project()

	def create_project(self):
		self.log_debug("Creating project at:" + self.project_path)
		try:
			os.stat(self.project_path)
		except:
			os.mkdir(self.project_path)

		self.copy_project_template_file(PROJECT_FILE_TEMPLATE)

		# Create Electric Imp project settings file
		settings_file_name = dst = os.path.join(self.project_path, 
			os.path.basename(self.project_path) + ".electric-imp-settings");
		settings = {
			EI_BUILD_API_KEY : self.build_api_key,
			EI_MODEL_ID      : self.model_id,
			EI_DEVICE_FILE   : self.model_name + ".device.nut",
			EI_AGENT_FILE    : self.model_name + ".agent.nut"
		}
		with open(settings_file_name, "w") as settings_file:
			json.dump(settings, settings_file)

		self.pull_model_revision()
		self.window.run_command("open_dir", {"dir":self.project_path})

	def copy_project_template_file(self, filename):
		src = os.path.join(self.get_template_dir(), filename)
		dst = os.path.join(self.project_path, 
			filename.replace("_project_name_", os.path.basename(self.project_path)))
		shutil.copy(src, dst)
   
	def pull_model_revision(self):
		agent_file  = os.path.join(self.project_path, self.model_name + ".agent.nut")
		device_file = os.path.join(self.project_path, self.model_name + ".device.nut")

		revisions = requests.get(
			EI_BUILD_URL + "models/" + self.model_id + "/revisions", 
			headers=self.get_http_headers(self.build_api_key)).json()
		if len(revisions["revisions"]) > 0:
			latest_revision_url = EI_BUILD_URL + "models/" + self.model_id + "/revisions/" + \
								  str(revisions["revisions"][0]["version"]);
			code = requests.get(
				latest_revision_url, 
				headers=self.get_http_headers(self.build_api_key)).json()
			with open(agent_file, "w") as file:
				file.write(code["revision"]["agent_code"])
			with open(device_file, "w") as file:
				file.write(code["revision"]["device_code"])
		else:
			# Create empty files
			open(agent_file,  'a').close()
			open(device_file, 'a').close()

	def get_template_dir(self):
		return os.path.join(os.path.dirname(os.path.realpath(__file__)), TEMPLATE_DIR_NAME)

	def build_api_key_is_valid(self, key):
		return requests.get(EI_BUILD_URL + "models", 
			headers=self.get_http_headers(key)).status_code == 200

def plugin_loaded():
	global settings
	settings = sublime.load_settings(PLUGIN_SETTINGS_FILE)

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
			ei_settings = eiCommand.load_ei_settings()
			device_id   = ei_settings.get(EI_DEVICE_ID)
			timestamp   = eiCommand.get_logs_timestamp()
			if device_id is None or timestamp is None:
				# Device is not selected yet and the console is not setup for the project, nothing to do
				continue
			url = EI_BUILD_URL + "devices/" + ei_settings.get(EI_DEVICE_ID) + "/logs?since=" + urllib.parse.quote(timestamp)
			response = requests.get(url, headers=eiCommand.get_http_headers(ei_settings.get(EI_BUILD_API_KEY))).json()
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
