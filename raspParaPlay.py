#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

import sys,os, random,subprocess
import sqlite3
import curses
import logging
import termios, fcntl
from curses import wrapper
from datetime import datetime
import textwrap

from scanner import scanner
from configurationManager import configurationManager
from collectionsManager import collectionsManager
from mysql.utilities.common import database

version = 30

exitMessage = ""

collectionDatabaseFileName = None

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
rows = None
columns = None

debug = True

action = "play"

dirs = [""]

blockList = [""]

sqliteConnection = None
sqliteCursor = None

quitProgram = False

system = "Unknown"

playSongsWithRatingAbove = 0

playAll = True

nowPlayingWindow = None
metaWindow = None
statsWindow = None
legendWindow = None

stats = { "numberOfSongs":0,"blocked":0 }

stdscr = None

germanRatingNames = ["Sehr gut","Gut","Befriedigend","Ausreichend","Mangelhaft","Please kill me."]

numberOfFilteredSongs = 0

loopMode = False

fileWithPath = ""
fileToCheck = None
previousSong = None

startPlayInterface = True

currentSongRating = None

sqlTablePlayCountColumnIndex = 1
sqlTableRatingColumnIndex = 1

hardCodedWordBlockList = ["Country Nummer"]

bannedSong = False


collections = ["Musik","TV","Filme","Erotik"]

selectedCollection = None

""" MODULES """

Scanner = None
ConfigurationManager = None
CollectionsManager = None

def calculateStats():
    
    global logging
    
    global sqliteConnection
    global sqliteCursor
    
    global stats
    
    sqliteCursor.execute("SELECT count(*) FROM plays WHERE block=0") # EXCLUDING BLOCKED SONGS !
    
    numberOfSongs =  sqliteCursor.fetchone() 
    
    stats["numberOfSongs"] = int(numberOfSongs[0])
    
    sqliteCursor.execute("SELECT count(*) FROM plays WHERE block=1")
    
    numberOfBlockedSongs =  sqliteCursor.fetchone()  
    
    stats["blocked"] = int(numberOfBlockedSongs[0])
    
    logging.debug("Calculated Stats : %s " % stats)


def readDirectoriesFromFile():
    
    global dirs
    global debug
    
    del dirs[:]
    
    directoryFilePath = getHomePath() + "/" +'directories.txt'
 
    
    with open(directoryFilePath, 'r') as f:
        dirs = f.readlines()


def getHomePath():
    
    from os.path import expanduser
    homePath = expanduser("~")
    
    return homePath


def initCollectionDatabase():
    
    global sqliteConnection,sqliteCursor
    global collectionDatabaseFileName
    global logging
    
    logging.debug("Init Collection Database, Database file is : %s " % collectionDatabaseFileName)
    
    sqliteConnection = sqlite3.connect(collectionDatabaseFileName)
    sqliteCursor = sqliteConnection.cursor()
   
    
def parseCommandLine():

    global exitMessage
    global action
    global startPlayInterface
    global logging
    global collectionDatabaseFileName
    
    global ConfigurationManager
    
    cliParameterCount = len(sys.argv)
    
    if( cliParameterCount > 1):
        firstParameter =sys.argv[1]
    if( cliParameterCount > 2):        
        secondParameter = sys.argv[2]
        
    logging.debug("Parsing command line.")

        
    if(ConfigurationManager.isFirstTime() == True):
    
        exitMessage = "\n\nIt seems that is the first time you use raspParaPlay.Thank you ! \n\n\nYou need to specifiy a directory where your media files are stored. \n"
        exitMessage += "\nOr, you can use the parameter -c to scan the current directory and subdirectories.\n\n"
    
        return False        
        
        
    if(cliParameterCount == 1):
            
            logging.debug("No command line arguments were given. Starting.")
            
            # Give control to collectionsManager
            
            collectionDatabaseFileName = CollectionsManager.askUserWhichCollectionShouldBeUsed()
            
            initCollectionDatabase()
            
            return True
    

    if( cliParameterCount > 1):
        
        if(debug):
            print("Action Command is :" + firstParameter)
            
        action = firstParameter
        
        if(action=="-c"):
            
            print("Not implemented yet.")
            
            return False
            
            pass
            
        
        if(action=="-s"):
            
            if(cliParameterCount > 2):
            
                logging.debug("Scanning given Directory (and its subdirectories)...")
                
                createDBFileAndTableIfNotExisting()
 
                logging.debug("Scanning in  %s. " % secondParameter)
                    
                startPlayInterface = False
                
                scan_directories(secondParameter)
                    
                logging.debug("Finish Scanning.\n")   
                
                return True 
                
            else:
                
                logging.debug("-scan Paramater, but without directory given. Exiting.")
                exitMessage = "You must specify a directory in combination with the -s parameter."
                return False
                
    
        
    return true

