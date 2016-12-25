#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 23 15:29:52 2016

@author: pavel
"""

from gi.repository import Gio
import subprocess

# Should be launched with root privileges,
# so some dirty solution
   
class Editor:
    MODES = {"normal"         : "",
             "full"           : "--full" }    
    
    command_template = """pkexec env DISPLAY=$DISPLAY \
    XAUTHORITY=$XAUTHORITY \
    SYSTEMD_EDITOR={editor} \
    systemctl edit {mode} {unit_id}"""
    

    def __init__(self, on_close):
        self.on_close = on_close        
        self.editor = Editor.get_default_text_editor()
        #os.putenv("SYSTEMD_EDITOR", editor)
        
    def run_editor(self, unit_id, mode_name = "normal"):        
        mode = Editor.MODES.get(mode_name, Editor.MODES["normal"])
        
        
        command = Editor.command_template.format(editor=self.editor,
                                                 mode = mode, 
                                                 unit_id = unit_id)    
        #os.system(command)
        subprocess.call(command, shell=True)
        
        self.on_close(unit_id)
        
    @staticmethod    
    def get_default_text_editor():    
        app = Gio.AppInfo.get_default_for_type("text/plain", False)
        editor = app.get_executable()
        return editor or "gedit"

        
        
#launcher = Editor(print)
#launcher.run_editor("miredo", "full")