import os
import json
import urllib2
import zipfile
import platform
from shutil import copyfile
import getpass
import re
import fileinput
import pwd
import time
from datetime import datetime
import sys
import subprocess

ptrailer = 'n'
ptpath = '/opt/ProfitTrailer'
exch = 'blank'


def moveForward():
    global ptrailer
    global ptpath
    ptrailer = raw_input(
        "Do you want to setup ProfitTrailer? (y/n): ").lower()
    if "y" in ptrailer.lower():
        print("You're the boss.")
        time.sleep(1)
        answer = raw_input(
            "Have you already registered your API key for ProfitTrailer? (y/n): ")
        if "y" in answer.lower():
            print("Thanks, continuing the setup.")
            time.sleep(1)
        else:
            print("Please go register your API key first.\nhttps://wiki.profittrailer.io/doku.php/faq#registering_api_keys_for_pt")
            exit(1)
        keys = raw_input(
            "Do you already have two API keys for your Exchange already? (y/n): ")
        if "y" in keys.lower():
            print("moving along...")
            time.sleep(1)
        else:
            print("Please go create two API keys first.\nhttps://wiki.profittrailer.io/doku.php/instructions#create_an_exchange_account_get_your_api_keys")
            exit(1)


def fileDownload():
    """
    Download Latest Profit Trailer
    """
    d = json.loads(urllib2.urlopen(
        "https://api.github.com/repos/taniman/profit-trailer/releases/latest").read())
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
    os.system("rm -rf /tmp/ProfitTrailer.zip")


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
    if "y" in ptrailer.lower():
        getApiKeys(exch)


def getApiKeys(exch):
    passwd = getpass.getpass("Web Password: ")
    print("\tYou entered: %s" % passwd)
    api1 = raw_input("First, API Key (default_apiKey): ")
    sec1 = raw_input("First, Secret Key (default_apiSecret): ")
    api2 = raw_input("Second, API Key(trading_apiKey): ")
    sec2 = raw_input("Second, Secret Key(trading_apiSecret): ")
    createConfig(exch, passwd, api1, sec1, api2, sec2)


def createConfig(exch, passwd, api1, sec1, api2, sec2):
    fpath = os.path.abspath(sys.argv[0]).rsplit('/', 2)[0]
    copyfile("%s/files/application.tmpl" % fpath,
             "/opt/ProfitTrailer/application.properties")
    for line in fileinput.input(["/opt/ProfitTrailer/application.properties"], inplace=1):
        line = re.sub('mktplc', exch.upper(), line.strip())
        line = re.sub('passwd', passwd, line.strip())
        line = re.sub('api1', api1, line.strip())
        line = re.sub('sec1', sec1, line.strip())
        line = re.sub('api2', api2, line.strip())
        line = re.sub('sec2', sec2, line.strip())
        print(line)
    for line in fileinput.input(["/opt/ProfitTrailer/configuration.properties"], inplace=1):
        line = re.sub('testMode=false', 'testMode=true', line.strip())
        print(line)
    startUpScripts()

def startUpScripts():
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
    
    os.system("chown -R profit:profit /opt/ProfitTrailer")
    
    if oper == 'centos' or oper == 'Ubuntu' or oper == 'redhat' or oper == 'debian':
        copyfile("%s/files/profit.service" % fpath,
                 "/etc/systemd/system/profit.service")
        os.system("cp -r %s/files/profit.service.d /etc/systemd/system/" % fpath)
    else:
        print("Sorry, your OS is not currently supported")
        exit(1)
    jdkInstall()

def jdkInstall():
    oper = str(platform.dist()[0])
    if oper == 'Ubuntu' or oper == 'debian':        
        os.system("apt-get install default-jdk -y")
    else:
        print("Not a supported OS")
    if oper == 'centos' or oper == 'redhat':
        os.system("yum install -y java-1.8.0-openjdk")  
    else:
        print("Not a supported OS")
    finalSteps()


def finalSteps():
    os.system("systemctl daemon-reload")
    os.system("systemctl enable profit")
    os.system("systemctl start profit")
    ip = urllib2.urlopen("http://icanhazip.com").read()        
        
    print("\n=============================================================\n")
    print("Your Keys have been entered in /opt/ProfitTrailer/application.properties")
    print("Be sure to edit your config files in /opt/ProfitTrailer/")
    print("ProfitTrailer has been started and is running in testMode")
    print("Your install is now available at http://%s:8081/monitoring") % ip.strip()
    print("\n=============================================================\n\n")




if __name__ == '__main__':
    moveForward()
    if "y" in ptrailer.lower():
        fileDownload()
        getExchange()
    