def handleKeyInputMainScreen(process,fileWithPath):
    
    global numberOfFilteredSongs,nowPlayingWindow
    global dirs,debug
    global blockList
    global sqliteCursor,sqliteConnection
    global system,stdscr,songCount,stats
    global quitProgram
    global playSongsWithRatingAbove,playAll
    global metaWindow
    global rows
    global columns
    global loopMode
    global fileToCheck    
    
    while( process.poll() is None):

        try:
            
            c = stdscr.getch()
            
            if(c != -1):
                logging.debug("Character %s was entered." % c)
            
            if c == ord('p'):
                
                if(system == "RASPBERRY"):
                    
                    process.stdin.write('p')   
                
            if c == 32:     
                
                logging.debug("Leertaste gedrückt. Springe zum nächsten Song.")   

                killPlayer(system,process)
                    
            if c == curses.KEY_UP:        

                if(system == "RASPBERRY"):
                    
                    process.stdin.write('+')       
                    
                    
            if c == curses.KEY_DOWN:        

                if(system == "RASPBERRY"):
                    
                    process.stdin.write('-')
                    
            if c == curses.KEY_LEFT:
               
                if(system == "RASPBERRY"):
                    
                    process.stdin.write(curses.KEY_LEFT)       
                    
                    
            if c == curses.KEY_RIGHT:        

                if(system == "RASPBERRY"):
                    
                    process.stdin.write(curses.KEY_RIGHT)                                                         

                
            if c == ord('q'):   
                
                logging.debug("Received quit !")

                killPlayer(system,process)
                    
                quitProgram = True
                
            if c == ord('1'):              

                setRating(fileWithPath,1)
                
            if c == ord('2'):                
            

                setRating(fileWithPath,2)
                
            if c == ord('3'):                  
            

                setRating(fileWithPath,3)
                
            if c == ord('4'):                 
            

                setRating(fileWithPath,4)
                
            if c == ord('5'):                 
            

                setRating(fileWithPath,5)
                
            if c == ord('6'):                 
           
                setRating(fileWithPath,6)    
                
            if c == ord('l'):
                
                
                loopMode = not loopMode
                
                logging.debug("Switching Loop-Mode to %s" % str(loopMode))  
                
                updateStatusWindow(statsWindow,loopMode,playAll,songCount)
                
                
            # ALT WAS PRESSED, NOT THE BEST METOD BUT WORKS    

            if c == 27: 
                
                stdscr.nodelay(True)
                ch2 = stdscr.getch() # get the key pressed after ALT
                
                if ch2 == -1:
                    break
                else:
                    
                    logging.debug("ALT was pressed with %i afterwards " % ch2)
                    
                    if(ord('1') <= ch2 <= ord('6')):
                        
                        ch2 = ch2 - ord('1')
                        
                        playSongsWithRatingAbove = ch2 + 1 #HMM
                        playAll = False
                        
                        logging.debug("ALT-1 QuickChanging to Rating besser als %i" % playSongsWithRatingAbove)
                        
                        updateStatusWindow(statsWindow,loopMode,playAll,songCount,playSongsWithRatingAbove) 
                        
                        killPlayer(system,process)                       
                  
                
            if c == 263 :
                
                playPrevious = True
                
                  
                
            if c == ord('r'):
                
                handleRatingFilter()
                
                killPlayer(system,process)
                    
            # BLOCK THE PLAYING SONG 
            # TOTHINK : AUTOMATICALLY SKIPPING TO NEXT RANDOM SONG ?
                
            if c == ord('b'):  
                
                handleBlocking(fileWithPath)
                

        except IOError: pass   
        
    logging.debug("Process no longer active, quitting keyboard-while loop and go back to play")

