#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#######################################################################
#
# FileBrowserVTI for VU+ by markusw and schomi (c)2013
# www.vuplus-support.org
#
# This plugin is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
# or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#
# This plugin is NOT free software. It is open source, you are allowed to
# modify it (if you keep the license), but it may not be commercially
# distributed other than under the conditions noted above.
#
# FilebrowserVTI 20140512 v1.2-r1
####################################################################### 

from Plugins.Plugin import PluginDescriptor
# Components
from Components.config import config, ConfigSubList, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, getConfigListEntry, ConfigSelection, NoSave, ConfigNothing
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.FileTransfer import FileTransferJob
from Components.Task import job_manager
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Scanner import openFile
from Components.MenuList import MenuList
# Screens
from Screens.Screen import Screen
from Screens.Console import Console
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.LocationBox import MovieLocationBox
from Screens.HelpMenu import HelpableScreen
from Screens.TaskList import TaskListScreen
from Screens.InfoBar import MoviePlayer as Movie_Audio_Player
# Tools
from Tools.Directories import *
from Tools.BoundFunction import boundFunction
#from Tools.HardwareInfo import HardwareInfo
# Various
from os.path import isdir as os_path_isdir
from mimetypes import guess_type
from enigma import eServiceReference, eServiceCenter, eTimer, eSize, eConsoleAppContainer, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER
from os import listdir, remove, rename, system, path, symlink, chdir
from os import system as os_system
from os import stat as os_stat
from os import walk as os_walk
from os import popen as os_popen
from os import path as os_path
from os import listdir as os_listdir
from time import strftime as time_strftime
from time import localtime as time_localtime

import os
# System mods
from InputBoxmod import InputBox
from FileListmod import FileList, MultiFileSelectList
# Addons
from Plugins.Extensions.FilebrowserVTi.addons.key_actions import *
from Plugins.Extensions.FilebrowserVTi.addons.type_utils import *
from __init__ import _

MOVIEEXTENSIONS = {"cuts": "movieparts","meta": "movieparts","ap": "movieparts","sc": "movieparts","eit": "movieparts"}

movie = "(?i)^.*\.(ts|iso|avi|divx|m4v|mpg|mpeg|mkv|mp4|mov|flv|m2ts|mts|3gp|3g2|wmv)"
music = "(?i)^.*\.(m4a|mp2|mp3|wav|ogg|flac|wma)"
pictures = "(?i)^.*\.(jpg|jpeg|jpe|bmp|png|gif)"
records = "(?i)^.*\.(ts)"
##################################

pname = _("Filebrowser VTi")
pdesc = _("manage local Files")
pversion = "1.2-r1"

config.plugins.filebrowservti = ConfigSubsection()
config.plugins.filebrowservti.savedir_left = ConfigYesNo(default = True)
config.plugins.filebrowservti.savedir_right = ConfigYesNo(default = True)
config.plugins.filebrowservti.add_mainmenu_entry = ConfigYesNo(default = True)
config.plugins.filebrowservti.add_extensionmenu_entry = ConfigYesNo(default = True)
config.plugins.filebrowservti.path_default = ConfigText(default = "/")
config.plugins.filebrowservti.path_left = ConfigText(default = "/")
config.plugins.filebrowservti.path_right = ConfigText(default = "/")
config.plugins.filebrowservti.my_extension = ConfigText(default = "", visible_width = 15, fixed_size = False)
config.plugins.filebrowservti.extension = ConfigSelection(default = "^.*", choices = [("^.*", _("without")),("myfilter", _("My Extension")), (records, _("Records")), (movie, _("Movie")), (music, _("Music")), (pictures, _("Pictures"))])
config.plugins.filebrowservti.input_length = ConfigInteger(default = 40, limits = (1, 100))
config.plugins.filebrowservti.diashow = ConfigInteger(default = 5000, limits = (1000, 10000))
config.plugins.filebrowservti.fake_entry = NoSave(ConfigNothing())

config.plugins.filebrowservti.path_left_tmp = ConfigText(default = config.plugins.filebrowservti.path_left.value)
config.plugins.filebrowservti.path_right_tmp = ConfigText(default = config.plugins.filebrowservti.path_right.value)
config.plugins.filebrowservti.path_left_selected = ConfigYesNo(default = True)
config.plugins.filebrowservti.sorted = ConfigInteger(default = 0, limits = (1, 2))

