from Tools.Profile import profile
from Tools.BoundFunction import boundFunction

# workaround for required config entry dependencies.
import Screens.MovieSelection

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Pixmap import MultiPixmap

profile("LOAD:enigma")
import enigma
from boxbranding import getBrandOEM

profile("LOAD:InfoBarGenerics")
from Screens.InfoBarGenerics import InfoBarShowHide, \
	InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarRdsDecoder, \
	InfoBarEPG, InfoBarSeek, InfoBarInstantRecord, InfoBarRedButton, InfoBarTimerButton, InfoBarVmodeButton, \
	InfoBarAudioSelection, InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarUnhandledKey, InfoBarLongKeyDetection, \
	InfoBarSubserviceSelection, InfoBarShowMovies,  \
	InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarBuffer, \
	InfoBarSummarySupport, InfoBarMoviePlayerSummarySupport, InfoBarTimeshiftState, InfoBarTeletextPlugin, InfoBarExtensions, \
	InfoBarSubtitleSupport, InfoBarPiP, InfoBarPlugins, InfoBarServiceErrorPopupSupport, InfoBarJobman, InfoBarZoom, InfoBarHdmi, \
	setResumePoint, delResumePoint
from Screens.ButtonSetup import InfoBarButtonSetup

profile("LOAD:InitBar_Components")
from Components.ActionMap import HelpableActionMap
from Components.Timeshift import InfoBarTimeshift
from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase

profile("LOAD:HelpableScreen")
from Screens.HelpMenu import HelpableScreen