def handleRatingFilter():
    
    logging.debug("Handling change of rating filter")
    
    global playSongsWithRatingAbove,playAll,statsWindow,loopMode,songCount
        
    playSongsWithRatingAbove -= 1
    
    playSongsWithRatingAbove %= 7
    
    if(playSongsWithRatingAbove == 0):
        
        playAll = True
        
    else:
        
        playAll = False
                   
    updateStatusWindow(statsWindow,loopMode,playAll,songCount) 
    
    
        
        
def killPlayer(system,process):
    
    global logging
    
    if(system != "RASPBERRY"):
        
        logging.debug("Killing Player Process, not Raspberry Pi")
        
        process.kill()
    else:
        
        logging.debug("Sending Key q to the Player Process omxplayer on Raspberry Pi")
        
        # Giving the OMX-Player the input via the popen PIPE :D
        process.stdin.write('q')
        
    logging.debug("Player process killed or terminated.")
        
        
def handleBlocking(fileWithPath):
    
    global numberOfFilteredSongs,nowPlayingWindow
    global dirs,debug
    global blockList
    global sqliteCursor,sqliteConnection
    global system,stdscr,songCount,stats
    global quitProgram
    global playSongsWithRatingAbove,playAll
    global metaWindow
    global rows
    global columns
    global loopMode
    global fileToCheck     
    
    logging.debug("Blocking Song '%s'" % fileWithPath)
                
    t = (fileWithPath,)
    sqliteCursor.execute("SELECT * FROM plays WHERE file=?",t)
    
    fileWithCurrentBlockStatusDBEntry = sqliteCursor.fetchone()
    
    blockStatus = fileWithCurrentBlockStatusDBEntry[3]
    
    logging.debug("Blockstatus of Song : %s" % str(blockStatus))
    
    if(blockStatus == 0):
        
        logging.debug("Song ist nun geblockt.")
        
        #TODO - ERASE WHOLE ROW
        
        metaWindow.addstr(4,2,"Song ist nun geblockt.  ")
        
        t = (fileWithPath,)
        sqliteConnection.execute("UPDATE plays SET block = 1 WHERE file=?",t)
        
        songCount -= 1
        
        updateStatusWindow(statsWindow,loopMode,playAll,songCount)
        
        #updateMetaWindow(metaWindow)- prevents blocking message window to show correctly
        
        stats['numberOfSongs'] -= 1
        
    else:
        
        logging.debug("Song ist nun entblockt.")
        
        metaWindow.addstr(4,2,"Song ist nun entblockt.  ")
    
        t = (fileWithPath,)
        sqliteConnection.execute("UPDATE plays SET block = 0 WHERE file=?",t)
        
        songCount += 1
        
        updateStatusWindow(statsWindow,loopMode,playAll,songCount)    
        
        stats['numberOfSongs'] += 1                 
        
    metaWindow.refresh()
        
    sqliteConnection.commit()    
    

        
def retrieveLowestPlayCount():
    
    logging.debug("Getting lowest play count, excluding blocked songs.")
    
    global sqliteCursor
    
    sqliteCursor.execute("SELECT min(playCount) FROM plays WHERE block != 1")
    
    min =  sqliteCursor.fetchone()
    
    return min        