#####################
### Config Screen ###
#####################
class FilebrowserConfigScreenVTi(Screen, ConfigListScreen):
	ALLOW_SUSPEND = True
	
	skin = """
		<screen position="40,80" size="1200,600" title="" >
			<widget name="config" position="10,50" size="1180,450" scrollbarMode="showOnDemand"/>
			<widget name="help" position="10,10" size="1180,25" font="Regular;20" foregroundColor="#00fff000"/>
			<widget name="key_red" position="100,570" size="260,25" transparent="1" font="Regular;20"/>
			<widget name="key_green" position="395,570" size="260,25"  transparent="1" font="Regular;20"/>
			<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_red.png" transparent="1" alphatest="on"/>
			<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_green.png" transparent="1" alphatest="on"/>
			<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_yellow.png" transparent="1" alphatest="on"/>
			<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_blue.png" transparent="1" alphatest="on"/>
		</screen>"""
		
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.list = []
		self.list.append(getConfigListEntry(_("Add plugin to Mainmenu"), config.plugins.filebrowservti.add_mainmenu_entry))
		self.list.append(getConfigListEntry(_("Add plugin to Extensionmenu"), config.plugins.filebrowservti.add_extensionmenu_entry))
		self.list.append(getConfigListEntry(_("Save left folder on exit (%s)") % config.plugins.filebrowservti.path_left_tmp.value, config.plugins.filebrowservti.savedir_left))
		self.list.append(getConfigListEntry(_("Save right folder on exit (%s)") % config.plugins.filebrowservti.path_right_tmp.value, config.plugins.filebrowservti.savedir_right))
		self.get_folder = getConfigListEntry(_("Default folder"), config.plugins.filebrowservti.path_default)
		self.list.append(self.get_folder)		
		self.list.append(getConfigListEntry(_("My extension"), config.plugins.filebrowservti.my_extension))
		self.list.append(getConfigListEntry(_("Filter extension, (*) appears in title"), config.plugins.filebrowservti.extension))
		self.list.append(getConfigListEntry(_("Input length - Filename"), config.plugins.filebrowservti.input_length))
		self.list.append(getConfigListEntry(_("Time for Slideshow"), config.plugins.filebrowservti.diashow))
		
		ConfigListScreen.__init__(self, self.list, session = session)
		self["help"] = Label(_("Select your personal settings:"))
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Ok"))
		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"green": self.save,
			"red": self.cancel,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.ok,
		}, -2)
		self.onLayoutFinish.append(self.onLayout)

	def onLayout(self):
		self.setTitle(pname+" ("+pversion+") "+_("Settings"))

	def ok(self):
		if self["config"].getCurrent() == self.get_folder:			
			self.session.openWithCallback(self.pathSelected, MovieLocationBox, _("Default Folder"), config.plugins.filebrowservti.path_default.value, minFree = 100)

	def pathSelected(self, res):
		if res is not None:
			config.plugins.filebrowservti.path_default.value = res
		
	def save(self):
		print "[Filebrowser VTi]: Settings saved"
		for x in self["config"].list:
			x[1].save()
		self.close(True)

	def cancel(self):
		print "[Filebrowser VTi]: Settings canceled"
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)

