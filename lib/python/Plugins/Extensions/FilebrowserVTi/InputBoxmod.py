#######################################################################
#
# InputBoxmod for VU+ by markusw and schomi (c) 2013
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
# InputBoxmod 20140512 v1.2-r1
####################################################################### 

from enigma import eRCInput, getPrevAsciiCode
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import NumberActionMap, HelpableActionMap
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.HelpMenu import HelpableScreen
from Components.Label import Label
from Inputmod import Input
from Tools.BoundFunction import boundFunction
from Components.Pixmap import Pixmap
from time import time
import os
from __init__ import _

class InputBox(Screen, HelpableScreen):
	def __init__(self, session, title = "", windowTitle = _("Input"), useableChars = None, **kwargs):
		Screen.__init__(self, session)

		self["text"] = Label(title)
		self["input"] = Input(**kwargs)
		self["VKeyIcon"] = Pixmap()
		self["help_text"] = Label(_("use virtual keyboard for text input"))
		self.onShown.append(boundFunction(self.setTitle, windowTitle))
		if useableChars is not None:
			self["input"].setUseableChars(useableChars)

		HelpableScreen.__init__(self)
		self["actions"] = NumberActionMap(["InputBoxActions", "InputAsciiActions", "KeyboardInputActions"], 
		{
			"gotAsciiCode": self.gotAsciiCode,
			"home": self.keyHome,
			"end": self.keyEnd,
			"deleteForward": self.keyDelete,
			"deleteBackward": self.keyBackspace,
			"tab": self.keyTab,
			"toggleOverwrite": self.keyInsert,
			"showVirtualKeyboard": self.virtualKeyBoard,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"0": self.keyNumberGlobal
		}, -1)
		self["WizardActions"] = HelpableActionMap(self, "WizardActions", 
			{
				"ok": (self.go, _("Save")),
				"back": (self.cancel,_("Cancel")),
				"down": (self.keyTab, _("Tab")),
				"left": (self.keyLeft, _("Left")),
				"right": (self.keyRight, _("Right")),
			}, -1)
		self["InfobarSeekActions"] = HelpableActionMap(self, "InfobarSeekActions", 
			{
			"seekBack": (self.keyHome,_("Home")),
			"seekFwd": (self.keyEnd,_("End")),
			"playpauseService": (self.keyInsert, _("Toggle Insert / Overwrite")),
			}, -1)
		self["InputBoxActions"] = HelpableActionMap(self, "InputBoxActions", 
			{
			"deleteForward": (self.keyDelete, _("Delete")),
			"deleteBackward": (self.keyBackspace, _("Backspace")),
			}, -1)

		if self["input"].type == Input.TEXT:
			self.onExecBegin.append(self.setKeyboardModeAscii)
		else:
			self.onExecBegin.append(self.setKeyboardModeNone)

	def virtualKeyBoard(self):
		self.input_text = self["input"].getText()
		input_title = self["text"].getText()
		self.session.openWithCallback(self.virtualKeyBoardCB, VirtualKeyBoard, title = input_title, text = self.input_text)

	def virtualKeyBoardCB(self, res):
		if res:
			self.input_text = res
		self["input"].setText(self.input_text)
		self["input"].end()

	def gotAsciiCode(self):
		self["input"].handleAscii(getPrevAsciiCode())

	def keyLeft(self):
		self["input"].left()

	def keyRight(self):
		self["input"].right()

	def keyNumberGlobal(self, number):
		self["input"].number(number)

	def keyDelete(self):
		self["input"].delete()

	def go(self):
		self.close(self["input"].getText())

	def cancel(self):
		self.close(None)

	def keyHome(self):
		self["input"].home()

	def keyEnd(self):
		self["input"].end()

	def keyBackspace(self):
		self["input"].deleteBackward()

	def keyTab(self):
		self["input"].tab()

	def keyInsert(self):
		self["input"].toggleOverwrite()

