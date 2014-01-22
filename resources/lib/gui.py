import sys
import xbmc
import xbmcaddon
import xbmcgui
import qfpynm
import time

# enable localization
getLS = sys.modules["__main__"].__language__
__cwd__ = sys.modules["__main__"].__cwd__


class GUI(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.msg = kwargs['msg']
        self.first = kwargs['first']
        self.doModal()

    def onInit(self):
        self.defineControls()

        self.status_label.setLabel(self.msg)

        self.showDialog()

        if self.first == True:
            nm_OK, err = self.check_nm()
            if nm_OK == True:
                devlist = qfpynm.list_wifi_devices()
                if len(devlist) > 1:
                    self.msg = getLS(30127)
                elif len(devlist) == 0:
                    self.msg = getLS(30128)
            else:
                self.msg = getLS(err)

        self.status_label.setLabel(self.msg)

        # self.disconnect_button.setEnabled(False)
        # self.delete_button.setEnabled(False)

    def check_nm(self):
        try:
            import dbus
        except:
            # dbus not available
            err = 30130
            return False, err

        try:
            bus = dbus.SystemBus()
        except:
            # could not connect to dbus
            err = 30131
            return False, err

        try:
            nm_proxy = bus.get_object(
                "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
            nm_iface = dbus.Interface(
                nm_proxy, "org.freedesktop.NetworkManager")
        except:
            # could not connect to network-manager
            err = 30132
            return False, err

        return True, ''

    def defineControls(self):
        # actions
        self.action_cancel_dialog = (9, 10)
        # control ids
        self.control_heading_label_id = 2
        self.control_list_label_id = 3
        self.control_list_id = 10
        self.control_delete_button_id = 11
        self.control_disconnect_button_id = 13
        self.control_add_connection_button_id = 14
        self.control_status_button_id = 15
        self.control_install_button_id = 18
        self.control_cancel_button_id = 19
        self.control_status_label_id = 100

        # controls
        self.heading_label = self.getControl(
            self.control_heading_label_id)
        self.list_label = self.getControl(self.control_list_label_id)
        self.list = self.getControl(self.control_list_id)
        #self.delete_button        = self.getControl(self.control_delete_button_id)
        self.control_add_connection_button = self.getControl(
            self.control_add_connection_button_id)
        #self.status_button        = self.getControl(self.control_status_button_id)
        #self.disconnect_button  = self.getControl(self.control_disconnect_button_id)
        #self.install_button     = self.getControl(self.control_install_button_id)
        #self.cancel_button      = self.getControl(self.control_cancel_button_id)
        self.status_label = self.getControl(self.control_status_label_id)

    def showDialog(self):
        self.updateList()
        state, stateTXT = qfpynm.get_nm_state()
        msg = stateTXT
        self.status_label.setLabel(msg)

    def closeDialog(self):
        self.close()

    def add_hidden(self):
        ssid = ''
        kb = xbmc.Keyboard("", getLS(30123), False)
        kb.doModal()
        if (kb.isConfirmed()):
            ssid = kb.getText()
        if ssid == '':
            self.msg = getLS(30108)
            self.status_label.setLabel(self.msg)
            return False

        encryption = ''
        kb = xbmc.Keyboard("", getLS(30124), False)
        kb.doModal()
        if (kb.isConfirmed()):
            encryption = kb.getText()
            if encryption != '':
                encryption = encryption.upper()

        if encryption == '' or not any(encryption in s for s in ['NONE', 'WEP', 'WPA']):
            self.msg = getLS(30125)
            self.status_label.setLabel(self.msg)
            return False
        return self.add_wireless(ssid, encryption)

    def add_wireless(self, ssid, encryption):
        finished = False
        connection_created = False
        con_path = ''
        asked = False
        while not finished:
            finished, connection_created, con_path = self.add_wireless_sub(
                ssid, encryption, connection_created, con_path, asked)
            asked = True
        return connection_created

    def add_wireless_sub(self, ssid, encryption, connection_created, con_path, asked=False):
        # Prompt for key
        key = ""
        if not encryption == 'NONE':
            message = 'Enter Password:'
            if asked:
                message = 'Connection Failed, please enter password again:'
            kb = xbmc.Keyboard("", message, False)

            kb.doModal()
            if (kb.isConfirmed()):
                key = kb.getText()
                errors = qfpynm.validate_wifi_input(key, encryption)

            if key == "" or errors != '':
                self.msg = getLS(30109)
                self.status_label.setLabel(self.msg)
                return True, connection_created, con_path
        if encryption == 'WEP':
            wep_alg = 'shared'
        else:
            wep_alg = ''
        if connection_created == False:
            con_path = qfpynm.add_wifi(ssid, key, encryption, wep_alg, True)
        else:
            aUUID = qfpynm.get_con_uuid_by_path(con_path)
            qfpynm.update_wifi(aUUID, key, encryption)
            qfpynm.activate_connection(aUUID)

        asked = False

        for i in range(1, 150):
            state, stateTXT = qfpynm.get_device_state(qfpynm.get_wifi_device())
            self.msg = stateTXT
            self.status_label.setLabel(self.msg)
            # Do not exit directly just to be sure.
            # If trying with a bad key when wifi is disconnected do not give state 60 but 30....
            # better never to disconnect wifi and only deactivate c
            if (i > 10 and state == 60) or (i > 10 and state == 30) or (state == 100 and i > 2):
                break
            time.sleep(1)
            self.msg = ''
            self.status_label.setLabel(self.msg)
            time.sleep(1)
        if state == 100:
            self.msg = getLS(30120)  # "Connected!"
            self.status_label.setLabel(self.msg)
            xbmc.executebuiltin('XBMC.ActivateWindow(Home)')
            self.close()
            return True, True, con_path
        if (state == 60 or state == 30) and encryption != "NONE":
            self.msg = getLS(30121)  # "Not Autorized!"
            self.status_label.setLabel(self.msg)
            return False, True, con_path

        self.msg = qfpynm.nm_state.get(state, '')  # "Connection failed"
        self.status_label.setLabel(self.msg)
        return True, True, con_path

    def make_connection(self, item, ask_password=False):

        if item.getProperty('active') == 'True':
            return True

        ssid = item.getProperty('ssid')
        uuid = item.getProperty('uuid')
        encryption = item.getProperty('encryption')

        # print uuid
        # if ask_password:
        #     key = ""
        #     kb = xbmc.Keyboard("", getLS(30104), False)
        #     kb.doModal()
        #     if (kb.isConfirmed()):
        #         key=kb.getText()
        #         errors = qfpynm.validate_wifi_input(key,encryption)

        #     if key == "" or errors != '':
        #         self.msg = getLS(30109)
        #         self.status_label.setLabel(self.msg)
        #     else:
        #         qfpynm.update_wifi(uuid, key, encryption)
        #         qfpynm.activate_connection(uuid)
        # else:
        if uuid != '':
            self.activate_connection(uuid)
        else:
            self.add_wireless(ssid, encryption)
            state, stateTXT = qfpynm.get_device_state(qfpynm.get_wifi_device())
            self.updateList()

        asked = False

        for i in range(1, 150):
            state, stateTXT = qfpynm.get_device_state(qfpynm.get_wifi_device())
            msg = stateTXT
            self.status_label.setLabel(msg)
            if (state == 100 and i > 2):
                break
            if (i > 2 and state == 60):
                if encryption not in ['WPA', 'WEP']:
                    print("Strange encryption:" + encryption)
                    break
                # Prompt for key
                key = ""

                message = 'Enter Password:'
                if asked:
                    message = 'Connection Failed, please enter password again:'

                kb = xbmc.Keyboard("", message, False)
                kb.doModal()

                if (kb.isConfirmed()):
                    key = kb.getText()
                    asked = True
                    errors = qfpynm.validate_wifi_input(key, encryption)

                if key == "" or errors != '':
                    self.msg = getLS(30109)
                    self.status_label.setLabel(self.msg)
                    break

                qfpynm.update_wifi(uuid, key, encryption)
                qfpynm.activate_connection(uuid)
                continue
            time.sleep(1)
            msg = msg
            self.status_label.setLabel(msg)

        if state == 100:
            msg = getLS(30120)  # "Connected!"

        elif state == 60:
            msg = getLS(30121)  # "Not Autorized!"
        else:
            msg = qfpynm.nm_state.get(state, '')  # "Connection failed"

        self.updateList()
        self.status_label.setLabel(msg)

        if state == 100:
            xbmc.executebuiltin('XBMC.ActivateWindow(Home)')
            self.close()
            return True
        return False

    def onClick(self, controlId):
        self.msg = ""
        self.status_label.setLabel(self.msg)

        # Activate connection from list
        if controlId == self.control_list_id:
            item = self.list.getSelectedItem()
            self.make_connection(item)

            state, stateTXT = qfpynm.get_device_state(qfpynm.get_wifi_device())
            print 'After effect', state
            if state != 100:
                self.make_connection(item, ask_password=True)

        # Add connection button
        elif controlId == self.control_add_connection_button_id:
            self.add_hidden()
            state, stateTXT = qfpynm.get_device_state(qfpynm.get_wifi_device())
            if state == 120:
                self.add_hidden()

            self.updateList()

        elif controlId == self.control_cancel_button_id:
            self.closeDialog()

    def onAction(self, action):
        if action in self.action_cancel_dialog:
            self.closeDialog()

    def onFocus(self, controlId):
        msg = ""
        if hasattr(self, 'status_label'):
            self.status_label.setLabel(msg)

    def disconnect(self):
        qfpynm.deactive_wifi()

    def activate_connection(self, uuid):
        qfpynm.activate_connection(uuid)

    def delete_connection(self, uuid):
        qfpynm.delete_connection(uuid)

    def updateList(self):
        saved_wifi = []
        uuid_map = {}
        active = qfpynm.get_wireless_networks()
        wifi_connections = qfpynm.get_connections()
        self.list.reset()

        for connection in wifi_connections:
            saved_wifi.append(connection.get('ssid'))
            uuid_map[connection.get('ssid')] = connection.get('uuid')

        print "Active List: ", active

        print "Active: ", saved_wifi

        print "Wifi: ", wifi_connections

        for connection_dict in active:

            status = ''

            state, stateTXT = qfpynm.get_device_state(qfpynm.get_wifi_device())

            if connection_dict['connected'] == True:
                color = 'red'
                if state == 100:
                    color = 'green'
                elif state == 50:
                    color = 'yellow'

                status = "[B][COLOR %s]*[/COLOR][/B]" % (color,)
            else:
                status = ""

            uuid = uuid_map.get(connection_dict['essid'], '')

            item = xbmcgui.ListItem(
                label=status, label2=connection_dict['essid'])
            item.setProperty('ssid', connection_dict['essid'])
            item.setProperty('uuid', uuid)
            item.setProperty('encryption', connection_dict['encrypt'])
            item.setProperty('active', str(connection_dict['connected']))

            self.list.addItem(item)