###################
### Main Screen ###
###################
class FilebrowserScreenVTi(Screen, key_actions, HelpableScreen):
	ALLOW_SUSPEND = True
	
	skin = """
		<screen position="40,80" size="1200,600" title="" >
			<widget name="list_left_head" position="10,10" size="570,65" font="Regular;20" foregroundColor="#00fff000"/>
			<widget name="list_right_head" position="595,10" size="570,65" font="Regular;20" foregroundColor="#00fff000"/>
			<widget name="list_left" position="10,85" size="570,470" scrollbarMode="showOnDemand"/>
			<widget name="list_right" position="595,85" size="570,470" scrollbarMode="showOnDemand"/>
			<widget name="help" position="500,50" size="600,500" zPosition="5" font="Regular;20" foregroundColor="#00fff000"/>
			<widget name="helpBack" position="498,48" size="604,504" zPosition="4" font="Regular;20" foregroundColor="#00ffffff" backgroundColor="#00ffffff" transparent="0"/>
			<widget name="helpShadow" position="508,58" size="604,504" zPosition="3" font="Regular;20" foregroundColor="#20000000" backgroundColor="#20000000"/>
			<widget name="key_red" position="100,570" size="260,25" transparent="1" font="Regular;20"/>
			<widget name="key_green" position="395,570" size="260,25"  transparent="1" font="Regular;20"/>
			<widget name="key_yellow" position="690,570" size="260,25" transparent="1" font="Regular;20"/>
			<widget name="key_blue" position="985,570" size="260,25" transparent="1" font="Regular;20"/>
			<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_red.png" transparent="1" alphatest="on"/>
			<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_green.png" transparent="1" alphatest="on"/>
			<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_yellow.png" transparent="1" alphatest="on"/>
			<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_blue.png" transparent="1" alphatest="on"/>
		</screen>"""
		
	def __init__(self, session,path_left=None):
		if path_left is None:
			if os_path_isdir(config.plugins.filebrowservti.path_left.value) and config.plugins.filebrowservti.savedir_left:
				path_left = config.plugins.filebrowservti.path_left.value
			else:
				path_left = config.plugins.filebrowservti.path_default.value
			
		if os_path_isdir(config.plugins.filebrowservti.path_right.value) and config.plugins.filebrowservti.savedir_right:
			path_right = config.plugins.filebrowservti.path_right.value
		else:
			path_right = config.plugins.filebrowservti.path_default.value

		self.session = session
		Screen.__init__(self, session)
		
		# set filter
		if config.plugins.filebrowservti.extension.value == "myfilter":
			filter = "^.*\.%s" % config.plugins.filebrowservti.my_extension.value
		else:
			filter = config.plugins.filebrowservti.extension.value
			
		# set actual folder
		HelpableScreen.__init__(self)
		self["list_left_head"] = Label(path_left)
		self["list_left_head_name"] = Label()
		self["list_left_head_state"] = Label()
		self["list_right_head"] = Label(path_right)
		self["list_right_head_name"] = Label()
		self["list_right_head_state"] = Label()
		self["list_left"] = FileList(path_left, matchingPattern = filter)
		self["list_right"] = FileList(path_right, matchingPattern = filter)

		self["help"] = Label(_("Help:\nKey [0] Refresh screen.\nKey [1] New folder.\nKey [2] New symlink wit name.\nKey [3] New symlink with foldername.\nKey [4] User rights 644/755.\nKey [5] Change to default folder. \nKey [8] Toggle sort direction up, down. \nKey [9] Toggle Quick-Help. \nKey [R] Select multiple files. \nKey [OK] Play movie and music, show pictures, view/edit files, install/extract files, run scripts. \nKey [EPG] Shows tasklist. Check copy/move progress in extensions menu. \nKey [TXT] View/Edit selected file. \nKey [Help] Shows Help."))
		self["helpBack"] = Label()
		self["helpShadow"] = Label()
		self['help'].hide()
		self['helpBack'].hide()
		self['helpShadow'].hide()
		helpOn = 0
		self.helpOn = helpOn
		
		self["key_red"] = Label(_("Delete"))
		self["key_green"] = Label(_("Move"))
		self["key_yellow"] = Label(_("Copy"))
		self["key_blue"] = Label(_("Rename"))

		self["ChannelSelectBaseActions"] = HelpableActionMap(self,"ChannelSelectBaseActions",
			{
				"prevBouquet": (self.listLeft, _("Select left window")),
				"nextBouquet": (self.listRight, _("Select right window")),
				"prevMarker": self.listLeft,
				"nextMarker": self.listRight,
			}, -1)

		self["WizardActions"] = HelpableActionMap(self, "WizardActions", 
			{
				"ok": (self.ok, _("Play movie & music, show pictures, view/edit files, install/extract files, run scripts")),
				"back": (self.exit,_("Exit")),
				"up": (self.goUp, _("Selection up")),
				"down": (self.goDown, _("Selection down")),
				"left": (self.goLeft, _("Page up")),
				"right": (self.goRight, _("Page down")),
			}, -1)

		self["MenuActions"] = HelpableActionMap(self, "MenuActions", 
			{
				"menu": (self.goMenu, _("Settings")),
			}, -1)

		self["NumberActions"] = HelpableActionMap(self, "NumberActions", 
			{
				"0": (self.doRefresh, _("Refresh screen")),
				"1": (self.gomakeDir, _("New folder")),
				"2": (self.gomakeSym, _("New symlink with name")),
				"3": (self.gomakeSymlink, _("New symlink with foldername")),
				"4": (self.call_change_mode, _("User rights 644/755")),
				"5": (self.goDefaultfolder, _("Change to default folder")),
				"8": (self.sortMode, _("Toggle sort direction up, down")),
				"9": (self.QuickHelp, _("Toogle Quick-Help")),
			}, -1)

		self["ColorActions"] = HelpableActionMap(self, "ColorActions", 
			{
				"red": (self.goRed, _("Delete")),
				"green": (self.goGreen, _("Move")),
				"yellow": (self.goYellow, _("Copy")),
				"blue": (self.goBlue, _("Rename")),
			}, -1)

		self["TimerEditActions"] = HelpableActionMap(self, "TimerEditActions", 
			{
				"eventview": (self.openTasklist, _("Show tasklist. Check copy/move progress in extensions menu")),
			}, -1)

		self["InfobarTeletextActions"] = HelpableActionMap(self, "InfobarTeletextActions", 
			{
				"startTeletext": (self.file_viewer, _("View/Edit files")),
			}, -1)

		self["InfobarActions"] = HelpableActionMap(self, "InfobarActions", 
			{
				"showMovies": (self.listSelect,  _("Multiselection list")),
			}, -1)

		if config.plugins.filebrowservti.path_left_selected:
			self.onLayoutFinish.append(self.listLeft)
		else:
			self.onLayoutFinish.append(self.listRight)

		self.onLayoutFinish.append(self.onLayout)

	def onLayout(self):
		if config.plugins.filebrowservti.extension.value == "^.*":
			filtered = ""
		else:
			filtered = "(*)"
		self.setTitle(pname + filtered)
		
	def sortMode(self):
		if config.plugins.filebrowservti.sorted.value == 0:
			config.plugins.filebrowservti.sorted.value = 1
		else:
			config.plugins.filebrowservti.sorted.value = 0
		self.SOURCELIST.refresh()

	def QuickHelp(self):
		if self.helpOn == 0:
			self['help'].show()
			self['helpBack'].show()
			self['helpShadow'].show()
			self.helpOn = 1
		else:
			self['help'].hide()
			self['helpBack'].hide()
			self['helpShadow'].hide()
			self.helpOn = 0
		
	def file_viewer(self):
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		if (filename == None) or (sourceDir == None):
		  return
		longname = sourceDir + filename
		try:
			xfile=os_stat(longname)
			if (xfile.st_size < 1000000):
				self.session.open(vEditor, longname)
				self.onFileActionCB(True)
		except:
			return
		
	def exit(self):
		if self["list_left"].getCurrentDirectory() and config.plugins.filebrowservti.savedir_left.value:
			config.plugins.filebrowservti.path_left.value = self["list_left"].getCurrentDirectory()
			config.plugins.filebrowservti.path_left.save()
		else:
			config.plugins.filebrowservti.path_left.value = config.plugins.filebrowservti.path_default.value

		if self["list_right"].getCurrentDirectory() and config.plugins.filebrowservti.savedir_right.value:
			config.plugins.filebrowservti.path_right.value = self["list_right"].getCurrentDirectory()
			config.plugins.filebrowservti.path_right.save()
		else:
			config.plugins.filebrowservti.path_right.value = config.plugins.filebrowservti.path_default.value

		self.close(self.session, True)

	def ok(self):
		if self.SOURCELIST.canDescent(): # isDir
			self.SOURCELIST.descent()			
			if self.SOURCELIST == self["list_right"]:
				self["list_left_head"].setText(self.TARGETLIST.getCurrentDirectory())
				self["list_right_head"].setText(self.SOURCELIST.getCurrentDirectory())
			else:
				self["list_left_head"].setText(self.SOURCELIST.getCurrentDirectory())
				self["list_right_head"].setText(self.TARGETLIST.getCurrentDirectory())	
			self.updateHead()
		else:
			self.onFileAction(self.SOURCELIST, self.TARGETLIST)
			self.doRefresh()

	def goMenu(self):
		config.plugins.filebrowservti.path_left_tmp.value = self["list_left"].getCurrentDirectory()
		config.plugins.filebrowservti.path_right_tmp.value = self["list_right"].getCurrentDirectory()		
		self.session.openWithCallback(self.goRestart, FilebrowserConfigScreenVTi)

	def goDefaultfolder(self):
		self.SOURCELIST.changeDir(config.plugins.filebrowservti.path_default.value)
		self["list_left_head"].setText(self["list_left"].getCurrentDirectory())
		self["list_right_head"].setText(self["list_right"].getCurrentDirectory())
		
	def goRestart(self, answer):
		config.plugins.filebrowservti.path_left.value = config.plugins.filebrowservti.path_left_tmp.value
		config.plugins.filebrowservti.path_right.value = config.plugins.filebrowservti.path_right_tmp.value
		self.close(self.session, False)
		 
	def goLeft(self):
		self.SOURCELIST.pageUp()
		self.updateHead()

	def goRight(self):
		self.SOURCELIST.pageDown()
		self.updateHead()

	def goUp(self):
		self.SOURCELIST.up()
		self.updateHead()

	def goDown(self):
		self.SOURCELIST.down()
		self.updateHead()