def updateNowPlayingWindow(nowPlayingWindow,fileWithPath,timesPlayed,rating):
    
    global logging
    
    logging.debug("Trying to play Song '%s'" % fileWithPath)
    
    displayFileName = fileWithPath
    
    displayFileName = displayFileName.split("/")
    
    # ??? playSongsWithRatingAboveToStr = playSongsWithRatingAbove + 1
    
    nowPlayingWindow.border()
    
    nowPlayingWindow.erase()
    
    fileNameOnly = displayFileName[len(displayFileName)-1]
    
    fileNameOnlyUFT8clean = fileNameOnly.encode('utf8', 'replace')
    
    try:
        
        nowPlayingWindow.addstr(2,3,"%s" % fileNameOnlyUFT8clean)
        
    except Exception, e: 
    
        logging.debug("Error while trying to display current filename, most likley UNICODE error, skipping")
        logging.debug(str(e))
        return False
    
    # TIMES PLAYED
    
    nowPlayingWindow.hline(4,3,"-",20-7)
    
    try:
        nowPlayingWindow.addstr(6,3,"- %i mal abgespielt." % (timesPlayed))
    except:
        
        message = "- Fehler ! Die Anzahl von Plays für den Song konnte nicht ermittelt werden"
        
        cleanMessage = message.encode('utf8','replace')
        
        nowPlayingWindow.addstr(6,3,cleanMessage)
    
    nowPlayingWindow.border()
    
    # FULL, SHORTEND PATH
    
    pathToConsole = fileWithPath
    
    h,w = nowPlayingWindow.getmaxyx()
    
    borderMod = 60
    
    offset = -w + 20
    
    pathToConsole = fileWithPath[offset:]
    
    if(len(fileWithPath) > offset):
        
        pathToConsole = "..." + pathToConsole
        
    pathToConsoleUTF8clean = pathToConsole.encode('utf8', 'replace')
    
    nowPlayingWindow.addstr(8,3,"- %s" % (pathToConsoleUTF8clean))
    
    # RATINGS
    
    germanRatingNames = ["Sehr gut","Gut","Befriedigend","Ausreichend","Mangelhaft","Please kill me."]
    
    if(rating != 0):
        
        nowPlayingWindow.addstr(10,3,"- Bewertung (von 1-6) : %i (%s)" % (rating,germanRatingNames[rating-1]))
        pass
    else:
        nowPlayingWindow.addstr(10,3,"- Keine Bewertung bisher getroffen")
        pass    
    
    return True
    

def getASongToPlay(loopMode,playAll,minimalPlayCount,playSongsWithRatingAbove=0,currentSong=None):
    
    global fileToCheck
    global hardCodedWordBlockList
    global bannedSong
    
    logging.debug("Obtaining a Song to play.")
    
    # Get all those songs with that playCount and choose one randomly, ignore songs that are blocked
    if(loopMode == False):
        
        logging.debug("Loop Mode is not activated.")
        
        if(playAll):
            
            logging.debug("PlayAll on, searching one song of all songs played equally less than all other songs, maximal %i time(s)." % minimalPlayCount)
            
            sqlString = "SELECT * FROM plays WHERE playCount=%i AND block=0 ORDER BY RANDOM() LIMIT 1" % minimalPlayCount
            
            sqliteCursor.execute(sqlString)
            
            
            
        else:
            
            logging.debug("PlayAll off, searching for songs with rating better than Rating %i. (thus excluding not-rated and blocked songs)" % playSongsWithRatingAbove)
            
            # GET THE NUMBER OF ALL SONGS THAT FALL INTO THE FILTER RATING CRITERIA 
            
            sqlString = "SELECT count(*) FROM plays WHERE rating < %i AND rating != 0 AND block=0" % playSongsWithRatingAbove
            
            sqliteCursor.execute(sqlString)
            
            countOfFilteredSongs = sqliteCursor.fetchone()
            
            numberOfFilteredSongs = countOfFilteredSongs[0]
            
            logging.debug("Found %i songs that fall in that category, trying to pick one." % numberOfFilteredSongs)
            
            sqlString = "SELECT * FROM plays WHERE rating < %i AND rating != 0 AND block=0 ORDER BY RANDOM() LIMIT 1" % playSongsWithRatingAbove
    
            sqliteCursor.execute(sqlString)        
            
            
        
        fileToCheck =  sqliteCursor.fetchone()
        
        
        if(fileToCheck is None):
            
            playSongsWithRatingAbove=0
            #print("There are no songs with a rating better than "+str(playSongsWithRatingAboveToStr))
            #print("Playing all files like normally instead.")
            #playSongsWithRatingAbove = 0
            playAll=True
            
            #updateStatusWindow()  
            
            return None
        
        #fileWithPath = fileToCheck[0]   
        
        logging.debug("Found File %s." % str(fileToCheck))
        
        logging.debug("Check Word Bann List...")
        
        
        for word in hardCodedWordBlockList:
            
            logging.debug("Checking word %s" % word)
            
            if(word in fileToCheck[0]):
                
               logging.debug("Found banned words, skipping song.")
               
               #bannedSong = True
               
               setSongBlockStatus(1,fileToCheck[0])
               
               #perhaps even blocking ?
               
               return None
        
        
        return(fileToCheck) 
    
    else:
        
        logging.debug("Song looping active. Repeating Song.")
        
        updateCountInIDE()
        
        return(fileToCheck)
        
    
    
