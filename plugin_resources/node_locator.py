import os


class NodeLocator:
    def __init__(self, platform):
        self.platform = platform

    def get_root_nodejs_dir_path(self):
        result = None
        if self.platform == "windows":
            path64 = "C:\\Program Files (x86)\\nodejs\\"
            path32 = "C:\\Program Files\\nodejs\\"
            if os.path.exists(path64):
                result = path64
            elif os.path.exists(path32):
                result = path32
        elif self.platform in ["linux", "osx"]:
            bin_dir = "bin/node"
            js_dir1 = "/usr/local/nodejs/"
            js_dir2 = "/usr/local/"
            if os.path.exists(os.path.join(js_dir1, bin_dir)):
                result = js_dir1
            elif os.path.exists(os.path.join(js_dir2, bin_dir)):
                result = js_dir2
        return result

    def get_node_path(self):
        if self.platform == "windows":
            return self.get_root_nodejs_dir_path() + "node.exe"
        elif self.platform in ["linux", "osx"]:
            return self.get_root_nodejs_dir_path() + "bin/node"

    def get_builder_cli_path(self):
        if self.platform == "windows":
            home = os.path.expanduser("~")
            return os.path.join(home, "Application Data", "npm", "node_modules", "Builder", "src", "cli.js")
        elif self.platform in ["linux", "osx"]:
            return self.get_root_nodejs_dir_path() + "lib/node_modules/Builder/src/cli.js"
