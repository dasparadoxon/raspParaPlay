#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""
COLLECTIONSMANAGER MODUL FOR raspParaPlay
---
Handles Collections
"""

import logging,os,sys,random,subprocess
import sqlite3
import curses

from datetime import datetime

from configurationManager import configurationManager

class collectionsManager:
    
    stdscr = None
    
    logger = None
    
    collections = None
    
    ConfigurationsManager = None
    
    hardcodedCollectionsForDev = [
        
        ["Musik","Musik"],
        ["Erotik","Erotik"],
        ["TV","TV"],
        ["Dokumentionen","Dokumentationen"],
        ["Filme","Filme"]
    
    ]    
    
    defaultCollectionIndex = 0
    
    secondsUntilDefaultCollectionIsLoaded = 5   
    
    def __init__(self,loggerToUse,useCollection=False,stdscrToUse=None):
        
        self.logger = loggerToUse
        
        self.stdscr = stdscrToUse
        
        self.logger.debug("CollectionsManager ready.")
        
        self.ConfigurationsManager = configurationManager(self.logger)
        
        self.collections = self.hardcodedCollectionsForDev
    
    
    def isCollectionSelected(self):
        
        check = self.collections
        
        if(check == None):
            self.logger.debug("A collection is not selected yet.")
            return False
        else:
            self.logger.debug("A collection is already selected.")
            return True       
        
    def generateFullDatabaseFilename(self,collectionName):
        
        return "paraplayDatabase" + collectionName + ".db"   
    
    def UI_showCollections(self):
        
        self.stdscr.border()
        
        for index,collection in enumerate(self.collections):
            
            self.stdscr.addstr(index + 1,1,"%i - %s" % (index,collection[0]))
        
            self.stdscr.refresh()
        
           


    def askUserWhichCollectionShouldBeUsed(self):
        
        self.UI_showCollections()
        
        validChoice = False
        
        key = None
        
        
        while validChoice == False:
            
            key = self.stdscr.getch()
            
            if(ord('1') <= key <= chr(len(self.collections))):  
                
                self.logger.debug("Key pressed : %i" % key)
                
                validChoice = True
                
                
        #TODO : Good conversion into int from keypressed, too tired :D        
        
        collectionDatabaseFilename = self.generateFullDatabaseFilename(self.hardcodedCollectionsForDev[key-49][1])
        
        self.logger.debug("Returning the Collection Database Filename '%s'." % collectionDatabaseFilename)
        
        return collectionDatabaseFilename
        
        