def updateCountInIDE():
    
    # NOT IMPLEMENTED
    
    pass    
        
        
def setSongBlockStatus(newStatus,file):
    
    global logging
    global sqliteConnection
    global sqliteCursor
    
    
    if(newStatus == 0):
        t = (file,)
        sqliteConnection.execute("UPDATE plays SET block = 0 WHERE file=?",t)
        
    if(newStatus == 1):
        t = (file,)
        sqliteConnection.execute("UPDATE plays SET block = 1 WHERE file=?",t)

    
    sqliteConnection.commit()
    
    logging.debug("Setting Block Status of %s to %i." % (file,newStatus))
    
    
            
        
def play():
    
    
    global numberOfFilteredSongs
    global dirs
    global blockList
    global debug
    global sqliteConnection
    global sqliteCursor
    global quitProgram
    global system
    global playSongsWithRatingAbove
    global playAll
    global nowPlayingWindow
    global stdscr
    global metaWindow
    global rows
    global columns
    global fileWithPath
    global loopMode
    global fileToCheck
    global statsWindow
    global stats
    global songCount
    global bannedSong
    
    logging.debug("(PLAY - START)")

    
    songCount = stats["numberOfSongs"]
    
    directory = dirs[0].strip()
        
    lowestPlayCount = retrieveLowestPlayCount()
    
    fileToPlay = (None,None,None)
    
    fileToPlay = getASongToPlay(loopMode,playAll,lowestPlayCount[0],playSongsWithRatingAbove)
    
    if(bannedSong):
        
        bannedSong = False
        fileToPlay = getASongToPlay(loopMode,playAll,lowestPlayCount[0]+1,playSongsWithRatingAbove)
    
        
    
    if(fileToPlay == None):
        
       logging.debug("Found no file that matches the ranking criteria !")
       
       logging.debug("PlayAll : %s, SongsAboveRating : %s" % (str(playAll),str(playSongsWithRatingAbove)))
       
       playAll = True
       playSongsWithRatingAbove = 0
       
       return
    
        # UPDATE WINDOWS
    
    noError = updateNowPlayingWindow(stdscr,fileToPlay[0],fileToPlay[1],fileToPlay[2])
    
    if(noError == False):
        return
    
    updateStatusWindow(statsWindow,loopMode,playAll,stats["numberOfSongs"], playSongsWithRatingAbove)
    
    updateMetaWindow(metaWindow)
    
        # CREATE PROCESS

    process = createPlayerProcess(fileToPlay[0])
    
    if(process == None):
        
        logging.debug("Got NONE back from creating process. Strange.")
        return
    
    refreshStdScr()
    
        # KEYBOARD LOOP, WATCHING OVER STATUS OF SONG PLAYING PROCESS
    
    handleKeyInputMainScreen(process,fileToPlay[0])    
    
        # INCREASE PLAY COUNT
    
    increasePlayCount(fileToPlay[0])
    
    logging.debug("(PLAY - STOP)\n")


def updateMetaWindow(metaWindow):
    
    metaWindow.erase()
    metaWindow.border()
    metaWindow.refresh()
    
def refreshStdScr():
    
    global stdscr
    global logging
    
    logging.debug("Refreshing PlayingNowScreen (stdscr).")
    
    stdscr.refresh()


