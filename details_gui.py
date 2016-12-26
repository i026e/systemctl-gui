#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 26 10:30:34 2016

@author: pavel
"""
import systemctl_commands as stl
import app_launcher

from gi.repository import Gtk, GObject
from utils import logger, async_method, Singleton

class CommandsMenu(Gtk.Menu):
    def __init__(self, on_command):
        self.on_command = on_command
        
        super(CommandsMenu, self).__init__()
        
        for name in sorted(stl.ALLOWED_ACTIONS.keys()):
            descr = stl.ALLOWED_ACTIONS.get(name, ("", ""))[1]
            menuitem = Gtk.MenuItem()
            menuitem.set_label(name)
            menuitem.set_tooltip_text(descr)
            
            menuitem.connect("activate", self.on_activate, name)
            self.append(menuitem)            

        self.show_all()            

    def on_activate(self, widget, command_name):
        self.on_command(command_name)

class DetailsWindow(metaclass = Singleton):
    UNIT_ACTION_BUTTONS = {  "details_start_btn" : "start",
                             "details_stop_btn" : "stop",
                             "details_restart_btn" : "restart",
                             "details_kill_btn" : "kill",
                             "details_enable_btn" : "enable",
                             "details_disable_btn" : "disable",
                             "details_reload_btn" : "reload" }
    def __init__(self, builder, model, parent_window):
        self.builder = builder
        self.model = model
        
        self.current_path = 0    
        self.current_unit = None        
        
        self.window = self.builder.get_object("details_window")
        self.window.connect("delete-event", self._on_hide)
        self.window.set_transient_for(parent_window)
        
        self.__init_buttons()
        self.__init_widgets()

        
    def __init_widgets(self):
        self.id_label = self.builder.get_object("details_id_label")
        self.status_view = self.builder.get_object("details_status_view")
        self.content_view = self.builder.get_object("details_content_view")
        self.dep_view = self.builder.get_object("details_depend_view")
        self.prop_view = self.builder.get_object("details_prop_view")
        

        
    def __init_buttons(self):
        self.ok_button = self.builder.get_object("details_ok_button")
        self.ok_button.connect("clicked", self._on_hide)
        
        self.action_button = self.builder.get_object("details_action_menu_button")
        self.action_button.set_popup(CommandsMenu(self._on_command_clicked))
        
        self.edit_button = self.builder.get_object("details_edit_button")
        self.edit_button.connect("clicked", self._on_edit_clicked, "normal")
        
        self.edit_full_button = self.builder.get_object("details_edit_full_button")
        self.edit_full_button.connect("clicked", self._on_edit_clicked, "full")
        
         
    def show(self, path):
        self.current_path = path        
        self.current_unit = self.model.get_unit_at_path(self.current_path)
        
        if self.current_unit is not None:
            self._update_widgets()            
        
        self.ok_button.grab_focus()    
        self.window.show()
        
    def _update_widgets(self):
        self.id_label.set_text(self.current_unit.id_)
        self.window.set_title(self.current_unit.id_)
        
        self._set_status()
        self._set_content()
        self._set_dependencies()
        self._set_properties()
        
    def _set_text(self, textview, text):
        textview.get_buffer().set_text(text)
        return False #!!! For idle_add
        
    @async_method    
    def _set_status(self):
        status = self.current_unit.get_status()
        GObject.idle_add(self._set_text, self.status_view , status)

    @async_method    
    def _set_dependencies(self):
        dependencies = self.current_unit.get_dependencies()
        GObject.idle_add(self._set_text, self.dep_view, dependencies)
        
    @async_method
    def  _set_properties(self):
        properties = self.current_unit.get_properties()
        GObject.idle_add(self._set_text, self.prop_view, properties) 
    
    @async_method    
    def _set_content(self):
        content = self.current_unit.get_content()
        GObject.idle_add(self._set_text, self.content_view, content)
     
    @async_method    
    def _start_editor(self, mode):
        app_launcher.Editor.run_editor(self._on_edit_completed,
                                       self.current_unit.id_, mode)
        
    def _on_hide(self, *args):
        self.current_unit = None
        self.window.hide()
        return True #!!! otherwise segfault on next show
        
    def _on_command_clicked(self, command):
        if self.current_unit is  not None:
            self.current_unit.execute(command)
            self.model.update_unit_at_path(self.current_path)
            self._update_widgets()
            
    def _on_edit_clicked(self, widget, mode):        
        self._start_editor(mode)
        
    def _on_edit_completed(self, unit_id):
        if (self.current_unit is not None) and \
            (self.current_unit.id_ == unit_id):
                GObject.idle_add(self._update_widgets)
            