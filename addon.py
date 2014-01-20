from xbmcswift2 import Plugin
from xbmcswift2 import xbmc, xbmcgui
from resources.lib import qfpynm
import time

plugin = Plugin()


@plugin.route('/')
def index():
    plugin.log.debug('Connections: ' + str(qfpynm.get_connections()))
    wifi_connections = qfpynm.get_wireless_networks()
    items = []
    for connection in wifi_connections:
        plugin.log.debug(connection)
        connection_ssid = connection.get('essid', '')
        connection_encryption = connection.get('encrypt', '')
        status = ''
        if connection['connected'] == True:
            status = '[C]'
        elif connection['automatic'] == True:
            status = '[A]'

        item = {
            'label': "%s %s" % (status, connection['essid']),
            'path': plugin.url_for('password_prompt', ssid=connection_ssid, encryption=connection_encryption),
            'is_playable': False
        }
        items.append(item)
    return items


@plugin.route('/password_prompt/<ssid>/<encryption>')
def password_prompt(ssid, encryption):
    password, errors = ('', '')

    plugin.log.debug("SSID: %s, Encryption %s" % (str(ssid), str(encryption)))
    result = add_wireless(ssid, encryption)
    message = 'Connected'

    if result == 'FAILED':
        message = 'Connection failed!'
    elif result == 'ALREADY_CONNECTED':
        message = 'Already Connected'

    dialog = xbmcgui.Dialog()
    dialog.ok(ssid, message)


def add_wireless(ssid, encryption):
    connected_to_ssid = False
    connection_list = qfpynm.get_connections()
    plugin.log.debug("Connections: %s" % str(qfpynm.nm_settings_iface.ListConnections()))
    
    for connection in connection_list:
        if connection.get('ssid') == ssid and connection.get('active') == True:
            connected_to_ssid = True

    if connected_to_ssid:
        return 'ALREADY_CONNECTED'

    finished = False
    connection_created = False
    con_path = ''
    while not finished:
        finished, connection_created, con_path = add_wireless_sub(
            ssid, encryption, connection_created, con_path)
    
    if connection_created == False:
        return 'FAILED'
    
    return 'CONNECTED'


def add_wireless_sub(ssid, encryption, connection_created, con_path):
    # Prompt for key
    was_connected = False
    connection_list = qfpynm.get_connections()
    for connection in connection_list:
        if connection.get('ssid') == ssid:
            con_path = connection.get('path')
            was_connected = True
    
    key = ""
    if not was_connected:
        kb = xbmc.Keyboard("", "Enter Password", False)
        kb.doModal()
        if (kb.isConfirmed()):
            key = kb.getText()
            errors = qfpynm.validate_wifi_input(key, encryption)

        if key == "" or errors != '':
            return True, connection_created, con_path
    
    if encryption == 'WEP':
        wep_alg = 'shared'
    else:
        wep_alg = ''

    if not was_connected:
        con_path = qfpynm.add_wifi(ssid, key, encryption, wep_alg, True)
    else:
        aUUID = qfpynm.get_con_uuid_by_path(con_path)
        qfpynm.activate_connection(aUUID)

    for i in range(1, 150):
        state, stateTXT = qfpynm.get_device_state(qfpynm.get_wifi_device())
        if (i > 10 and state == 60) or (i > 10 and state == 30) or (state == 100 and i > 2):
            break
        time.sleep(1)
    if state == 100:
        return True, True, con_path
    if (state == 60 or state == 30) and encryption != "NONE":
        return False, True, con_path

    return True, True, con_path

if __name__ == '__main__':
    plugin.run()
