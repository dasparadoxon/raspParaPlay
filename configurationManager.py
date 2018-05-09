#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""
configurationManager MODUL FOR raspParaPlay
---
Handles main Database and gives modules the ability to save there
"""

import logging,os,sys,random,subprocess
import sqlite3

from datetime import datetime

class configurationManager:
    
    logger = None
    
    collections = None
    
    configurationDatabaseFilename = "paraPlayDatabaseConfiguration.db"

    
    """ """
    
    def __init__(self,loggerToUse):
        
        self.logger = loggerToUse
        
        self.logger.debug("configurationManager ready.")
     
    def configurationDatabaseFileExists(self):
        
        return os.path.isfile(self.configurationDatabaseFilename)

    def isFirstTime(self):
        
        return False
        
        # SKIPPING THIS (V30) UNTIL I WANT TO USE THE CONF DB ACTUALLY
        
        check = self.configurationDatabaseFileExists()
        
        if(check == True):
            self.logger.debug("raspParaPlay has been executed before here.")
            return False
        else:
            self.logger.debug("This seems to be the first time raspParaPlay is running here.")
            return True
        
   
    def createConfigurationDatabase(self):
        
        pass