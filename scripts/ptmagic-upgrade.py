import os
import json
import urllib2
import zipfile


ptmagic = 'n'
pmpath = '/opt/PTMagic'
upgrade = 'n'


def moveForward():
    global ptmagic
    global pmpath
    global upgrade

    upgrade = raw_input(
        "Do you want to upgrade PTMagic? (y/n): ").lower()
    if "y" in upgrade:
        print("Ok, we'll upgrade...")
        pmpath = raw_input(
            "What's the path to your PTMagic install (e.g. /opt/PTMagic)? ")
        if pmpath.startswith('/') and not pmpath.endswith('/'):
            try:
                os.path.exists("%s/settings.general.json" % pmpath)
            except KeyError:
                print("That path doesn't seem to be correct")
        else:
            pmpath = pmpath.rstrip("/")
    else:
        print("Ok, If you don't want to update PTMagic, then we've got nothing \
           to do here.  Goodbye")
        exit(1)


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
    print("Extracting %s to /opt/") % (data)
    zip = zipfile.ZipFile(data)
    zip.extractall('/tmp/')
    os.system('cp -r /tmp/PTMagic*/PTMagic /opt/')
    if "y" in upgrade:
        if os.path.exists('/etc/systemd/system/ptmagic.service'):
            os.system("systemctl restart ptmagic")
            os.system("sleep 5 && systemctl restart ptmagic-monitor")
            print("PTMagic has been upgraded and restarted!")
        else:
            print(
                "PTMagic has been upgraded, you will need \
                    to restart PTMagic and PTMagic-Monitor")
    os.system('rm -rf /tmp/PTMagic*')


if __name__ == '__main__':
    moveForward()
    if "y" in upgrade:
        getPtmagic()
