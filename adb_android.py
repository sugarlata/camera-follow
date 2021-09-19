from ppadb.client import Client as AdbClient


class ADBControl:

    def __init__(self, config):

        self._adb_server_host = config.get("adb_server_host", "127.0.0.1")
        self._adb_server_port = config.get("adb_server_port", 5037)
        self._adb_device_number = config.get("adb_device_number", 0)

        self._client = AdbClient(host=self._adb_server_host, port=self._adb_server_port)
        self._device = self._client.devices()[self._adb_device_number]

    def _adb_shell(self, command):

        self._device.shell(command)

    def take_photo(self):

        self._adb_shell("input keyevent KEYCODE_CAMERA")


if __name__ == '__main__':

    adb_conn = ADBControl({})
    adb_conn.take_photo()