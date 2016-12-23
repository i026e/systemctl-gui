#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 13:41:48 2016

@author: pavel
"""
import subprocess
import logging

APP = "mime-editor-gui"
Logger = logging.getLogger(APP)
Logger.setLevel(logging.DEBUG)

def run_command(*args):
    process = subprocess.Popen(args,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           universal_newlines = True)
    return_code = process.wait()
    #Logger.debug("return code %s", return_code)
    
    return process.stdout.read()

def list_units():
    out = run_command("systemctl", "list-unit-files")
    out.strip()
    
    units_list = []
    for line in out.split("\n")[1:-2]:
        line = line.strip()
        if len(line) > 0:
            try:
                unit, status = line.split()                
                units_list.append((unit, status))
            except Exception as e:
                Logger.error(e)
                
    return units_list
    
def get_status(unit_id):
    return run_command("systemctl", "status", unit_id).strip()
    
def get_description(unit_id):
    data = get_status(unit_id).split("\n")    
    try:    
        descr = data[0].split(" - ")[-1].strip()
    except Exception as e:
        Logger.error(e)
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

def enable(unit_id):
    """Enable unit file"""
    return run_command("systemctl", "enable", unit_id)
    
  
def disable(unit_id):
    """Disable unit file"""
    return run_command("systemctl", "disable", unit_id)
   
  
def reenable(unit_id):
    """Reenable unit file"""
    return run_command("systemctl", "reenable", unit_id)
    
  
def preset(unit_id):
    """Enable/disable unit file
       based on preset configuration"""
    return run_command("systemctl", "preset", unit_id)

  
def start(unit_id):
    """Start (activate) unit"""
    return run_command("systemctl", "start", unit_id)

  
def stop(unit_id):
    """Stop (deactivate) unit"""
    return run_command("systemctl", "stop", unit_id)

  
def reload(unit_id):
    """Reload unit"""
    return run_command("systemctl", "reload", unit_id)
    

def restart(unit_id):
    """Start or restart unit"""
    return run_command("systemctl", "restart", unit_id)

  
def try_restart(unit_id):
    """Restart unit if active"""
    return run_command("systemctl", "try-restart", unit_id)

  
def reload_or_restart(unit_id):
    """Reload unit if possible,
       otherwise start or restart"""
    return run_command("systemctl", "reload-or-restart", unit_id)

  
def try_reload_or_restart(unit_id):
    """If active, reload unit,
       if supported, otherwise restart"""
    return run_command("systemctl", "try-reload-or-restart", unit_id)


def isolate(unit_id):
    """Start unit and stop all others"""
    return run_command("systemctl", "isolate", unit_id)

  
def kill(unit_id):
    """Send signal to processes of a unit"""
    return run_command("systemctl", "kill", unit_id)
    
