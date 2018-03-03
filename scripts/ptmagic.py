
import os
import json
import urllib2
import zipfile
import platform
from shutil import copyfile
import re
import fileinput
import time
import subprocess
import sys
import pwd


ptmagic = 'n'
ptpath = 'ProfitTrailer'
pmpath = 'PTMagic'
exch = 'Binance'
upgrade = 'n'



def moveForward():
    global ptmagic
    global ptpath
    global pmpath
    global upgrade
    
    ptmagic = raw_input(
        "Do you want to setup PTMagic? (y/n): ").lower()
    if "y" in ptmagic.lower():
        print("Thanks, will do.")
        time.sleep(1)
        ptpath = raw_input(
            "What's the path to your Proft Trailer install (e.g. /$HOME/ProfitTrailer)? ")
        if ptpath.startswith('/') and not ptpath.endswith('/'):
            try:
                os.path.exists("%s/application.properties" % ptpath)
            except KeyError:
                print("That path doesn't seem to be correct")
        else:
            ptpath = ptpath.rstrip("/")


def getPtmagic():
    """
    Download Latest PTMagic
    """
    d = json.loads(urllib2.urlopen(
        "https://api.github.com/repos/Legedric/ptmagic/releases/latest").read())
    url = d["assets"][0]["browser_download_url"]
    file_name = d["assets"][0]["name"]
    dloc = "/tmp/%s" % file_name
    u = urllib2.urlopen(url)
    f = open(dloc, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print("Downloading: %s Bytes: %s") % (file_name, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (
            file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8) * (len(status) + 1)
        print status,

    f.close()
    procPtmagic(dloc)


def procPtmagic(data):
    """
    Process ptmagic zip previously downloaded
    """
    print("Extracting %s to /$HOME/") % (data)    
    zip = zipfile.ZipFile(data)
    zip.extractall('/tmp/')
    os.system('cp -r /tmp/PTMagic*/PTMagic /$HOME/')    
    if "n" in upgrade:
        os.system('cp -r /tmp/PTMagic*/_default\ settings/* /$HOME/PTMagic/')
        os.system("cp -r %s/trading/* /$HOME/PTMagic/_presets/Default/" % ptpath)        
    if "y" in upgrade:
        if os.path.exists('/etc/systemd/system/ptmagic.service'):            
            os.system("systemctl restart ptmagic")
            os.system("sleep 5 && systemctl restart ptmagic-monitor")
            print("PTMagic has been upgraded and restarted!")
        else:
            print("PTMagic has been upgraded, you will need to restart PTMagic and PTMagic-Monitor")
    os.system('rm -rf /tmp/PTMagic*')

'''
def getExchange():
    global exch
    while True:
        try:
            exch = int(raw_input(
                "Which Exchange?\n\t1) Binance\n\t2) Bittrex\n\t3) Poloniex\n\tSelection: "))
        except TypeError:
            print("Please select a number 1-3.")
            time.sleep(1)
            continue
        else:
            break
    if int(exch) == 1:
        exch = 'Binance'
    elif int(exch) == 2:
        exch = 'Bittrex'
    elif int(exch) == 3:
        exch = 'Poloniex'
    else:
        print("Please try again and select a number 1-3.")
        time.sleep(1)
        exit(1)
    print("\tYou selected: %s" % exch)
    if "y" in ptmagic.lower():
        ptmagicConfig(exch)
'''

def ptmagicConfig(exch):
    for line in fileinput.input(["%s/application.properties" % ptpath], inplace=1):
        line = re.sub('trading.logHistory = \d+',
                      'trading.logHistory = 9999', line.strip())
        print(line)
    for line in fileinput.input(["/$HOME/PTMagic/settings.general.json"], inplace=1):
        line = re.sub('\"ProfitTrailerPath\": \".*\",',
                      '\"ProfitTrailerPath\": \"%s/\",' % (ptpath), line.strip())
        line = re.sub("\"Exchange\": \"Bittrex\"\,",
                      "\"Exchange\": \"%s\"," % (exch.capitalize()), line.strip())
        line = re.sub("\"TestMode\": \"false\"\,",
                      "\"TestMode\": \"true\",", line.strip())
        print(line)
    for line in fileinput.input(["/$HOME/PTMagic/Monitor/appsettings.json"], inplace=1):
        line = re.sub('\"PTMagicBasePath\": \".*\",',
                      '\"PTMagicBasePath\": \"/$HOME/PTMagic/\",', line.strip())
        print(line)
    ptmagicStartUpScripts()


def ptmagicStartUpScripts():
    fpath = os.path.abspath(sys.argv[0]).rsplit('/', 2)[0]
    o = str(platform.dist()[0])
    minor = str(platform.dist()[1])
    try:
        pwd.getpwnam('profit')
    except KeyError:
        os.system("useradd profit -d /$HOME -s /bin/false -r")
    os.system('chown -R profit:profit /$HOME/PTMagic')
    if o == 'Ubuntu':
        os.system("curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg")
        os.system("mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg")
        if minor == '16.04':
            copyfile("%s/files/microsoft-1604.list" % fpath,
                     "/etc/apt/sources.list.d/microsoft.list")
        elif minor == '17.04':
            copyfile("%s/files/microsoft-1704.list" % fpath,
                     "/etc/apt/sources.list.d/microsoft.list")
        elif minor == '17.10':
            copyfile("%s/files/microsoft-1710.list" % fpath,
                     "/etc/apt/sources.list.d/microsoft.list")
        else:
            print "Sorry, only Ubuntu 16.04, 17.04, and 17.10 are currently supported"
            exit(1)
        os.system('apt-get install apt-transport-https -y')
        os.system('apt-get update -y')
        os.system('apt-get install dotnet-sdk-2.1.4 -y')
    elif o == 'centos' or o == 'redhat':
        os.system("rpm --import https://packages.microsoft.com/keys/microsoft.asc")
        copyfile("%s/files/microsoft.repo" % fpath,
                 "/etc/yum.repos.d/microsoft.repo")
        os.system("yum install -y dotnet-sdk-2.1.4 libunwind libicu")
    elif o == 'debian':
        minor = float(platform.dist()[1])
        os.system("apt-get install curl libunwind8 gettext apt-transport-https -y")
        os.system("curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg")
        os.system("mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg")
        if minor > 9:
            copyfile("%s/files/microsoft-9.list" % fpath,
                "/etc/apt/sources.list.d/microsoft.list")
        elif minor < 9:
            copyfile("%s/files/microsoft-8.list" % fpath,
                "/etc/apt/sources.list.d/microsoft.list")
        else:
            print("Sorry, your version of Debian is currently not supported")
        os.system("apt-get update -y")
        os.system("apt-get install dotnet-sdk-2.1.4 -y")
    else:
        print("Sorry, your OS is not currently supported")
        exit(1)

    if o == 'centos' or o == 'Ubuntu' or o == 'redhat' or o == 'debian':
        copyfile("%s/files/ptmagic.service" % fpath,
                 "/etc/systemd/system/ptmagic.service")
        os.system("cp -r %s/files/ptmagic.service.d /etc/systemd/system/" % fpath)
        copyfile("%s/files/ptmagic-monitor.service" % fpath,
                 "/etc/systemd/system/ptmagic-monitor.service")
        os.system("cp -r %s/files/ptmagic-monitor.service.d /etc/systemd/system/" % fpath)
        os.system("systemctl daemon-reload")
        os.system("systemctl enable ptmagic")
        os.system("systemctl enable ptmagic-monitor")
        subprocess.Popen(
            'systemctl start ptmagic && sleep 600 && systemctl start ptmagic-monitor', shell=True)

        ip = urllib2.urlopen("http://icanhazip.com").read()
        print("\n=============================================================\n")
        print("PTMagic has now been installed to /$HOME/PTMagic")
        print("Be sure to edit your config files  to set market conditions in /$HOME/PTMagic/settings.analyzer.json")
        print("PTMagic-Monitor will be started after 10 minutes once PTMagic is done running")
        print("PTMagic once it's running will be in test mode, so edit /$HOME/PTMagic/settings.general.json to make it live!")
        print("Your PTMagic will be available at http://%s:5000/") % ip.strip()
        print("\n=============================================================\n\n")
    else:
        print("Sorry, your OS is not currently supported")
        exit(1)


if __name__ == '__main__':
    moveForward()
    if "y" in ptmagic.lower():
        getPtmagic()
        getExchange()
    if "y" in upgrade:
        getPtmagic()

