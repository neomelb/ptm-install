import os
import json
import zipfile
import platform
from shutil import copyfile
import re
import fileinput
import pwd
import time
from datetime import datetime
import sys
import subprocess
import urllib2

pfeeder = 'n'
ptpath = 'blank'
base_coin = 'blank'


def moveForward():
    """
    Verify they really want to setup PTF
    """
    global pfeeder
    global ptpath
    pfeeder = raw_input(
        "Do you want to setup PTFeeder? (y/n): ").lower()
    if "y" in pfeeder.lower():
        print("You're the boss.")
        time.sleep(1)
        answer = raw_input(
            "Have you already registered your API key for PTFeeder? (y/n): ")
        if "y" in answer.lower():
            print("Thanks, continuing the setup.")
            time.sleep(1)
        else:
            print("Please go register your API key first.\nhttps://github.com/mehtadone/PTFeeder/wiki/License-Registration-and-Activation")
            exit(1)
    ptpath = raw_input(
        "What's the path to your Proft Trailer install (e.g. /opt/ProfitTrailer)? ")
    if ptpath.startswith('/') and not ptpath.endswith('/'):
        try:
            os.path.exists("%s/application.properties" % ptpath)
        except KeyError:
            print("That path doesn't seem to be correct")
    else:
        ptpath = ptpath.rstrip("/")


def fileDownload():
    """
    Download Latest PTFeeder
    """
    d = json.loads(urllib2.urlopen(
        "https://api.github.com/repos/mehtadone/PTFeeder/releases/latest").read())
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
    procFile(dloc)


def procFile(data):
    """
    Process zip previously downloaded
    """
    print("Extracting %s to /opt/") % (data)
    zip = zipfile.ZipFile(data)
    zip.extractall('/opt/')
    os.system("rm -rf /tmp/pt-feeder*.zip")


def getBaseCoin():
    """
    Get the Base Coin they use
    """
    global base_coin
    while True:
        try:
            base_coin = int(raw_input(
                "What's your base coin?\n\t1) BTC\n\t2) ETH\n\t3) USDT\n\tSelection: "))
        except TypeError:
            print("Please select a number 1-3.")
            time.sleep(1)
            continue
        else:
            break
    if int(base_coin) == 1:
        base_coin = 'BTC'
    elif int(base_coin) == 2:
        base_coin = 'ETH'
    elif int(base_coin) == 3:
        base_coin = 'USDT'
    else:
        print("Please try again and select a number 1-3.")
        time.sleep(1)
        exit(1)
    print("\tYou selected: %s" % base_coin)
    getKey(base_coin)


def getKey(base_coin):
    """
    Get PTF License Key
    """
    license_key = raw_input(
        "PTFeeder License Key (e.g. XXXX-XXXX-XXXX-XXXX): ")
    createConfig(base_coin, license_key)


def createConfig(base_coin, license_key):
    """
    Create the config for PTF
    """
    fpath = os.path.abspath(sys.argv[0]).rsplit('/', 2)[0]
    for line in fileinput.input(["/opt/PTFeeder/hostsettings.json"], inplace=1):
        line = re.sub('\"LicenseKey\": \"\"',
                      '\"LicenseKey\": \"%s\"' % license_key, line.strip())
        line = re.sub('\"ProfitTrailerFolder1\": \"\"',
                      '\"ProfitTrailerFolder1\": \"%s\"' % pt_location, line.strip())
        print(line)
    for line in fileinput.input(["/opt/PTFeeder/appsettings.json"], inplace=1):
        line = re.sub('\"BaseCurrency\": \"BTC\"',
                      '\"BaseCurrency\": \"%s\"' % base_coin, line.strip())
        print(line)
    os.system("cp -r %s/trading /tmp/trading.bak" % pt_location)
    startUpScripts()


def startUpScripts():
    """
    Create the user and startup scripts
    """
    fpath = os.path.abspath(sys.argv[0]).rsplit('/', 2)[0]
    oper = str(platform.dist()[0])

    def finduser(name):
        try:
            return pwd.getpwnam(name)
        except KeyError:
            return None

    if not finduser("profit"):
        print("creating user...")
        os.system("useradd profit -d /opt -s /bin/false -r")
    else:
        print("user already exists")

    os.system("chown -R profit:profit /opt/PTFeeder")

    if oper == 'centos' or oper == 'Ubuntu' or oper == 'redhat' or oper == 'debian':
        copyfile("%s/files/ptfeeder.service" % fpath,
                 "/etc/systemd/system/ptfeeder.service")
        os.system("cp -r %s/files/ptfeeder.service.d /etc/systemd/system/" % fpath)
    else:
        print("Sorry, your OS is not currently supported")
        exit(1)
    dotnetInstall()


def dotnetInstall():
    """
    Install dotnet
    """
    oper = str(platform.dist()[0])
    if o == 'Ubuntu':
        os.system(
            "curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg")
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
        os.system(
            "curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg")
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
    finalSteps()


def finalSteps():
    """
    Enable and start PTF
    """
    os.system("systemctl daemon-reload")
    os.system("systemctl enable ptfeeder")
    os.system("systemctl start ptfeeder")

    print("\n=============================================================\n")
    print("Your PTFeeder has been installed to /opt/PTFeeder/")
    print("Your License Key has been entered in /opt/PTFeeder/config/hostsettings.json")
    print("Be sure to edit your config files in /opt/PTFeeder/config/")
    print("A backup of your ProfitTrail settings has been created at /tmp/trading.bak")
    print("PTFeeder has been started")
    print("PTFeeder can be controlled with \'sudo systemctl <start|stop|restart|status> ptfeeder\'")
    print("\n=============================================================\n\n")


if __name__ == '__main__':
    moveForward()
    if "y" in pfeeder.lower():
        fileDownload()
        getBaseCoin()