### Multiselect ###		
	def listSelect(self):
		selectedid = self.SOURCELIST.getSelectionID()
		config.plugins.filebrowservti.path_left_tmp.value = self["list_left"].getCurrentDirectory()
		config.plugins.filebrowservti.path_right_tmp.value = self["list_right"].getCurrentDirectory()
		if self.SOURCELIST == self["list_left"]:
			leftactive = True
		else:
			leftactive = False
			
		self.session.openWithCallback(self.doRefreshDir, FilebrowserScreenFileSelectVTi, leftactive, selectedid)
		self.updateHead()
		
	def openTasklist(self):
		self.tasklist = []
		for job in job_manager.getPendingJobs():
			self.tasklist.append((job,job.name,job.getStatustext(),int(100*job.progress/float(job.end)) ,str(100*job.progress/float(job.end)) + "%" ))
		self.session.open(TaskListScreen, self.tasklist)

### copy ###
	def goYellow(self):
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		targetDir = self.TARGETLIST.getCurrentDirectory()
		if (filename == None) or (sourceDir == None) or (targetDir == None):
		  return
		if not sourceDir in filename:
		   copytext = _("copy file - existing file will be overwritten !")
		else:
		   copytext = _("copy folder - existing folders/files will be overwritten !")
		self.session.openWithCallback(self.doCopy,ChoiceBox, title = copytext+"?\n%s\nfrom\n%s\n%s"%(filename,sourceDir,targetDir),list=[(_("yes"), True ),(_("no"), False )])

	def doCopy(self,result):
		if result is not None:
			if result[1]:
				filename = self.SOURCELIST.getFilename()
				sourceDir = self.SOURCELIST.getCurrentDirectory()
				targetDir = self.TARGETLIST.getCurrentDirectory()
				dst_file = targetDir
				if dst_file.endswith("/"):
				  targetDir = dst_file[:-1]
				if not sourceDir in filename:
				  job_manager.AddJob(FileTransferJob(sourceDir+filename, targetDir, False, True,  "%s : %s" % (_("copy file"), sourceDir+filename)))
				  self.doCopyCB()
				else:
				  job_manager.AddJob(FileTransferJob(filename, targetDir, True, True,  "%s : %s" % (_("copy folder"), filename)))
				  self.doCopyCB()

	def doCopyCB(self):
		self.doRefresh()

### delete ###
	def goRed(self):
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		if (filename == None) or (sourceDir == None):
		  return
		if not sourceDir in filename:
		   deltext = _("delete file")
		else:
		   deltext = _("delete folder")
		self.session.openWithCallback(self.doDelete,ChoiceBox, title = deltext+"?\n%s\nfrom dir\n%s"%(filename,sourceDir),list=[(_("yes"), True ),(_("no"), False )])

	def doDelete(self,result):
		if result is not None:
			if result[1]:
				filename = self.SOURCELIST.getFilename()
				sourceDir = self.SOURCELIST.getCurrentDirectory()
				if not sourceDir in filename:
				  self.session.openWithCallback(self.doDeleteCB,Console, title = _("deleting file ..."), cmdlist = ["rm \""+sourceDir+filename+"\""])
				else:
				  self.session.openWithCallback(self.doDeleteCB,Console, title = _("deleting folder ..."), cmdlist = ["rm -rf \""+filename+"\""])

	def doDeleteCB(self):
		self.doRefresh()

### move ###
	def goGreen(self):
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		targetDir = self.TARGETLIST.getCurrentDirectory()
		if (filename == None) or (sourceDir == None) or (targetDir == None):
		  return
		if not sourceDir in filename:
		   movetext = _("move file")
		else:
		   movetext = _("move folder")
		self.session.openWithCallback(self.doMove,ChoiceBox, title = movetext+"?\n%s\nfrom dir\n%s\nto dir\n%s"%(filename,sourceDir,targetDir),list=[(_("yes"), True ),(_("no"), False )])

	def doMove(self,result):
		if result is not None:
			if result[1]:
				filename = self.SOURCELIST.getFilename()
				sourceDir = self.SOURCELIST.getCurrentDirectory()
				targetDir = self.TARGETLIST.getCurrentDirectory()
				dst_file = targetDir
				if dst_file.endswith("/"):
				  targetDir = dst_file[:-1]
				if not sourceDir in filename:
				  job_manager.AddJob(FileTransferJob(sourceDir+filename, targetDir, False, False,  "%s : %s" % (_("move file"), sourceDir+filename)))
				  self.doMoveCB()
				else:
				  job_manager.AddJob(FileTransferJob(filename, targetDir, True, False,  "%s : %s" % (_("move folder"), filename)))
				  self.doMoveCB()

	def doMoveCB(self):
		self.doRefresh()