def createPlayerProcess(fileWithPathToPlay):
    
    logging.debug("Creating player process")
    
    
    try:
        commandLine = "omxplayer"
    
        if(system != "RASPBERRY"):
            
            commandLine = "mpg123"
            
        parameter1 = fileWithPathToPlay
       
        args  = [commandLine,parameter1]
        
        logging.debug("New process parameters : %s" % str(args))
        
        FNULL = open(os.devnull, 'w')
        
        p = subprocess.Popen(args,stdin = subprocess.PIPE,stdout=FNULL, stderr=subprocess.STDOUT )  
        
        logging.debug("Player Subprocess created.")
        
    except:
        
        logging.debug("Something gone wrong while trying to create the player subprocess.")
        
        return None
    
    return p  
        
def increasePlayCount(filePath):
    
    global sqliteConnection
    global sqliteCursor 
    global sqlTablePlayCountColumnIndex   
    global logging
    
    logging.debug("Trying to increase playcount for file %s" % filePath[-30:])
    
    t = (filePath,)
    sqliteConnection.execute("UPDATE plays SET playcount = playcount + 1 WHERE file=?",t)
                
    sqliteConnection.commit()
    
    t = (filePath,)
    sqliteCursor.execute("SELECT * FROM plays WHERE file=?",t)
    
    result = sqliteCursor.fetchone()

    
    newPlaycount = result[sqlTablePlayCountColumnIndex]    
    
    logging.debug("Increased playcount of %s to %i plays." % (t[-30:],newPlaycount))   
     
    
def setRating(fileWithPath,newRating):
    
    global logging                
    global sqliteConnection
    global sqliteCursor  
    global metaWindow  
    
    germanRatingNames = ["Sehr gut","Gut","Befriedigend","Ausreichend","Mangelhaft","Please kill me."]
    
    # old rating ?
    
    metaWindow.move(2,1)
    metaWindow.clrtoeol()
    metaWindow.border()
    
    metaWindow.addstr(2,2,"Bewertung ist nun %i. (%s)." % (newRating,germanRatingNames[newRating-1]))
    metaWindow.refresh()
    
    t = (fileWithPath,)
    sqliteConnection.execute("UPDATE plays SET rating="+str(newRating)+" WHERE file=?",t) 
    
    sqliteConnection.commit()
    
    logging.debug("Changed song rating to %i." % newRating)
    

def checkIfDatabaseTableExists(tableName):
    
    global logging
    
    global sqliteConnection
    global sqliteCursor
    
    query = "SELECT name FROM sqlite_master WHERE type='%s' AND name='%s'" % (tableName,tableName)
    
    sqliteCursor.execute(query)
    
    tableExists = sqliteCursor.fetchone()
    
    logging.debug("Table %s : %s" % (tableName,str(tableExists)))
        
    
    
    
def createBlockingWordsTableIfNotExisting():
    
    global logging
    
    global sqliteConnection
    global sqliteCursor
    
    checkIfDatabaseTableExists('wordBlockList')
    
    


def createDBFileAndTableIfNotExisting():
    
    global sqliteConnection
    global sqliteCursor
    global dirs
    global collectionDatabaseFileName
    
    debugDatabase = False
    
    #databaseFileExists = os.path.isfile(collectionDatabaseFileName)

    #if(debugDatabase):
    #    if(databaseFileExists):
    #        logging.debug("Database %s exists." % databaseFileName)
    #    else:
    #        logging.debug("Database %s does not exist." % databaseFileName)
    
    sqliteConnection = sqlite3.connect(databaseFileName)
    sqliteCursor = sqliteConnection.cursor()
    
    #if(not databaseFileExists):
        
        
    #    logging.debug("Creating table in Database.")
            
        # Create table
    #    sqliteCursor.execute('''CREATE TABLE plays
    #                (file text, playCount int, rating int,block int)''') 
                    
    #    logging.debug("\tReading files and sub-directories into database...")
        
    #    scan_directories(dirs[0].strip())
        
    #    logging.debug("\tCreated database entries for files and subdirectories")
        
    createBlockingWordsTableIfNotExisting()    
        