class InputBoxmod(Screen, HelpableScreen):
	skin = """
		<screen position="center,center" size=" 1100, 95" title="Input">
			<widget name="text" position="10,10" size="1080,22" font="Regular;18" />
			<widget name="input" position="10,50" size="1080,24" font="Regular;22" />
		</screen>"""

	def __init__(self, session, title = "", windowTitle = _("Input"), useableChars = None, **kwargs):
		Screen.__init__(self, session)

		self["text"] = Label(title)
		self["input"] = Input(**kwargs)
		self.onShown.append(boundFunction(self.setTitle, windowTitle))
		HelpableScreen.__init__(self)
		if useableChars is not None:
			self["input"].setUseableChars(useableChars)

		self["actions"] = NumberActionMap(["InputBoxActions", "InputAsciiActions", "KeyboardInputActions"], 
		{
			"gotAsciiCode": self.gotAsciiCode,
			"home": self.keyHome,
			"end": self.keyEnd,
			"deleteForward": self.keyDelete,
			"deleteBackward": self.keyBackspace,
			"tab": self.keyTab,
			"toggleOverwrite": self.keyInsert,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"0": self.keyNumberGlobal
		}, -1)
		self["WizardActions"] = HelpableActionMap(self, "WizardActions", 
			{
				"ok": (self.go, _("Save")),
				"back": (self.cancel,_("Cancel")),
				"down": (self.keyTab, _("Tab")),
				"left": (self.keyLeft, _("Left")),
				"right": (self.keyRight, _("Right")),
			}, -1)
		self["InfobarSeekActions"] = HelpableActionMap(self, "InfobarSeekActions", 
			{
			"seekBack": (self.keyHome,_("Home")),
			"seekFwd": (self.keyEnd,_("End")),
			"playpauseService": (self.keyInsert, _("Toggle Insert / Overwrite")),
			}, -1)
		self["InputBoxActions"] = HelpableActionMap(self, "InputBoxActions", 
			{
			"deleteForward": (self.keyDelete, _("Delete")),
			"deleteBackward": (self.keyBackspace, _("Backspace")),
			}, -1)
		if self["input"].type == Input.TEXT:
			self.onExecBegin.append(self.setKeyboardModeAscii)
		else:
			self.onExecBegin.append(self.setKeyboardModeNone)

	def gotAsciiCode(self):
		self["input"].handleAscii(getPrevAsciiCode())

	def keyLeft(self):
		self["input"].left()

	def keyRight(self):
		self["input"].right()

	def keyNumberGlobal(self, number):
		self["input"].number(number)

	def keyDelete(self):
		self["input"].delete()

	def go(self):
		self.close(self["input"].getText())

	def cancel(self):
		self.close(None)

	def keyHome(self):
		self["input"].home()

	def keyEnd(self):
		self["input"].end()

	def keyBackspace(self):
		self["input"].deleteBackward()

	def keyTab(self):
		self["input"].tab()

	def keyInsert(self):
		self["input"].toggleOverwrite()

class PinInput(InputBox):
	def __init__(self, session, service = "", triesEntry = None, pinList = [], *args, **kwargs):
		InputBox.__init__(self, session = session, text="    ", maxSize=True, type=Input.PIN, *args, **kwargs)
		
		self.waitTime = 15
		
		self.triesEntry = triesEntry
		
		self.pinList = pinList
		self["service"] = Label(service)
		
		if self.getTries() == 0:
			if (self.triesEntry.time.value + (self.waitTime * 60)) > time():
				remaining = (self.triesEntry.time.value + (self.waitTime * 60)) - time()
				remainingMinutes = int(remaining / 60)
				remainingSeconds = int(remaining % 60)
				self.onFirstExecBegin.append(boundFunction(self.session.openWithCallback, self.closePinCancel, MessageBox, _("You have to wait %s!") % (str(remainingMinutes) + " " + _("minutes") + ", " + str(remainingSeconds) + " " + _("seconds")), MessageBox.TYPE_ERROR))
			else:
				self.setTries(3)

		self["tries"] = Label("")
		self.onShown.append(self.showTries)

	def gotAsciiCode(self):
		if self["input"].currPos == len(self["input"]) - 1:
			InputBox.gotAsciiCode(self)
			self.go()
		else:
			InputBox.gotAsciiCode(self)

	def keyNumberGlobal(self, number):
		if self["input"].currPos == len(self["input"]) - 1:
			InputBox.keyNumberGlobal(self, number)
			self.go()
		else:
			InputBox.keyNumberGlobal(self, number)
		
	def checkPin(self, pin):
		if pin is not None and pin.find(" ") == -1 and int(pin) in self.pinList:
			return True
		return False
		
	def go(self):
		self.triesEntry.time.value = int(time())
		self.triesEntry.time.save()
		if self.checkPin(self["input"].getText()):
			self.setTries(3)
			self.closePinCorrect()
		else:
			self.keyHome()
			self.decTries()
			if self.getTries() == 0:
				self.closePinWrong()
			else:
				pass
	
	def closePinWrong(self, *args):
		print "args:", args
		self.close(False)
		
	def closePinCorrect(self, *args):
		self.close(True)
		
	def closePinCancel(self, *args):
		self.close(None)
			
	def cancel(self):
		self.closePinCancel()
		
	def getTries(self):
		return self.triesEntry.tries.value

	def decTries(self):
		self.setTries(self.triesEntry.tries.value - 1)
		self.showTries()
		
	def setTries(self, tries):
		self.triesEntry.tries.value = tries
		self.triesEntry.tries.save()
				
	def showTries(self):
		self["tries"].setText(_("Tries left:") + " " + str(self.getTries()))