### rename ###
	def goBlue(self):
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		length = config.plugins.filebrowservti.input_length.value
		if (filename == None) or (sourceDir == None):
		  return
		self.session.openWithCallback(self.doRename,InputBox,text=filename, visible_width=length, overwrite=False, firstpos_end=True, allmarked=False, title = _("Please enter file/folder name"), windowTitle=_("rename file"))
		#overwrite : False = Einfügemodus beim Aufruf der Inputbox
		#firstpos_end : True = Cursor beim Aufruf am Textende - False = Cursor am Textanfang
		#visible_width : wenn der Wert kleiner der Skin-Eingabegrösse für den Text ist, wird gescrollt falls der Text zu lange ist
		#allmarked : Text beim Aufruf markiert oder nicht

	def doRename(self,newname):
		if newname:
			filename = self.SOURCELIST.getFilename()
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			if not sourceDir in filename:
			  self.session.openWithCallback(self.doRenameCB,Console, title = _("renaming file ..."), cmdlist = ["mv \""+sourceDir+filename+"\" \""+sourceDir+newname+"\""])
			else:
			  self.session.openWithCallback(self.doRenameCB,Console, title = _("renaming folder ..."), cmdlist = ["mv \""+filename+"\" \""+newname+"\""])

	def doRenameCB(self):
		self.doRefresh()

### symlink by name ###
	def gomakeSym(self):
	  filename = self.SOURCELIST.getFilename()
	  sourceDir = self.SOURCELIST.getCurrentDirectory()
	  if (filename == None) or (sourceDir == None):
		return
	  self.session.openWithCallback(self.doMakesym,InputBox,text="", title =  _("Please enter name of the new symlink"), windowTitle =_("New symlink"))

	def doMakesym(self,newname):
	  if newname:
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		targetDir = self.TARGETLIST.getCurrentDirectory()
		#self.session.openWithCallback(self.doMakesymCB,Console, title = _("create symlink"), cmdlist = ["ln -s \""+sourceDir+"\" \""+targetDir+newname+"\""])
		symlink(sourceDir, targetDir+newname)
		self.doRefresh()
		
	def doMakesymCB(self):
	  self.doRefresh()

### symlink by folder ###
	def gomakeSymlink(self):
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		targetDir = self.TARGETLIST.getCurrentDirectory()
		if not sourceDir in filename:
		   movetext = _("create symlink to file")
		else:
		   movetext = _("symlink to ")
		testfile = filename[:-1]
		test = path.islink(testfile)
		if (filename == None) or (sourceDir == None):
			return
		if path.islink(testfile):
			return
		self.session.openWithCallback(self.domakeSymlink,ChoiceBox, title = movetext+" %s in %s"%(filename,targetDir),list=[(_("yes"), True ),(_("no"), False )])

	def domakeSymlink(self,result):
		if result is not None:
		  if result[1]:
			filename = self.SOURCELIST.getFilename()
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			targetDir = self.TARGETLIST.getCurrentDirectory()
			if not sourceDir in filename:
				return
				self.session.openWithCallback(self.doRenameCB,Console, title = _("renaming file ..."), cmdlist = ["mv \""+sourceDir+filename+"\" \""+sourceDir+newname+"\""])
				symlink(sourceDir, targetDir+newname)
			else:
				self.session.openWithCallback(self.doRenameCB,Console, title = _("renaming folder ..."), cmdlist = ["ln -s \""+filename+"\" \""+targetDir+"\""])
		self.doRefresh()
		
### new folder ###
	def gomakeDir(self):
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		if (filename == None) or (sourceDir == None):
		  return
		self.session.openWithCallback(self.doMakedir,InputBox,text="", title =  _("Please enter name of the new directory"), windowTitle =_("new folder"))

	def doMakedir(self,newname):
		if newname:
			filename = self.SOURCELIST.getFilename()
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			#self.session.openWithCallback(self.doMakedirCB,Console, title = _("create folder"), cmdlist = ["mkdir \""+sourceDir+newname+"\""])
			mkdir(sourceDir+newname)
			self.doRefresh()
			
	def doMakedirCB(self):
		self.doRefresh()