class InfoBar(
	InfoBarBase, InfoBarShowHide,
	InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarEPG, InfoBarRdsDecoder,
	InfoBarInstantRecord, InfoBarAudioSelection, InfoBarRedButton, InfoBarTimerButton, InfoBarVmodeButton,
	HelpableScreen, InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarUnhandledKey, InfoBarLongKeyDetection,
	InfoBarSubserviceSelection, InfoBarTimeshift, InfoBarSeek, InfoBarCueSheetSupport, InfoBarBuffer,
	InfoBarSummarySupport, InfoBarTimeshiftState, InfoBarTeletextPlugin, InfoBarExtensions,
	InfoBarPiP, InfoBarPlugins, InfoBarSubtitleSupport, InfoBarServiceErrorPopupSupport, InfoBarJobman, InfoBarZoom, InfoBarHdmi,
	InfoBarButtonSetup, Screen,
):

	ALLOW_SUSPEND = True
	instance = None

	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = HelpableActionMap(self, "InfobarActions", {
			"showMovies": (self.showMovies, _("Watch recordings and media...")),
			"showRadio": (self.showRadio, _("Listen to the radio...")),
			"showTv": (self.TvRadioToggle, self._helpTvRadioToggle()),
			"openTimerList": (self.openTimerList, _("Open timer list...")),
			"openSleepTimer": (self.openSleepTimer, _("Show/add sleep timers...")),
			"showMediaPlayer": (self.showMediaPlayer, _("Open the media player...")),
			"showPluginBrowser": (self.showPluginBrowser, _("Open the plugins screen...")),
			"showSetup": (self.showSetup, _("Open the settings screen...")),
			"showWWW": (self.showWWW, _("Open Web browser...")),
			"showLanSetup": (self.showLanSetup, _("Show LAN Setup...")),
			"showFormat": (self.showFormat, _("Display the screen format...")),

		}, prio=2, description=_("Basic functions"))

		self.radioTV = 0
		self.allowPiP = True

		for x in (
			HelpableScreen,
			InfoBarBase, InfoBarShowHide,
			InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarEPG, InfoBarRdsDecoder,
			InfoBarInstantRecord, InfoBarAudioSelection, InfoBarRedButton, InfoBarTimerButton, InfoBarUnhandledKey, InfoBarLongKeyDetection, InfoBarVmodeButton,
			InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarSubserviceSelection, InfoBarBuffer,
			InfoBarTimeshift, InfoBarSeek, InfoBarCueSheetSupport, InfoBarSummarySupport, InfoBarTimeshiftState,
			InfoBarTeletextPlugin, InfoBarExtensions, InfoBarPiP, InfoBarSubtitleSupport, InfoBarJobman, InfoBarZoom, InfoBarHdmi,
			InfoBarPlugins, InfoBarServiceErrorPopupSupport, InfoBarButtonSetup
		):
			x.__init__(self)

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
			enigma.iPlayableService.evUpdatedEventInfo: self.__eventInfoChanged,
			enigma.iPlayableService.evStart: self.__eventServiceStart
		})

		self["serviceNumber"] = Label()
		self["serviceName"] = Label()
		self["serviceName1"] = Label()

		self.current_begin_time = 0
		assert InfoBar.instance is None, "class InfoBar is a singleton class and just one instance of this class is allowed!"
		InfoBar.instance = self

		if config.misc.initialchannelselection.value:
			self.onShown.append(self.showMenu)

		self.onShown.append(self._onShown)

	def _onShown(self):
		vis = config.usage.show_channel_numbers_in_servicelist.value
		for widget in "serviceNumber", "serviceName":
			if self[widget].visible != vis:
				self[widget].visible = vis
		if self["serviceName1"].visible == vis:
			self["serviceName1"].visible = not vis

	def __eventServiceStart(self):
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		name = info and info.getName()
		name = name or ""
		name = name.replace('\xc2\x86', '').replace('\xc2\x87', '')
		for widget in "serviceName", "serviceName1":
			self[widget].setText(name)

		serviceref = self.session.nav.getCurrentlyPlayingServiceReference()
		channelNum = serviceref and serviceref.getChannelNum()
		self["serviceNumber"].setText(str(channelNum) if channelNum is not None else "")

	def openChannelSelection(self):
		if InfoBar.instance.servicelist is None:
			InfoBar.instance.servicelist = InfoBar.instance.session.instantiateDialog(ChannelSelection)
		InfoBar.instance.showTv()

	def showMenu(self):
		self.onShown.remove(self.showMenu)
		config.misc.initialchannelselection.value = False
		config.misc.initialchannelselection.save()
		self.openChannelSelection()

	def doButtonsCheck(self):
		if config.vixsettings.ColouredButtons.value:
			self["key_yellow"].setText(_("Search"))

			configINFOEpgType = config.usage.defaultEPGType
			if configINFOEpgType.value == "Graphical EPG..." or configINFOEpgType.value == "None":
				self["key_red"].setText(_("Single EPG"))
			else:
				self["key_red"].setText(_("ViX EPG"))

			if not config.vixsettings.Subservice.value:
				self["key_green"].setText(_("Timers"))
			else:
				self["key_green"].setText(_("Subservices"))
		self["key_blue"].setText(_("Extensions"))

	def __onClose(self):
		InfoBar.instance = None

	def __eventInfoChanged(self):
		if self.execing:
			service = self.session.nav.getCurrentService()
			old_begin_time = self.current_begin_time
			info = service and service.info()
			ptr = info and info.getEvent(0)
			self.current_begin_time = ptr and ptr.getBeginTime() or 0
			if config.usage.show_infobar_on_event_change.value:
				if old_begin_time and old_begin_time != self.current_begin_time:
					self.doShow()

	def __checkServiceStarted(self):
		self.__serviceStarted(True)
		self.onExecBegin.remove(self.__checkServiceStarted)

	def serviceStarted(self):  # override from InfoBarShowHide
		new = self.servicelist.newServicePlayed()
		if self.execing:
			InfoBarShowHide.serviceStarted(self)
			self.current_begin_time = 0
		elif self.__checkServiceStarted not in self.onShown and new:
			self.onShown.append(self.__checkServiceStarted)

	def __checkServiceStarted(self):
		self.serviceStarted()
		self.onShown.remove(self.__checkServiceStarted)

	def openChannelList(self):
		self.showTvChannelList(True)

	def openBouquetList(self):
		showTv(self)

	def _helpTvRadioToggle(self):
		if getBrandOEM() == 'gigablue':
			return _("Switch between TV and radio...")
		else:
			return _("Watch TV...")

	def TvRadioToggle(self):
		if getBrandOEM() == 'gigablue':
			self.toogleTvRadio()
		else:
			self.showTv()

	def toogleTvRadio(self):
		if self.radioTV == 1:
			self.radioTV = 0
			self.showTv()
		else:
			self.radioTV = 1
			self.showRadio()

	def showTv(self):
		self.showTvChannelList(True)
		if config.usage.show_servicelist.value:
			self.servicelist.showFavourites()

	def showRadio(self):
		if config.usage.e1like_radio_mode.value:
			self.showRadioChannelList(True)
			if config.usage.show_servicelist.value:
				self.servicelist.showFavourites()
		else:
			self.rds_display.hide()  # in InfoBarRdsDecoder
			from Screens.ChannelSelection import ChannelSelectionRadio
			self.session.openWithCallback(self.ChannelSelectionRadioClosed, ChannelSelectionRadio, self)

	def ChannelSelectionRadioClosed(self, *arg):
		self.rds_display.show()  # in InfoBarRdsDecoder
		self.servicelist.correctChannelNumber()

	def showMovies(self, defaultRef=None):
		self.lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		if self.lastservice and ':0:/' in self.lastservice.toString():
			self.lastservice = enigma.eServiceReference(config.movielist.curentlyplayingservice.value)
		self.session.openWithCallback(self.movieSelected, Screens.MovieSelection.MovieSelection, defaultRef, timeshiftEnabled=self.timeshiftEnabled())

	def movieSelected(self, service):
		ref = self.lastservice
		del self.lastservice
		if service is None:
			if ref and not self.session.nav.getCurrentlyPlayingServiceOrGroup():
				self.session.nav.playService(ref)
		else:
			self.session.open(MoviePlayer, service, slist=self.servicelist, lastservice=ref)

	def openTimerList(self):
		from Screens.TimerEdit import TimerEditList
		self.session.open(TimerEditList)

	def openSleepTimer(self):
		from Screens.PowerTimerEdit import PowerTimerEditList
		self.session.open(PowerTimerEditList)

	def showMediaPlayer(self):
		try:
			from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer
			self.session.open(MediaPlayer)
			no_plugin = False
		except Exception, e:
			self.session.open(MessageBox, _("The MediaPlayer plugin is not installed!\nPlease install it."), type=MessageBox.TYPE_INFO, timeout=10)

	def showPluginBrowser(self):
		from Screens.PluginBrowser import PluginBrowser
		self.session.open(PluginBrowser)

	def showSetup(self):
		from Screens.GeneralSetup import GeneralSetup
		self.session.open(GeneralSetup)

	def showLanSetup(self):
		from Screens.NetworkSetup import NetworkAdapterSelection
		self.session.open(NetworkAdapterSelection)

	def showWWW(self):
		try:
			try:
				from Plugins.Extensions.HbbTV.plugin import OperaBrowser
			except:
				from Plugins.Extensions.IniHbbTV.plugin import OperaBrowser

			self.session.open(OperaBrowser)
			no_plugin = False
		except Exception, e:
			self.session.open(MessageBox, _("The WebBrowser plugin is not installed!\nPlease install it."), type=MessageBox.TYPE_INFO, timeout=10)

	def showFormat(self):
		try:
			from Plugins.SystemPlugins.Videomode.plugin import videoSetupMain
			self.session.instantiateDialog(videoSetupMain)
			no_plugin = False
		except Exception, e:
			self.session.open(MessageBox, _("The VideoMode plugin is not installed!\nPlease install it."), type=MessageBox.TYPE_INFO, timeout=10)