def scan_directories(path):
    
    
    
    countImports = 0
    
    for root, subdirs, files in os.walk(path):
        #print('--\nroot = ' + root)
        #list_file_path = os.path.join(root, 'my-directory-list.txt')
        #print('list_file_path = ' + list_file_path)
    
        #with open(list_file_path, 'wb') as list_file:
            
            #for subdir in subdirs:
                #print('\t- subdirectory ' + subdir)
    
        for filename in files:
            file_path = os.path.join(root, filename)
    
            #print('\t- file %s (full path: %s)' % (filename, file_path))
            #print('\t- Datei :  %s' % (filename))
            
            thefilename, file_extension = os.path.splitext(file_path)
            
            #TODO ENCODING HERE ?
            #s.encode('utf16')
            
            #print("Extention:"+file_extension)
            
            if(file_extension==".mp3" or file_extension==".flv" or file_extension==".ogg"):
                
                #logging.debug("Inserting '%s' into Database." % file_path)
            
                sqliteConnection.execute("INSERT INTO plays VALUES (\""+file_path+"\",0,0,0)")
            
                sqliteConnection.commit()
                
                countImports = countImports + 1
                
                #filenameUTF = filename.encode('utf-16')
                
                logging.debug('\t- %i - Datei :  \'%s\' in Datenbank aufgenommen.' % (countImports,filename))
            else:
                logging.debug('\t- Datei :  %s ist keine Musikdatei.' % (filename))
  
                    


    
def updateStatusWindow(statsWindow,loopMode,playAll,songCount,playSongsWithRatingAbove=0,numberOfFilteredSongs=0):
    
    global logging
    
    logging.debug("Updating Status Window.")
    
    # TODO: CHECK FOR ENOUGH HEIGHT IN WINDOWS
    
    statsWindow.erase()
    
    statsWindow.border()
    
    statsWindow.addstr(1,1," ABSPIEL-MODUS")
    statsWindow.hline(2,1,"-",curses.COLS/2-2)
    
    if(loopMode):
        
        statsWindow.addstr(4,1," - Loope aktuellen Song.")
        pass
    
    else:
    
        if(playAll):
            statsWindow.addstr(4,1," - Spiele alle nichtblockierten Songs ab.")
            pass
        else:
            
            statsWindow.addstr(4,1," - Bewertung besser als : %i (%s)" %(playSongsWithRatingAbove,germanRatingNames[playSongsWithRatingAbove-1]))
            pass
        
    statistikOffset = 7    
        
    statsWindow.addstr(statistikOffset,1," STATISTIKEN")
    statsWindow.hline(statistikOffset+1,1,"-",curses.COLS/2-2)
    
    if(playAll):
        try:
            statsWindow.addstr(statistikOffset+3,1," - Songpool : %i " % (songCount))
        except:
            
            # MOST LIKLEY THE TERMINAL IS TOO SMALL TO SHOW THE STRING !!! TODO
            
            # statsWindow.addstr(statistikOffset+3,1," - FEHLER - Unbekannte Anzahl von Songs !")
            
            pass
        
        pass
        
    else:
        
        # THIS NEEDS TO GO INTO A FUNCTION
        
        sqlString = "SELECT count(*) FROM plays WHERE rating < %i AND rating != 0 AND block=0" % playSongsWithRatingAbove
        
        sqliteCursor.execute(sqlString)
        
        countOfFilteredSongs = sqliteCursor.fetchone()
        
        numberOfFilteredSongs = countOfFilteredSongs[0]
        
        statsWindow.addstr(statistikOffset+3,1," - %i Songs von %i" % (numberOfFilteredSongs,songCount))
        
    #showBlockedSongCount = False
        
    #if(showBlockedSongCount):
    #    statsWindow.addstr(statistikOffset+5,1," - BLOCKIERTE SONGS : %i " % (stats["blocked"]))
    
    statsWindow.refresh()
    
    #legendWindow.refresh()
    
    stdscr.refresh()
    
def createSubWindows():
    
    global statsWindow,nowPlayingWindow,metaWindow,legendWindow,stdscr,rows,columns,logging
    
    logging.debug("Creating Subwindows.")
    
    spaceForKeyWindow = 3
    
    metaWindow = curses.newwin(curses.LINES/2 - spaceForKeyWindow,int(curses.COLS)/2,int(curses.LINES)/2,0)
    metaWindow.scrollok(0)
    metaWindow.border()
    metaWindow.refresh()
    
    statsWindow = curses.newwin(curses.LINES/2 - spaceForKeyWindow,int(curses.COLS)/2,curses.LINES/2,int(curses.COLS)/2)
    statsWindow.scrollok(0)
    statsWindow.border()
    statsWindow.refresh()
    
    createLegendWindow()
    
    stdscr.refresh()
    