### basic functions ###
	def updateHead(self):
		text_target = self.Info(self.TARGETLIST)
		text_source = self.Info(self.SOURCELIST)
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		targetDir = self.TARGETLIST.getCurrentDirectory()
		if self.SOURCELIST == self["list_right"]:
			if targetDir is not None:
				self["list_left_head"].setText(self.TARGETLIST.getCurrentDirectory() + text_target)
				if self.TARGETLIST.getFilename()!= None:
					if '/' in self.TARGETLIST.getFilename() and text_target != "":
						self["list_left_head_name"].setText(self.TARGETLIST.getFilename())
					elif text_target == "":
						self["list_left_head_name"].setText(targetDir)
					else:
						self["list_left_head_name"].setText(targetDir + self.TARGETLIST.getFilename())
				else:
					self["list_left_head_name"].setText(self.TARGETLIST.getCurrentDirectory())
			else:
				self["list_left_head_name"].setText(self.TARGETLIST.getFilename())
			self["list_left_head_state"].setText(text_target.partition('   ')[-1])
			if sourceDir is not None:
				self["list_right_head"].setText(self.SOURCELIST.getCurrentDirectory() + text_source)
				if self.SOURCELIST.getFilename()!= None:
					if '/' in self.SOURCELIST.getFilename() and text_source != "":
						self["list_right_head_name"].setText(self.SOURCELIST.getFilename())
					elif text_source == "":
						self["list_right_head_name"].setText(sourceDir)
					else:
						self["list_right_head_name"].setText(sourceDir + self.SOURCELIST.getFilename())
				else:
					self["list_right_head_name"].setText(self.SOURCELIST.getCurrentDirectory())
			else:
				self["list_right_head_name"].setText(self.SOURCELIST.getFilename())
			self["list_right_head_state"].setText(text_source.partition('   ')[-1])
				
		else:
			if sourceDir is not None:
				self["list_left_head"].setText(self.SOURCELIST.getCurrentDirectory() + text_source)
				if self.SOURCELIST.getFilename()!= None:
					if '/' in self.SOURCELIST.getFilename() and text_source != "":
						self["list_left_head_name"].setText(self.SOURCELIST.getFilename())
					elif text_source == "":
						self["list_left_head_name"].setText(sourceDir)
					else:
						self["list_left_head_name"].setText(sourceDir + self.SOURCELIST.getFilename())
				else:
					self["list_left_head_name"].setText(self.SOURCELIST.getCurrentDirectory())
			else:
				self["list_left_head_name"].setText(self.SOURCELIST.getFilename())
			self["list_left_head_state"].setText(text_source.partition('   ')[-1])
			if targetDir is not None:
				self["list_right_head"].setText(self.TARGETLIST.getCurrentDirectory() + text_target)	
				if self.TARGETLIST.getFilename()!= None:
					if '/' in self.TARGETLIST.getFilename() and text_target != "":
						self["list_right_head_name"].setText(self.TARGETLIST.getFilename())
					elif text_target == "":
						self["list_right_head_name"].setText(targetDir)
					else:
						self["list_right_head_name"].setText(targetDir + self.TARGETLIST.getFilename())
				else:
					self["list_right_head_name"].setText(self.TARGETLIST.getCurrentDirectory())
			else:
				self["list_right_head_name"].setText(self.TARGETLIST.getFilename())
			self["list_right_head_state"].setText(text_target.partition('   ')[-1])

	def doRefreshDir(self):
		self["list_left"].changeDir(config.plugins.filebrowservti.path_left_tmp.value)
		self["list_right"].changeDir(config.plugins.filebrowservti.path_right_tmp.value)
		if self.SOURCELIST == self["list_left"]:
			self["list_left"].selectionEnabled(1)
			self["list_right"].selectionEnabled(0)
		else:
			self["list_left"].selectionEnabled(0)
			self["list_right"].selectionEnabled(1)
		self.updateHead()

	def doRefresh(self):
		self.SOURCELIST.refresh()
		self.TARGETLIST.refresh()
		self.updateHead()

	def listRight(self):
		self["list_left"].selectionEnabled(0)
		self["list_right"].selectionEnabled(1)
		self.SOURCELIST = self["list_right"]
		self.TARGETLIST = self["list_left"]
		self.doRefresh()

	def listLeft(self):
		self["list_left"].selectionEnabled(1)
		self["list_right"].selectionEnabled(0)
		self.SOURCELIST = self["list_left"]
		self.TARGETLIST = self["list_right"]
		self.doRefresh()

	def call_change_mode(self):
		self.change_mod(self.SOURCELIST)

