#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 26 10:36:20 2016

@author: pavel
"""
import logging
import threading

from tempfile import NamedTemporaryFile

APP = "mime-editor-gui"



def async_method(func):
    def start(*args, **kwargs):
        thr = threading.Thread(target = func, args = args, kwargs = kwargs)
        thr.start()
    return start
    
class Singleton(type):
    """ A metaclass that creates a Singleton base class when called. """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


        
class Logger(metaclass=Singleton):   
    
    class CallbackHandler(logging.Handler):
        def __init__(self, *args, **kwargs):
            super(Logger.CallbackHandler, self).__init__(*args, **kwargs)
            self.listener_callbacks = []
            
        def emit(self, record):
            msg = self.format(record)
            for callback in self.listener_callbacks:
                callback(msg)
                
        def add_listener(self, listener_cb):
            self.listener_callbacks.append(listener_cb)
            
    def __init__(self):
        self.logger = logging.getLogger(APP)
        self.logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # to file
        self.tempfile = NamedTemporaryFile(delete = False)
        self.file_handler = logging.FileHandler(self.tempfile.name)
        self.file_handler.setFormatter(self.formatter)
        self.file_handler.setLevel(logging.INFO)        
        self.logger.addHandler(self.file_handler)       
        
        # to console
        self.con_handler = logging.StreamHandler()
        self.con_handler.setFormatter(self.formatter)
        self.con_handler.setLevel(logging.INFO)
        self.logger.addHandler(self.con_handler)
        
        # to anyone
        self.cb_handler = Logger.CallbackHandler()
        self.cb_handler.setFormatter(self.formatter)
        self.cb_handler.setLevel(logging.INFO)
        self.logger.addHandler(self.cb_handler)
        
    def __getattr__(self, attr):       
        return getattr(self.logger, attr)
        
    def add_listener(self, listener_cb):
        self.cb_handler.add_listener(listener_cb)
    
        
logger = Logger()
logger.info("Log file: %s", logger.tempfile.name)