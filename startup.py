import resources.lib.qfpynm as qfpynm
import xbmc, xbmcgui

state, message = qfpynm.get_nm_state()

if state != 70:
	dialog = xbmcgui.Dialog()
	dialog.ok('No Internet Connection', 'You are not connected to any WiFi Netwok.', 'Select a network to connect.')
	xbmc.executebuiltin('XBMC.RunAddon(script.wifimanager)')