class MoviePlayer(
	InfoBarBase, InfoBarShowHide, InfoBarLongKeyDetection, InfoBarMenu, InfoBarEPG,
	InfoBarSeek, InfoBarShowMovies, InfoBarInstantRecord, InfoBarAudioSelection, HelpableScreen, InfoBarNotifications,
	InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport,
	InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, Screen, InfoBarTeletextPlugin,
	InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarPlugins, InfoBarPiP, InfoBarZoom, InfoBarButtonSetup
):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	instance = None

	def __init__(self, session, service, slist=None, lastservice=None):
		Screen.__init__(self, session)

		self["key_yellow"] = Label()
		self["key_blue"] = Label()
		self["key_green"] = Label()

		self["eventname"] = Label()
		self["state"] = Label()
		self["speed"] = Label()
		self["statusicon"] = MultiPixmap()

		self["actions"] = HelpableActionMap(self, "MoviePlayerActions", {
			"leavePlayer": (self.leavePlayer, self._helpLeavePlayer),
			"leavePlayerOnExit": (self.leavePlayerOnExit, self._helpLeavePlayerOnExit)
		}, description=_("Movie player"))

		self.allowPiP = True

		for x in (
			HelpableScreen, InfoBarShowHide, InfoBarLongKeyDetection, InfoBarMenu, InfoBarEPG,
			InfoBarBase, InfoBarSeek, InfoBarShowMovies, InfoBarInstantRecord,
			InfoBarAudioSelection, InfoBarNotifications,
			InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport,
			InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport,
			InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport, InfoBarExtensions,
			InfoBarPlugins, InfoBarPiP, InfoBarZoom, InfoBarButtonSetup
		):
			x.__init__(self)

		self.onChangedEntry = []
		self.servicelist = slist
		self.lastservice = lastservice or session.nav.getCurrentlyPlayingServiceOrGroup()
		session.nav.playService(service)
		self.cur_service = service
		self.returning = False
		self.onClose.append(self.__onClose)
		self.onShow.append(self.doButtonsCheck)

		assert MoviePlayer.instance is None, "class InfoBar is a singleton class and just one instance of this class is allowed!"
		MoviePlayer.instance = self

	def doButtonsCheck(self):
		if config.vixsettings.ColouredButtons.value:
			self["key_yellow"].setText(_("Search"))
			self["key_green"].setText(_("Timers"))
		self["key_blue"].setText(_("Extensions"))

	def __onClose(self):
		MoviePlayer.instance = None
		from Screens.MovieSelection import playlist
		del playlist[:]
		if not config.movielist.stop_service.value:
			Screens.InfoBar.InfoBar.instance.callServiceStarted()
		self.session.nav.playService(self.lastservice)
		config.usage.last_movie_played.value = self.cur_service.toString()
		config.usage.last_movie_played.save()

	def handleLeave(self, how):
		self.is_closing = True
		if how == "ask":
			if config.usage.setup_level.index < 2:  # -expert
				list = (
					(_("Yes"), "quit"),
					(_("No"), "continue")
				)
			else:
				list = (
					(_("Yes"), "quit"),
					(_("Yes, returning to movie list"), "movielist"),
					(_("Yes, and delete this movie"), "quitanddelete"),
					(_("Yes, delete this movie and return to movie list"), "deleteandmovielist"),
					(_("No"), "continue"),
					(_("No, but restart from begin"), "restart")
				)

			from Screens.ChoiceBox import ChoiceBox
			self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list=list)
		else:
			self.leavePlayerConfirmed([True, how])

	def _helpLeavePlayer(self):
		return {
			"ask": _("Stop movie and ask user next action"),
			"movielist": _("Stop movie and return to movie list"),
			"quit": _("Stop movie and return to previous service")
		}.get(config.usage.on_movie_stop.value, _("No current function"))

	def leavePlayer(self):
		setResumePoint(self.session)
		self.handleLeave(config.usage.on_movie_stop.value)

	def _helpLeavePlayerOnExit(self):
		return {
			"no": _("Close PiP") if self.session.pipshown else _("Stop movie on EXIT disabled"),
			"popup": _("Ask whether to close PiP") if self.session.pipshown else _("Ask whether to stop movie"),
			"without popup": _("Close PiP") if self.session.pipshown else _("Stop movie")
		}.get(config.usage.on_movie_exit.value, _("No current function"))

	def leavePlayerOnExit(self):
		if self.shown:
			self.hide()
		elif self.session.pipshown and "popup" in config.usage.pip_hideOnExit.value:
			if config.usage.pip_hideOnExit.value == "popup":
				self.session.openWithCallback(self.hidePipOnExitCallback, MessageBox, _("Disable Picture in Picture"), simple=True)
			else:
				self.hidePipOnExitCallback(True)
		elif config.usage.leave_movieplayer_onExit.value == "popup":
			self.session.openWithCallback(self.leavePlayerOnExitCallback, MessageBox, _("Exit movie player?"), simple=True)
		elif config.usage.leave_movieplayer_onExit.value == "without popup":
			self.leavePlayerOnExitCallback(True)

	def leavePlayerOnExitCallback(self, answer):
		if answer:
			setResumePoint(self.session)
			self.handleLeave("quit")

	def hidePipOnExitCallback(self, answer):
		if answer:
			self.showPiP()

	def deleteConfirmed(self, answer):
		if answer:
			self.leavePlayerConfirmed((True, "quitanddeleteconfirmed"))

	def deleteAndMovielistConfirmed(self, answer):
		if answer:
			self.leavePlayerConfirmed((True, "deleteandmovielistconfirmed"))

	def movielistAgain(self):
		from Screens.MovieSelection import playlist
		del playlist[:]
		self.session.nav.playService(self.lastservice)
		self.leavePlayerConfirmed((True, "movielist"))

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer is None:
			return
		if answer in ("quitanddelete", "quitanddeleteconfirmed", "deleteandmovielist", "deleteandmovielistconfirmed"):
			ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			serviceHandler = enigma.eServiceCenter.getInstance()
			if answer in ("quitanddelete", "deleteandmovielist"):
				msg = ''
				if config.usage.movielist_trashcan.value:
					import Tools.Trashcan
					try:
						trash = Tools.Trashcan.createTrashFolder(ref.getPath())
						Screens.MovieSelection.moveServiceFiles(ref, trash)
						# Moved to trash, okay
						if answer == "quitanddelete":
							self.close()
						else:
							self.movielistAgain()
						return
					except Exception, e:
						print "[InfoBar] Failed to move to .Trash folder:", e
						msg = _("Cannot move to trash can") + "\n" + str(e) + "\n"
				info = serviceHandler.info(ref)
				name = info and info.getName(ref) or _("this recording")
				msg += _("Do you really want to delete %s?") % name
				if answer == "quitanddelete":
					self.session.openWithCallback(self.deleteConfirmed, MessageBox, msg)
				elif answer == "deleteandmovielist":
					self.session.openWithCallback(self.deleteAndMovielistConfirmed, MessageBox, msg)
				return

			elif answer in ("quitanddeleteconfirmed", "deleteandmovielistconfirmed"):
				offline = serviceHandler.offlineOperations(ref)
				if offline.deleteFromDisk(0):
					self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)
					if answer == "deleteandmovielistconfirmed":
						self.movielistAgain()
					return

		if answer in ("quit", "quitanddeleteconfirmed"):
			self.close()
		elif answer in ("movielist", "deleteandmovielistconfirmed"):
			if config.movielist.stop_service.value:
				ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			else:
				ref = self.lastservice
			self.returning = True
			self.session.openWithCallback(self.movieSelected, Screens.MovieSelection.MovieSelection, ref)
			self.session.nav.stopService()
			if not config.movielist.stop_service.value:
				self.session.nav.playService(self.lastservice)
		elif answer == "restart":
			self.doSeek(0)
			self.setSeekState(self.SEEK_STATE_PLAY)
		elif answer in ("playlist", "playlistquit", "loop"):
			(next_service, item, length) = self.getPlaylistServiceInfo(self.cur_service)
			if next_service is not None:
				if config.usage.next_movie_msg.value:
					self.displayPlayedName(next_service, item, length)
				self.session.nav.playService(next_service)
				self.cur_service = next_service
			else:
				if answer == "playlist":
					self.leavePlayerConfirmed([True, "movielist"])
				elif answer == "loop" and length > 0:
					self.leavePlayerConfirmed([True, "loop"])
				else:
					self.leavePlayerConfirmed([True, "quit"])
		elif answer in "repeatcurrent":
			if config.usage.next_movie_msg.value:
				(item, length) = self.getPlaylistServiceInfo(self.cur_service)
				self.displayPlayedName(self.cur_service, item, length)
			self.session.nav.stopService()
			self.session.nav.playService(self.cur_service)

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing:
			return
		ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		if ref:
			delResumePoint(ref)
		self.handleLeave(config.usage.on_movie_eof.value)

	def up(self):
		slist = self.servicelist
		if slist and slist.dopipzap:
			if "keep" not in config.usage.servicelist_cursor_behavior.value:
				slist.moveUp()
			self.session.execDialog(slist)
		else:
			self.showMovies()

	def down(self):
		slist = self.servicelist
		if slist and slist.dopipzap:
			if "keep" not in config.usage.servicelist_cursor_behavior.value:
				slist.moveDown()
			self.session.execDialog(slist)
		else:
			self.showMovies()

	def right(self):
		# XXX: gross hack, we do not really seek if changing channel in pip :-)
		slist = self.servicelist
		if slist and slist.dopipzap:
			# XXX: We replicate InfoBarChannelSelection.zapDown here - we shouldn't do that
			if slist.inBouquet():
				prev = slist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value and slist.atEnd():
							slist.nextBouquet()
						else:
							slist.moveDown()
						cur = slist.getCurrentSelection()
						if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
							break
			else:
				slist.moveDown()
			slist.zap(enable_pipzap=True)
		else:
			InfoBarSeek.seekFwd(self)

	def left(self):
		slist = self.servicelist
		if slist and slist.dopipzap:
			# XXX: We replicate InfoBarChannelSelection.zapUp here - we shouldn't do that
			if slist.inBouquet():
				prev = slist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value:
							if slist.atBegin():
								slist.prevBouquet()
						slist.moveUp()
						cur = slist.getCurrentSelection()
						if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
							break
			else:
				slist.moveUp()
			slist.zap(enable_pipzap=True)
		else:
			InfoBarSeek.seekBack(self)

	def showPiP(self):
		try:
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			xres = str(info.getInfo(enigma.iServiceInformation.sVideoWidth))
			slist = self.servicelist
			if self.session.pipshown:
				if slist and slist.dopipzap:
					slist.togglePipzap()
				if self.session.pipshown:
					del self.session.pip
					self.session.pipshown = False
			else:
				if int(xres) <= 720 or about.getCPUString() == 'BCM7346B2' or about.getCPUString() == 'BCM7425B2':
					from Screens.PictureInPicture import PictureInPicture
					self.session.pip = self.session.instantiateDialog(PictureInPicture)
					self.session.pip.show()
					if self.session.pip.playService(slist.getCurrentSelection()):
						self.session.pipshown = True
						self.session.pip.servicePath = slist.getCurrentServicePath()
					else:
						self.session.pipshown = False
						del self.session.pip
				else:
					self.session.open(MessageBox, _("Your %s %s does not support PiP HD") % (enigma.getMachineBrand(), enigma.getMachineName()), type=MessageBox.TYPE_INFO, timeout=5)
		except:
			pass

	def movePiP(self):
		if self.session.pipshown:
			InfoBarPiP.movePiP(self)

	def swapPiP(self):
		pass

	def showMovies(self):
		ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		if ref and ':0:/' not in ref.toString():
			self.playingservice = ref  # movie list may change the currently playing
		else:
			self.playingservice = enigma.eServiceReference(config.movielist.curentlyplayingservice.value)
		self.session.openWithCallback(self.movieSelected, Screens.MovieSelection.MovieSelection, ref)

	def movieSelected(self, service):
		if service is not None:
			self.cur_service = service
			self.is_closing = False
			self.session.nav.playService(service)
			self.returning = False
		elif self.returning:
			self.close()
		else:
			self.is_closing = False
			ref = self.playingservice
			del self.playingservice
			# no selection? Continue where we left off
			if ref and not self.session.nav.getCurrentlyPlayingServiceOrGroup():
				self.session.nav.playService(ref)

	def getPlaylistServiceInfo(self, service):
		from MovieSelection import playlist
		for i, item in enumerate(playlist):
			if item == service:
				if config.usage.on_movie_eof.value == "repeatcurrent":
					return i + 1, len(playlist)
				i += 1
				if i < len(playlist):
					return playlist[i], i + 1, len(playlist)
				elif config.usage.on_movie_eof.value == "loop":
					return playlist[0], 1, len(playlist)
		return None, 0, 0

	def displayPlayedName(self, ref, index, n):
		from Tools import Notifications
		Notifications.AddPopup(text=_("%s/%s: %s") % (index, n, self.ref2HumanName(ref)), type=MessageBox.TYPE_INFO, timeout=5)

	def ref2HumanName(self, ref):
		return enigma.eServiceCenter.getInstance().info(ref).getName(ref)
