import sys
import getopt
import ftplib
import ssl
import os


_DEFAULT_LOCAL_FILENAME = "inventory.html"
_DEFAULT_REMOTE_DIRECTORY = 'httpdocs'
_DEFAULT_FTP_PORT=21
_DEFAULT_FTPS_PORT=990

_OPTION_HELP = '-h'
_OPTION_FILENAME = '-f'
_OPTION_SERVER = '-s'
_OPTION_USERNAME = '-u'
_OPTION_PASSWORD = '-p'
_OPTION_INSECURE = '-x'


class Upload:

    def __init__(self, server='', port=_DEFAULT_FTPS_PORT, username='', password='', use_tls=True, filename=_DEFAULT_LOCAL_FILENAME):
        self.server = server
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.port = port
        self.filename = filename
        self.ftp_connection = None


    def connect(self):
        try:
            if (self.use_tls):
                self.ftp_connection = ftplib.FTP_TLS(self.server)
                self.ftp_connection.context = ssl.SSLContext()
                self.ftp_connection.context.check_hostname = False
            else:
                self.ftp_connection = ftplib.FTP(self.server)

            #self.ftp_connection.set_debuglevel(2)

            self.ftp_connection.login(user=self.username, passwd=self.password)
            self.ftp_connection.getwelcome()

        except Exception as e:
            print(e)

    def disconnect(self):
        try:
            self.ftp_connection.close()
        except Exception as e:
            print(e)

    def upload_file(self, filename=None):
        try:
            if filename is not None:
                self.filename = filename

            #if (self.use_tls):
            #        self.ftp_connection.prot_p()

            with open(self.filename, 'rb') as fp:
                self.ftp_connection.storbinary('STOR ' + self.filename, fp)
            remote_size = self.ftp_connection.size(self.filename)

            local_size = os.path.getsize(self.filename)
            if (local_size != remote_size):
                print('WARNING! {} failed to upload'.format(self.filename))

        except Exception as e:
            print(e)

def print_usage():
    print('Usage: upload.py -f <HTML file name>')
    print('')
    print('\t-f\tthe name of the HTML file to upload to the web site')
    print('\t-u\tthe username of the ftp account')
    print('\t-p\tthe password for the ftp account ')
    print('\t-s\tthe web server to upload the file to')
    print('\t-x\tuse insecure method (this is bad, try not to do this)')
    print('\t-h\tprints out this message')
    print('Examples:')
    print('\tupload.py -f inventory.html -u auto -p password -s normsbeerandwine.com')
    print('')


def main(argv):
    try:
        # See Python3 getopt class for details on the short option configuration string format
        # https://docs.python.org/3/library/.getopt.html
        short_options_config = _OPTION_HELP[1:] + _OPTION_FILENAME[1:] + ':' + _OPTION_SERVER[1:] + ':' + _OPTION_USERNAME[1:] + ':'+ _OPTION_PASSWORD[1:] + ':'+ _OPTION_INSECURE[1:] + ':'
        opts, args = getopt.getopt(argv, short_options_config)

        upload = Upload(server='normsbeerandwine.com', username='auto', use_tls=True, filename='inventory.json')
        upload.password = '3Gycw@58'

        for opt, arg in opts:
            if opt == _OPTION_HELP:
                print_usage()
                sys.exit()
            elif opt == _OPTION_FILENAME:
               upload.filename = arg
            elif opt == _OPTION_USERNAME:
                upload.username = arg
            elif opt == _OPTION_PASSWORD:
                upload.password = arg
            elif opt == _OPTION_FILENAME:
                upload.filename = arg
            elif opt == _OPTION_INSECURE:
                upload.use_tls = False
                upload.port = _DEFAULT_FTP_PORT

        upload.connect()
        upload.upload_file()
        upload.disconnect()

    except Exception as e:
        print(e)
        print('')
        print_usage()
        sys.exit(2)

if __name__ == "__main__":
    main(sys.argv[1:])
