#!/usr/bin/python3
import PyChromeDevTools
import time
import sys
import subprocess
import os
import json
import signal
import shutil
import random
import re

PORT=random.randint(2000,10000)
PROFILE_DIR="/tmp/tester_profile_" +str(PORT)
CHROME_CMD="google-chrome --remote-debugging-port="+str(PORT)+" --headless --user-data-dir="+PROFILE_DIR
MIN_TIME = 60*60*24*30 # 1 MONTH
tracker_file="trackers_ghostery_disconnect"
SHORT_TIMEOUT=1
LONG_TIMEOUT=60

# Global vars
tracker_list=set()

def main():

    # Parse Arg
    # Strip Eventual "http://"
    if "/" in sys.argv[1]:
        url = sys.argv[1]
    else:
        url="http://" + sys.argv[1] + "/"  

    # Load Tracker List
    global tracker_list
    with open(tracker_file, 'r') as f:
        for line in f:
            tracker_list.add(line.strip())

    # Start Chrome
    shutil.rmtree(PROFILE_DIR, ignore_errors=True)
    FNULL = open(os.devnull, 'w')
    proc = subprocess.Popen(CHROME_CMD, shell=True, stdin=None, stdout=FNULL, 
                            stderr=subprocess.STDOUT, close_fds=True, preexec_fn=os.setsid)
    time.sleep(SHORT_TIMEOUT)

    # Connect Python wrapper
    chrome = PyChromeDevTools.ChromeInterface(port=PORT)
    chrome.Network.enable()
    chrome.Page.enable()

    # Navigate to URL and wait it to load
    start_time=time.time()
    chrome.Page.navigate(url=url)
    _,messages_1=chrome.wait_event("Page.frameStoppedLoading", timeout=LONG_TIMEOUT)
    time.sleep(SHORT_TIMEOUT*2)
    messages_2=chrome.pop_messages()

    chrome.Page.navigate(url=url)
    _,messages_3=chrome.wait_event("Page.frameStoppedLoading", timeout=LONG_TIMEOUT)
    time.sleep(SHORT_TIMEOUT*2)
    messages_4=chrome.pop_messages()

    # Get all contacted domains
    all_domains=set()
    messages=messages_1+messages_2+messages_3+messages_4
    for m in messages:
        if "method" in m and m["method"] == "Network.responseReceived":
            try:
                this_domain=m["params"]["response"]["url"].split("/")[2]
                all_domains.add(this_domain)
            except:
                continue

    # Find Cookies and Trackers
    first_party=get2LD(url.split("/")[2])
    result={"trackers_cookies":set(),"trackers_no_cookies":set(), "other_cookies":set()}
    cookies=chrome.Network.getAllCookies()
    for cookie in cookies["result"]["cookies"]:
        if is_tracker(cookie["domain"]):
            tracker=True
        else:
            tracker=False
    
        if get2LD(cookie["domain"]) != first_party:
            third_party=True
        else:
            third_party=False

        if cookie["expires"] - start_time > MIN_TIME:
            persistent=True
        else:
            persistent=False

        if tracker and persistent:
            result["trackers_cookies"].add(cookie["domain"].strip("."))
        elif third_party and not tracker and persistent:
            result["other_cookies"].add(cookie["domain"].strip("."))

    # Add trackers without cookie
    for domain in all_domains:
        try:
            domain_SLD=getGood2LD(domain)
            if is_tracker(domain):
                if not domain     in result["trackers_cookies"] and \
                   not domain_SLD in result["trackers_cookies"] and \
                   not domain     in result["other_cookies"]    and \
                   not domain_SLD in result["other_cookies"]:
                    result["trackers_no_cookies"].add(domain)
        except:
            continue
    # Convert sets to lists
    for k in result:
        result[k]=list(result[k])
    print (json.dumps(result))

    # Kill Chrome and delete profile
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    shutil.rmtree(PROFILE_DIR, ignore_errors=True)


def is_tracker(host):

    global tracker_list  
    
    if host             in tracker_list or \
       getGood2LD(host) in tracker_list or \
       get3LD (host)    in tracker_list:
        return True
    
    else:
        return False


# False TLDs
bad_domains=set("co.uk co.jp co.hu co.il com.au co.ve .co.in com.ec com.pk co.th co.nz com.br com.sg com.sa \
com.do co.za com.hk com.mx com.ly com.ua com.eg com.pe com.tr co.kr com.ng com.pe com.pk co.th \
com.au com.ph com.my com.tw com.ec com.kw co.in co.id com.com com.vn com.bd com.ar \
com.co com.vn org.uk net.gr".split())

# Cut a domain after 2 levels
# e.g. www.google.it -> google.it
def get2LD(fqdn):
    if fqdn[-1] == ".":
        fqdn = fqdn[:-1]    
    names = fqdn.split(".")
    tln_array = names[-2:]
    tln = ""
    for s in tln_array:
        tln = tln + "." + s
    return tln[1:]

# Cut a domain after 2 levels considering long TLDs
# e.g. www.google.it -> google.it
def getGood2LD(fqdn):
    if fqdn[-1] == ".":
        fqdn = fqdn[:-1]    
    names = fqdn.split(".")
    if ".".join(names[-2:]) in bad_domains:
        return get3LD(fqdn)
    tln_array = names[-2:]
    tln = ""
    for s in tln_array:
        tln = tln + "." + s
    return tln[1:]

# Cut a domain after 3 levels
# e.g. www.c3.google.it -> c3.google.it
def get3LD(fqdn):
    if fqdn[-1] == ".":
        fqdn = fqdn[:-1]
    names = fqdn.split(".")
    tln_array = names[-3:]
    tln = ""
    for s in tln_array:
        tln = tln + "." + s
    return tln[1:]

main()