#####################			
### Select Screen ###
#####################
class FilebrowserScreenFileSelectVTi(Screen, key_actions, HelpableScreen):
	ALLOW_SUSPEND = True
	
	skin = """
		<screen position="40,80" size="1200,600" title="" >
			<widget name="list_left_head" position="10,10" size="570,65" font="Regular;20" foregroundColor="#00fff000"/>
			<widget name="list_right_head" position="595,10" size="570,65" font="Regular;20" foregroundColor="#00fff000"/>
			<widget name="list_left" position="10,85" size="570,470" scrollbarMode="showOnDemand"/>
			<widget name="list_right" position="595,85" size="570,470" scrollbarMode="showOnDemand"/>
			<widget name="key_red" position="100,570" size="260,25" transparent="1" font="Regular;20"/>
			<widget name="key_green" position="395,570" size="260,25"  transparent="1" font="Regular;20"/>
			<widget name="key_yellow" position="690,570" size="260,25" transparent="1" font="Regular;20"/>
			<widget name="key_blue" position="985,570" size="260,25" transparent="1" font="Regular;20"/>
			<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_red.png" transparent="1" alphatest="on"/>
			<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_green.png" transparent="1" alphatest="on"/>
			<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_yellow.png" transparent="1" alphatest="on"/>
			<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FilebrowserVTi/pic/button_blue.png" transparent="1" alphatest="on"/>
		</screen>"""
		
	def __init__(self, session, leftactive, selectedid):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		
		self.selectedFiles = []
		self.selectedid = selectedid

		path_left = config.plugins.filebrowservti.path_left_tmp.value
		path_right = config.plugins.filebrowservti.path_right_tmp.value

		# set filter
		if config.plugins.filebrowservti.extension.value == "myfilter":
			filter = "^.*\.%s" % config.plugins.filebrowservti.my_extension.value
		else:
			filter = config.plugins.filebrowservti.extension.value
		
		# set actuall folder
		self["list_left_head"] = Label(path_left)
		self["list_right_head"] = Label(path_right)
		self["list_left_head_name"] = Label()
		self["list_left_head_state"] = Label()
		self["list_right_head_name"] = Label()
		self["list_right_head_state"] = Label()

		if leftactive:
			self["list_left"] = MultiFileSelectList(self.selectedFiles, path_left, matchingPattern = filter)
			self["list_right"] = FileList(path_right, matchingPattern = filter)
			self.SOURCELIST = self["list_left"]
			self.TARGETLIST = self["list_right"]
			self.listLeft()
		else:
			self["list_left"] = FileList(path_left, matchingPattern = filter)
			self["list_right"] = MultiFileSelectList(self.selectedFiles, path_right, matchingPattern = filter)
			self.SOURCELIST = self["list_right"]
			self.TARGETLIST = self["list_left"]
			self.listRight()

		self["key_red"] = Label(_("Delete"))
		self["key_green"] = Label(_("Move"))
		self["key_yellow"] = Label(_("Copy"))
		self["key_blue"] = Label(_("Skip selection"))

		self["ChannelSelectBaseActions"] = HelpableActionMap(self,"ChannelSelectBaseActions",
			{
				"prevBouquet": (self.listLeft, _("Select left window")),
				"nextBouquet": (self.listRight, _("Select right window")),
				"prevMarker": self.listLeft,
				"nextMarker": self.listRight,
			}, -1)

		self["WizardActions"] = HelpableActionMap(self, "WizardActions", 
			{
				"ok": (self.ok, _("Select / Unselect")),
				"back": (self.exit,_("Exit")),
				"up": (self.goUp, _("Selection up")),
				"down": (self.goDown, _("Selection down")),
				"left": (self.goLeft, _("Page up")),
				"right": (self.goRight, _("Page down")),
			}, -1)

		self["NumberActions"] = HelpableActionMap(self, "NumberActions", 
			{
				"0": (self.doRefresh, _("Refresh screen")),
				"8": (self.sortMode, _("Toggle sort direction up, down")),
			}, -1)

		self["ColorActions"] = HelpableActionMap(self, "ColorActions", 
			{
				"red": (self.goRed, _("Delete")),
				"green": (self.goGreen, _("Move")),
				"yellow": (self.goYellow, _("Copy")),
				"blue": (self.goBlue, _("Skip selection")),
			}, -1)

		self["TimerEditActions"] = HelpableActionMap(self, "TimerEditActions", 
			{
				"eventview": (self.openTasklist, _("Show tasklist. Check copy/move progress in extensions menu")),
			}, -1)

		self["InfobarActions"] = HelpableActionMap(self, "InfobarActions", 
			{
				"showMovies": (self.changeSelectionState,  _("Select/Unselect")),
			}, -1)
		self.onLayoutFinish.append(self.onLayout)

	def onLayout(self):
		if config.plugins.filebrowservti.extension.value == "^.*":
			filtered = ""
		else:
			filtered = "(*)"
		self.setTitle(pname + filtered +_("(Selectmode)"))
		self.SOURCELIST.moveToIndex(self.selectedid)
		self.updateHead()

	def sortMode(self):
		if config.plugins.filebrowservti.sorted.value == 0:
			config.plugins.filebrowservti.sorted.value = 1
		else:
			config.plugins.filebrowservti.sorted.value = 0
		self.SOURCELIST.refresh()

	def changeSelectionState(self):
		if self.ACTIVELIST == self.SOURCELIST:
			self.ACTIVELIST.changeSelectionState()
			self.selectedFiles = self.ACTIVELIST.getSelectedList()
			print self.selectedFiles
			self.goDown()
				
	def exit(self):
		config.plugins.filebrowservti.path_left_tmp.value = self["list_left"].getCurrentDirectory()
		config.plugins.filebrowservti.path_right_tmp.value = self["list_right"].getCurrentDirectory()
		self.close()

	def ok(self):
	
		if self.ACTIVELIST == self.SOURCELIST:
			self.changeSelectionState()
		else:
			if self.ACTIVELIST.canDescent(): # isDir
				self.ACTIVELIST.descent()		
			if self.ACTIVELIST == self["list_right"]:
				self["list_left_head"].setText(self.TARGETLIST.getCurrentDirectory())
				self["list_right_head"].setText(self.SOURCELIST.getCurrentDirectory())
			else:
				self["list_left_head"].setText(self.SOURCELIST.getCurrentDirectory())
				self["list_right_head"].setText(self.TARGETLIST.getCurrentDirectory())	
			
	def goMenu(self):
		self.session.open(FilebrowserConfigScreenVTi)
		 
	def goLeft(self):
		self.ACTIVELIST.pageUp()
		self.updateHead()
		
	def goRight(self):
		self.ACTIVELIST.pageDown()
		self.updateHead()

	def goUp(self):
		self.ACTIVELIST.up()
		self.updateHead()
		
	def goDown(self):
		self.ACTIVELIST.down()
		self.updateHead()
		
	def openTasklist(self):
		self.tasklist = []
		for job in job_manager.getPendingJobs():
			self.tasklist.append((job,job.name,job.getStatustext(),int(100*job.progress/float(job.end)) ,str(100*job.progress/float(job.end)) + "%" ))
		self.session.open(TaskListScreen, self.tasklist)		
		
### delete select ###
	def goRed(self):
		for file in self.selectedFiles:
			if os_path_isdir(file):
				container = eConsoleAppContainer()
				container.execute("rm -rf '%s'" % file)
			else:
				remove(file)
		self.exit()

### move select ###
	def goGreen(self):
		targetDir = self.TARGETLIST.getCurrentDirectory()

		for file in self.selectedFiles:
			extension = file.split('.')
			extension = extension[-1].lower()
			if MOVIEEXTENSIONS.has_key(extension):
				print "[Moviebrowser]: skip " +extension
			else:
				print "[Moviebrowser]: copy " +extension
				dst_file = targetDir
				if dst_file.endswith("/"):
					targetDir = dst_file[:-1]
				job_manager.AddJob(FileTransferJob(file, targetDir, False, False,  "%s : %s" % (_("move file"),file)))
		self.exit()

### copy select ###
	def goYellow(self):
		targetDir = self.TARGETLIST.getCurrentDirectory()

		for file in self.selectedFiles:
			extension = file.split('.')
			extension = extension[-1].lower()
			if MOVIEEXTENSIONS.has_key(extension):
				print "[Moviebrowser]: skip " +extension
			else:
				print "[Moviebrowser]: copy " +extension
				dst_file = targetDir
				if dst_file.endswith("/"):
					targetDir = dst_file[:-1]
				if file.endswith("/"):
					job_manager.AddJob(FileTransferJob(file, targetDir, True, True,  "%s : %s" % (_("copy folder"),file)))				
				else:
					job_manager.AddJob(FileTransferJob(file, targetDir, False, True,  "%s : %s" % (_("copy file"),file)))				
		self.exit()
		
	def goBlue(self):	
		self.exit()
		
