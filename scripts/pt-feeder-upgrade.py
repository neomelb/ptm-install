import os
import json
import urllib2
import zipfile


ptfeeder = 'n'
ptfpath = 'blank'
upgrade = 'n'


def moveForward():
    global ptfeeder
    global pmpath
    global upgrade

    upgrade = raw_input(
        "Do you want to upgrade PTFeeder? (y/n): ").lower()
    if "y" in upgrade:
        print("Ok, we'll upgrade...")
        pmpath = raw_input(
            "What's the path to your PTFeeder install (e.g. /opt/PTFeeder)? ")
        if pmpath.startswith('/') and not pmpath.endswith('/'):
            try:
                os.path.exists("%s/settings.general.json" % pmpath)
            except KeyError:
                print("That path doesn't seem to be correct")
        else:
            pmpath = pmpath.rstrip("/")
    else:
        print("Ok, If you don't want to update PTFeeder, then we've got nothing \
           to do here.  Goodbye")
        exit(1)


def getPTFeeder():
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
    procPtfeeder(dloc)


def procPtfeeder(data):
    """
    Process ptfeeder zip previously downloaded
    """
    print("Extracting %s to /opt/") % (data)
    zip = zipfile.ZipFile(data)
    zip.extractall('/tmp/')
    os.system("rm -rf /tmp/pt-feeder*/config")
    os.system("rm -rf /tmp/pt-feeder*/database")
    os.system('cp -r /tmp/pt-feeder*/* /opt/PTFeeder/')
    if "y" in upgrade:
        if os.path.exists('/etc/systemd/system/ptfeeder.service'):
            os.system("systemctl restart ptfeeder")
            os.system("sleep 5 && systemctl restart ptfeeder-monitor")
            print("PTFeeder has been upgraded and restarted!")
        else:
            print(
                "PTFeeder has been upgraded, you will need \
                    to restart PTFeeder")
    os.system('rm -rf /tmp/PTFeeder*')


if __name__ == '__main__':
    moveForward()
    if "y" in upgrade:
        getPTFeeder()
