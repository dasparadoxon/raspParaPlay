#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""
SCANNER MODUL FOR raspParaPlay
---
Handles scanning directories, filling the database, update the file base
- isAware of Collections
- isAware of CollectionsManager
"""

import logging,os,sys,random,subprocess
import sqlite3

from datetime import datetime

class scanner:
    
    logger = None
    
    def __init__(self,loggerToUse):
        
        self.logger = loggerToUse
        
        self.logger.debug("Scanner ready.")
        
        





