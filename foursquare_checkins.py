#!/usr/bin/env python3

# pip3 install requests --user

import inspect
import math
import time
import sys
import re

import csv
import json

import argparse
import configparser

import warnings
with warnings.catch_warnings(record=True) as w:
    # ignore OpenSSL Warnings on MacOS
    import requests
    for wi in w:
        if wi.category.__name__!='NotOpenSSLWarning':
            print(wi.filename+":"+str(wi.lineno)+": "+str(wi._category_name)+": "+str(wi.message),file=sys.stderr)
        pass
    pass

user_id = None
oauth_token = None

def get_checkins(offset,limit,afterTimestamp=0):
    #url = "https://api.foursquare.com/v2/users/"+user_id+"/historysearch?locale=en&v=20220920&offset="+str(offset)+"&limit="+str(limit)+"&sort=oldestfirst&oauth_token="+oauth_token
    url = "https://api.foursquare.com/v2/users/self/checkins?locale=en&v=20231231&offset="+str(offset)+"&limit="+str(limit)+"&sort=newestfirst&oauth_token="+oauth_token
    if (afterTimestamp>0):
        url += "&afterTimestamp="+str(afterTimestamp)
        pass
    print(url)
    return requests.get(url)

def clean_checkin(item):
    for key in ["canonicalUrl","canonicalPath"]:
        item.pop(key,"")
        pass
    venue = item["venue"]
    for key in ["contact","allowMenuUrlEdit","menu","deliveryProviders","delivery","reservations"]:
        venue.pop(key,"")
        pass
    location = venue["location"]
    for key in ["formattedAddress"]:
        location.pop(key,"")
        pass
    for category in venue["categories"]:
        for key in ["icon","mapIcon"]:
            category.pop(key,"")
            pass
        pass
    pass

def clean_config_value(value):
    return re.sub(r"^(['\"])(.*)\1$",r"\2",value)

if __name__ == '__main__':
    offset = 0
    limit = 100
    jsonfile = None
    afterTimestamp = 0
    
    aparser = argparse.ArgumentParser()
    aparser.add_argument('--jsonfile','-j',dest='jsonfile')
    aparser.add_argument('--new',action='store_true',dest='newfile',
                         help="create a new json file")
    aparser.add_argument('--exportcsv',action='store_true',dest='exportcsv')
    aparser.add_argument('--config',dest='configfile')
    args = aparser.parse_args()
    if (not args.jsonfile):
        aparser.print_help()
        sys.exit()
    else:
        jsonfile = args.jsonfile
        pass

    if (args.configfile):
        config = configparser.ConfigParser()
        configstring = '';
        with open(args.configfile,"r") as cf:
            configstring = cf.read()
            pass
        try:
            config.read_string(configstring)
        except configparser.MissingSectionHeaderError:
            configstring = "[user]\n"+configstring
            config.read_string(configstring)
            pass
        user_id = clean_config_value(config['user']["user_id"])
        oauth_token = clean_config_value(config['user']["oauth_token"])
        pass
    
    
    csvwriter = csv.writer(sys.stdout)
    column_defs = [['Date',['niceDate']],
                   ['Name',['venue','name']],
                   ['Category',['venue','categories',0,'name']],
                   ['Neighborhood',['venue','location','neighborhood']],
                   ['City',['venue','location','city']],
                   ['State',['venue','location','state']],
                   ['Country',['venue','location','country']],
                   ['LocationContext',['venue','location','contextLine']],
                   ['lat',['venue','location','lat']],
                   ['lng',['venue','location','lng']],
                   ['Comment',['shout']],
                   ]
    columns = map(lambda el:el[0],column_defs)
    if (args.exportcsv):
        csvwriter.writerow(columns)
        pass
    try:
        f = open(jsonfile,"r")
    except FileNotFoundError:
        if (not args.newfile):
            print(f"File {jsonfile} not found. aborting")
            sys.exit(1)
            pass
    else:
        afterTimestamp = 0
        for line in f:
            item = json.loads(line)
            createdAt = item['createdAt']
            if (createdAt>afterTimestamp):
                afterTimestamp = createdAt
                pass
            if (args.exportcsv):
                vals = []
                for cdef in column_defs:
                    val = ''
                    if (len(cdef)>1):
                        val = item
                        for key in cdef[1]:
                            if (isinstance(val,list)):
                                if (len(val)>int(key)):
                                    val = val[int(key)]
                                else:
                                    val = ''
                                    break
                                pass
                            elif key in val:
                                val = val[key]
                            else:
                                val = ''
                                break
                            pass
                        pass
                    vals.append(val)
                    pass
                csvwriter.writerow(vals)
                pass
            pass
        f.close()
        pass
    if (args.exportcsv):
        sys.exit(0)
    #afterTimestamp = 1704215344
    #afterTimestamp = 1703362182
    r = get_checkins(offset,1,afterTimestamp)
    rate_limit = r.headers["X-RateLimit-Limit"]
    rate_remaining = r.headers["X-RateLimit-Remaining"]
    #print(r.text)
    res = r.json()
    checkins = res['response']['checkins']['count']
    items = res['response']['checkins']['items']
    newitems = []
    if (len(items)>0):
        while (offset<checkins):
            query_size = 0
            if (offset+limit>checkins):
                query_size = checkins-offset
            else:
                query_size = limit
                pass
            r = get_checkins(offset,query_size,afterTimestamp)
            res = r.json()
            items = res['response']['checkins']['items']
            if (len(items)==0):
                break
            for item in items:
                name = item['venue']['name']
                tzoffset = item['timeZoneOffset']
                date = item['createdAt']
                date = time.gmtime(date+tzoffset*60)
                date = time.strftime("%Y/%m/%d %H:%M:%S",date)
                # add nice date
                item['niceDate'] = date
                newitems.append(item)
                #csvwriter.writerow([date,name,lat,lng])
                pass
            offset = offset+query_size
            if (len(items)<limit):
                break
            pass
        pass
    if (len(newitems)>0):
        newitems.reverse()
        f = open(jsonfile,"a")
        for item in newitems:
            # remove stuff we don't care about
            clean_checkin(item)
            json.dump(item,f)
            print("",file=f)
            pass
        f.close()