def createLegendWindow():
    
    global legendWindow
    global stdscr
    global version
    global logging
    
    logging.debug("Creating Legend Window.")
    
    legendWindow = curses.newwin(3,0,curses.LINES-3,0)
    legendWindow.scrollok(0)
    legendWindow.border()
    legendWindow.addstr(1,1," [ LEERTASTE- Weiter ] [ q - Ende ] [ b - Blocken ] [ 1-6 Bewerten ] [ r - Filter ] [ l - Loop ]")
    lengthOfVersionString = len("[ VERSION %i ]" % (version))
    legendWindow.addstr(1,curses.COLS - lengthOfVersionString-2,"[ VERSION %i ]" % (version))
    legendWindow.refresh()
    
def startCurses():
    
    global logging    
    
    global stdscr
    
    stdscr = curses.initscr()
    
    logging.debug("Curses initialised...")
    
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    curses.curs_set(0)
    stdscr.scrollok(0)
    stdscr.nodelay(1) 
    
    logging.debug("Curses Options set...")
    
    curses.start_color()
    
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    
    logging.debug("Curses Custom Colors set...")


    
def endCurses():
    
    global stdscr
    
    curses.nocbreak(); 
    stdscr.keypad(0); 
    curses.echo()
    
    curses.endwin()
    
    logging.debug("Finished Curses.");
    
def mainLoop(stdscr):
    
    global logging
    
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    curses.curs_set(0)
    stdscr.scrollok(0)
    stdscr.nodelay(1) 
    
    global quitProgram
    
    while(quitProgram == False):
        
        logging.debug("Main Loop - Going into play again.")
        play()
        
def cursesWithWrapperInit(stdscr):
    
    curses.curs_set(0)

    stdscr.resize(curses.LINES/2,curses.COLS)
    
    stdscr.border()
    
def initNativeLogSystem(whatSystem):
    
    try:
        os.remove('raspParaPlay.log')
    except:
        pass
    
    #dateTime = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
    
    global logging   
    
    logFileName = 'raspParaPlay.log'
    
    if(whatSystem=="PC_UBUNTU"):
        
        logging.basicConfig(
         filename=logFileName,
         level=logging.DEBUG, 
         #format= '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
         format= '[%(asctime)s] %(funcName)30s - {%(lineno)d} %(levelname)s - %(message)s',
         datefmt='%H:%M:%S'
        )
        
        
    if(whatSystem=="RASPBERRY"):
        logging.basicConfig(filename='raspParaPlay.log',level=logging.ERROR)    
        

      
      
    #logging.debug("\n [%s]-------------------------------------------------------" % dateTime)
    
    
def initComponents():
    
    global Scanner
    global logging
    global stdscr
    
    Scanner = scanner(logging)
    
    global ConfigurationManager
    
    ConfigurationManager = configurationManager(logging)
    
    global CollectionsManager
    
    CollectionsManager = collectionsManager(logging,stdscrToUse=stdscr)
    
    logging.debug("Loaded Components [Scanner, ConfigurationsManager, CollectionsManager]")
    
        
        
def main(stdscr_from_wrapper):    
    
    global logging    
    global rows,columns
    global stdscr
    global version
    global stats
    global system
    
    cursesWithWrapperInit(stdscr_from_wrapper)
    
    stdscr = stdscr_from_wrapper
    
    systemInfo = os.uname()
    
    system = "RASPBERRY"
    
    if( systemInfo[1] == 'ubuntu' and systemInfo[4]=='i686'):
        system = "PC_UBUNTU"

    initNativeLogSystem(system)
    
    logging.debug(systemInfo)
    
    initComponents()
    
    if(parseCommandLine() == False):
        
        return    
    
    calculateStats()
        
    createSubWindows()
        
    mainLoop(stdscr)



wrapper(main)

print(exitMessage)