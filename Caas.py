import sublime
import sublime
import sublime_plugin
import re
import subprocess
import os
import fcntl

try:  # Python 3
    from NimLime.Project import Utility
except ImportError:  # Python 2:
    from Project import Utility

ActiveCaas = None
ActiveProject = None

def get_caas_for_project(project_file):
    global ActiveProject
    global ActiveCaas
    if project_file == None:
        return None
    if project_file == ActiveProject:
        return ActiveCaas
    # create a new Caas
    stop_active_caas()
    ActiveProject = project_file
    ActiveCaas = Caas(project_file)
    ActiveCaas.start_service()
    return ActiveCaas

def stop_active_caas():
    global ActiveProject
    global ActiveCaas
    if ActiveProject != None:
        ActiveCaas.stop_service()
        ActiveCaas = None
        ActiveProject = None

class Caas:
    service = None # CAAS connection
    project_file = None # Main project file

    def __init__(self, project_file):
        self.project_file = project_file

    def __del__(self):
        self.stop_service()

    # Methods
    def start_service(self):
        # If service is running, do nothing
        if self.service is not None:
            return
        self.service = subprocess.Popen(
            ["nimrod", "serve", "--server.type:stdin", "\"" + self.project_file + "\""],
            bufsize = -1,
            stdout = subprocess.PIPE,
            stdin = subprocess.PIPE,
            stderr = subprocess.STDOUT #subprocess.PIPE
        )

        print("Nimrod CaaS for project " + self.project_file + " now running")

    def stop_service(self):
        if self.service != None:
            self.service.terminate()
            self.service = None
            print("Nimrod CaaS for project " + self.project_file + " was stopped")

    def send_command(self, cmd, filename, line, col, dirtyFile = "", extra = ""):
        if self.service == None: return False

        trackType = " --track:"
        filePath = filename
        
        projFile = self.project_file
        if projFile == None or projFile == "":
            projFile = filename

        if dirtyFile != "":
            trackType = " --trackDirty:"
            filePath = dirtyFile + "," + filename        

        # Call the service
        args = "idetools" \
            + trackType \
            + "\"" + filePath + "," + str(line) + "," + str(col) + "\" " \
            + cmd + extra + "\n"

        print(args)
        try:
            self.service.stdin.write(args.encode("UTF-8"))
            self.service.stdin.flush()
        except: # Stop the active service to make a reload possible
            self.stop_service()
            stop_active_caas()
            return False
        return True

    def read_line(self):
        try:
            return self.service.stdout.readline()
        except Exception as e: # Stop the active service to make a reload possible
            self.stop_service()
            stop_active_caas()
            return "\n".encode("UTF-8")
