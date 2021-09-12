print('Import os')
import os.path as path
print('Import arrow')
import arrow


PRINT_LOG = True
FILE_LOG = False


class EmotimoLogger:

    # TODO Send this to MQTT
    def __init__(self, log_location=''):
        self._fn = path.join(log_location, '%s.log' % arrow.now().format('YYYY-DD-MM'))
        self._writer = None

    def _open(self):
        if self._writer is None:

            if path.exists(self._fn):
                self._writer = open(self._fn, "a")
            else:
                self._writer = open(self._fn, "w")

    def _close(self):
        if self._writer is not None:
            self._writer.close()
            self._writer = None

    def write_log(self, module, status, message):

        epoch = arrow.utcnow().timestamp()

        log_str = "%s %s %s %s" % (
            str(epoch),
            '{format_string: <8}'.format(format_string=module),
            '{format_string: <8}'.format(format_string=status),
            message
        )

        if PRINT_LOG:
            print(log_str)

        if FILE_LOG:
            self._open()
            self._writer.write(log_str)
            self._close()
