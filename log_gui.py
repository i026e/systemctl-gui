#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 26 16:40:05 2016

@author: pavel
"""
from gi.repository import GObject
from utils import logger, Singleton

class LogWindow(metaclass=Singleton):
    def __init__(self, builder, parent_window):
        self.builder = builder
        self.visible = False
        
        self.window = self.builder.get_object("log_window")
        self.window.connect("delete-event", self._on_hide)        
        
        self.log_view = self.builder.get_object("log_view")
        self.log_buffer = self.log_view.get_buffer()        
        
        ok_button = self.builder.get_object("log_ok_button")
        ok_button.connect("clicked", self._on_hide)
        
        logger.add_listener(self._on_log_msg)
        
    def _set_bufer(self):
        logger.tempfile.file.seek(0)
        text = logger.tempfile.file.read().decode("utf-8")
        self.log_buffer.set_text(text)
        
    def _reset_buffer(self):
        start_iter = self.log_buffer.get_start_iter()
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.delete(start_iter, end_iter)
        
    def show(self):
        self._set_bufer()
        self.visible = True
        self.window.show()
        
    def _on_hide(self, *args):
        self.visible = False
        self._reset_buffer()
        self.window.hide()
        return True #!!!
        
    def _on_log_msg(self, message):
        def add_message():
            end_iter = self.log_buffer.get_end_iter()
            self.log_buffer.insert(end_iter, message)
            return False
            
        if self.visible:
            GObject.idle_add(add_message)
        