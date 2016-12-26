#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 13:41:48 2016

@author: pavel
"""
import subprocess
from utils import logger

ALLOWED_ACTIONS = { "enable"                : (("enable",),"Enable unit file"),
                    "disable"               : (("disable",),"Disable unit file"),
                    "reenable"              : (("reenable",),"Reenable unit file"),
                    "preset"                : (("preset",),"Enable/disable unit file based on preset configuration"),
                    "start"                 : (("start",),"Start (activate) unit"),
                    "stop"                  : (("stop",),"Stop (deactivate) unit"),
                    "reload"                : (("reload",),"Reload unit"),
                    "restart"               : (("restart",),"Start or restart unit"),
                    "try-restart"           : (("try-restart",),"Restart unit if active"),
                    "reload-or-restart"     : (("reload-or-restart",),"Reload unit if possible, otherwise start or restart"),
                    "try-reload-or-restart" : (("try-reload-or-restart",),"If active, reload unit, if supported, otherwise restart"),
                    "isolate"               : (("isolate",),"Start unit and stop all others"),
                    "kill"                  : (("kill",),"Send signal to processes of a unit"),
                    }

def escape(string):
    return string.replace("&", "&amp;")   

def run_command(*args):
    output = ""
    try:
        process = subprocess.Popen(args,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines = True)
        return_code = process.wait() 
        output = process.stdout.read()

        logger.debug("%s : code %s \n stdout=\n %s \n\n", process.args, 
                     return_code, output)
    except Exception as e:
        logger.error(e)
    finally:
        return escape(output.strip()) 
        
def list_units():
    out = run_command("systemctl", "list-unit-files")
    
    units_list = []
    for line in out.split("\n")[1:-2]:
        line = line.strip()
        if len(line) > 0:
            try:
                unit, status = line.split()                
                units_list.append((unit, status))
            except Exception as e:
                logger.error(e)
                
    return units_list
    
def get_status(unit_id):
    return run_command("systemctl", "status", unit_id)
    
def get_content(unit_id):
    return run_command("systemctl", "cat", unit_id)
    
def get_description(unit_id):
    data = get_status(unit_id).split("\n")    
    try:    
        descr = data[0].split(" - ")[-1].strip()
    except Exception as e:
        logger.error(e)
        descr = unit_id
    finally:
        return descr 
        
def get_dependencies(unit_id):
    return run_command("systemctl", "list-dependencies", unit_id).strip()   
    
def get_properties(unit_id):
    return run_command("systemctl", "show", unit_id).strip()  
    
def is_enabled(unit_id):
    val = run_command("systemctl", "is-enabled", "--value", unit_id)
    return "enabled" == val.strip()
    
def is_active(unit_id):
    val = run_command("systemctl", "is-active", "--value", unit_id)
    return "active" == val.strip()
    
def execute(unit_id, action_name):
    if action_name in ALLOWED_ACTIONS:
        action = ALLOWED_ACTIONS.get(action_name)[0]
        return run_command("systemctl", *action, unit_id)
    else:
        logger.error("%s unknown action: %s", unit_id, action_name)

def daemon_reload():
    return run_command("systemctl", "daemon−reload")
    
def get_systemctl_version():
    return run_command("systemctl", "--version")