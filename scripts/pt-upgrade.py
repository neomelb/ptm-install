import os
import json
import urllib2
import zipfile


pt = 'n'
ptpath = '/opt/PT'
upgrade = 'n'


def moveForward():
    global pt
    global ptpath
    global upgrade

    upgrade = raw_input(
        "Do you want to upgrade ProfitTrailer? (y/n): ").lower()
    if "y" in upgrade:
        print("Ok, we'll upgrade...")        
        ptpath = raw_input(
            "What's the path to your ProfitTrailer install (e.g. /opt/ProfitTrailer)? ")
        if ptpath.startswith('/') and not ptpath.endswith('/'):
            try:
                os.path.exists("%s/application.properties" % ptpath)
                print("Looks good")
            except KeyError:
                print("That path doesn't seem to be correct")
                exit(1)
        else:
            ptpath = ptpath.rstrip("/")
    else:
        print("Ok, If you don't want to update ProfitTrailer, then we've got nothing \
           to do here.  Goodbye")
        exit(1)


def getPt():
    """
    Download Latest PT
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
    procPt(dloc)


def procPt(data):
    """
    Process pt zip previously downloaded
    """
    #print("Extracting %s to /opt/") % (data)
    zip = zipfile.ZipFile(data)
    zip.extractall('/tmp/')
    os.system('cp -r /tmp/ProfitTrailer/ProfitTrailer.jar %s' % ptpath)
    if "y" in upgrade:
        if os.path.exists('/etc/systemd/system/profit.service'):
            os.system("systemctl restart profit")
            print("ProfitTrailer has been upgraded and restarted!")
        else:
            print(
                "ProfitTrailer has been upgraded, you will need \
                    to restart ProfitTrailer now.")
    os.system('rm -rf /tmp/ProfitTrailer*')


if __name__ == '__main__':
    moveForward()
    if "y" in upgrade:
        getPt()
