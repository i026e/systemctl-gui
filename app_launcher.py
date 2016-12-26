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

def get_default_text_editor():    
    app = Gio.AppInfo.get_default_for_type("text/plain", False)
    editor = app.get_executable()
    return editor or "gedit"
    
def get_default_browser():
    return  Gio.AppInfo.get_default_for_uri_scheme("http").get_executable()
   
class Editor:
    MODES = {"normal"         : "",
             "full"           : "--full" }    
    
    command_template = """pkexec env DISPLAY=$DISPLAY \
    XAUTHORITY=$XAUTHORITY \
    SYSTEMD_EDITOR={editor} \
    systemctl edit {mode} {unit_id}"""
    

    @staticmethod    
    def run_editor(on_close, unit_id, mode_name = "normal"):
        editor = get_default_text_editor()         
        mode = Editor.MODES.get(mode_name, Editor.MODES["normal"])
        
        
        command = Editor.command_template.format(editor=editor,
                                                 mode = mode, 
                                                 unit_id = unit_id)    
        #os.system(command)
        subprocess.call(command, shell=True)
        
        on_close(unit_id)
        
        
class Browser:
    man_command = """man --html={browser} {page}"""
    
    @staticmethod
    def open_man(on_close, man_page):
        browser = get_default_browser()
        command = Browser.man_command.format(browser=browser, page=man_page)
        subprocess.call(command, shell=True)
        
        on_close(man_page)
    
    @staticmethod    
    def systemctl_man(on_close):
        Browser.open_man(on_close, "systemctl")

        
#launcher = Editor(print)
#launcher.run_editor("miredo", "full")