### basic functions ###
	def updateHead(self):
		text_target = self.Info(self.TARGETLIST)
		text_source = self.Info(self.SOURCELIST)
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		targetDir = self.TARGETLIST.getCurrentDirectory()
		if self.SOURCELIST == self["list_right"]:
			if targetDir is not None:
				self["list_left_head"].setText(self.TARGETLIST.getCurrentDirectory() + text_target)
				if self.TARGETLIST.getFilename()!= None:
					if '/' in self.TARGETLIST.getFilename() and text_target != "":
						self["list_left_head_name"].setText(self.TARGETLIST.getFilename())
					elif text_target == "":
						self["list_left_head_name"].setText(targetDir)
					else:
						self["list_left_head_name"].setText(targetDir + self.TARGETLIST.getFilename())
				else:
					self["list_left_head_name"].setText(self.TARGETLIST.getCurrentDirectory())
			else:
				self["list_left_head_name"].setText(self.TARGETLIST.getFilename())
			self["list_left_head_state"].setText(text_target.partition('   ')[-1])
			if sourceDir is not None:
				self["list_right_head"].setText(self.SOURCELIST.getCurrentDirectory() + text_source)
				if self.SOURCELIST.getFilename()!= None:
					if '/' in self.SOURCELIST.getFilename() and text_source != "":
						self["list_right_head_name"].setText(self.SOURCELIST.getFilename())
					elif text_source == "":
						self["list_right_head_name"].setText(sourceDir)
					else:
						self["list_right_head_name"].setText(sourceDir + self.SOURCELIST.getFilename())
				else:
					self["list_right_head_name"].setText(self.SOURCELIST.getCurrentDirectory())
			else:
				self["list_right_head_name"].setText(self.SOURCELIST.getFilename())
			self["list_right_head_state"].setText(text_source.partition('   ')[-1])
				
		else:
			if sourceDir is not None:
				self["list_left_head"].setText(self.SOURCELIST.getCurrentDirectory() + text_source)
				if self.SOURCELIST.getFilename()!= None:
					if '/' in self.SOURCELIST.getFilename() and text_source != "":
						self["list_left_head_name"].setText(self.SOURCELIST.getFilename())
					elif text_source == "":
						self["list_left_head_name"].setText(sourceDir)
					else:
						self["list_left_head_name"].setText(sourceDir + self.SOURCELIST.getFilename())
				else:
					self["list_left_head_name"].setText(self.SOURCELIST.getCurrentDirectory())
			else:
				self["list_left_head_name"].setText(self.SOURCELIST.getFilename())
			self["list_left_head_state"].setText(text_source.partition('   ')[-1])
			if targetDir is not None:
				self["list_right_head"].setText(self.TARGETLIST.getCurrentDirectory() + text_target)	
				if self.TARGETLIST.getFilename()!= None:
					if '/' in self.TARGETLIST.getFilename() and text_target != "":
						self["list_right_head_name"].setText(self.TARGETLIST.getFilename())
					elif text_target == "":
						self["list_right_head_name"].setText(targetDir)
					else:
						self["list_right_head_name"].setText(targetDir + self.TARGETLIST.getFilename())
				else:
					self["list_right_head_name"].setText(self.TARGETLIST.getCurrentDirectory())
			else:
				self["list_right_head_name"].setText(self.TARGETLIST.getFilename())
			self["list_right_head_state"].setText(text_target.partition('   ')[-1])

	def doRefresh(self):
		print self.selectedFiles
		self.SOURCELIST.refresh()
		self.TARGETLIST.refresh()
		self.updateHead()

	def listRight(self):
		self["list_left"].selectionEnabled(0)
		self["list_right"].selectionEnabled(1)
		self.ACTIVELIST = self["list_right"]
		self.updateHead()

	def listLeft(self):
		self["list_left"].selectionEnabled(1)
		self["list_right"].selectionEnabled(0)
		self.ACTIVELIST = self["list_left"]
		self.updateHead()

######################		
### Start routines ###
######################
def filescan_open(list, session, **kwargs):
	path = "/".join(list[0].path.split("/")[:-1])+"/"
	session.open(FilebrowserScreenVTi,path_left=path)

def start_from_filescan(**kwargs):
	from Components.Scanner import Scanner, ScanPath
	return \
		Scanner(mimetypes= None,
			paths_to_scan =
				[
					ScanPath(path = "", with_subdirs = False),
				],
			name = pname,
			description = _("Open with Filebrowser VTi"),
			openfnc = filescan_open,
		)

def start_from_mainmenu(menuid, **kwargs):
	#starting from main menu
	if menuid == "mainmenu":
		return [(pname, start_from_pluginmenu, "filecommand", 48)]
	return []

def start_from_pluginmenu(session,**kwargs):
	session.openWithCallback(exit, FilebrowserScreenVTi)

def exit(session, result):
	if not result:
		session.openWithCallback(exit, FilebrowserScreenVTi)

def Plugins(path,**kwargs):
	desc_mainmenu  = PluginDescriptor(name=pname, description=pdesc,  where = PluginDescriptor.WHERE_MENU, fnc = start_from_mainmenu)
	desc_pluginmenu = PluginDescriptor(name=pname, description=pdesc,  where = PluginDescriptor.WHERE_PLUGINMENU, fnc = start_from_pluginmenu)
	desc_extensionmenu = PluginDescriptor(name=pname, description=pdesc, where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = start_from_pluginmenu)
	desc_filescan = PluginDescriptor(name=pname, where = PluginDescriptor.WHERE_FILESCAN, fnc = start_from_filescan)
	list = []
	list.append(desc_pluginmenu)
####
	#buggie 
#	list.append(desc_filescan)
####
	if config.plugins.filebrowservti.add_extensionmenu_entry.value:
		list.append(desc_extensionmenu)
	if config.plugins.filebrowservti.add_mainmenu_entry.value:
		list.append(desc_mainmenu)
	return list

