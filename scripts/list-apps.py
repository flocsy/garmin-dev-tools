#!/usr/bin/env python3

import sys
import os
import getopt
import xml.etree.ElementTree as ET


def usage():
    cmd = os.path.basename(__file__)
    print(f'''{cmd} [options] <GarminDevice.xml>
options:
    -h|--help
    -a|--app-id <app-id>            <app-id>: the id of the app in the manifest.xml
    -m|--manifest <manifest.xml>    <manifest.xml>: path to manifest.xml
    -f|--format <format>            <format>: can be either a comma separated list of tags
                                    or a lower case string of the characters "asfnvt" corresponding to the tags
                                    default: AppId,StoreId,FileName,AppName,Version,AppType

examples:

    to list all the tags of all the apps on the device:
        {cmd} GarminDevice.xml

    to list all the tags of the app with app-id:
        {cmd} -a 12345678-90ab-cdef-1234-567890abcdef ../../GARMIN/GarminDevice.xml

    to list the FileName of the app corresponding to the manifest:
        {cmd} -m manifest.xml -f FileName GarminDevice.xml

    to list the AppName and Version:
        {cmd} -fnv GarminDevice.xml
''')


MANIFEST_NS = {'iq': 'http://www.garmin.com/xml/connectiq'}

NS = {
    'gd': 'http://www.garmin.com/xmlschemas/GarminDevice/v2',
    'iq': 'http://www.garmin.com/xmlschemas/IqExt/v1'
}

TAG_KEY_2_TAG = {'a': 'AppId', 's': 'StoreId', 'f': 'FileName', 'n': 'AppName', 'v': 'Version', 't': 'AppType'}


def get_manifest_app_id(manifest_xml_file):
    tree = ET.parse(manifest_xml_file)
    root = tree.getroot()
    application = root.findall('./iq:application', MANIFEST_NS)
    id = application[0].get('id')
    return id


def parse_garmin_device_xml(xml_file, manifest_app_id = None, format = None):
    tags = ['AppId', 'StoreId', 'FileName', 'AppName', 'Version', 'AppType']
    if format:
        custom_tags = []
        if format.islower():
            tag_keys = list(format)
        else:
            tag_keys = format.split(',')
        for tag in tag_keys:
            if tag in tags:
                custom_tags.append(tag)
            else:
                if tag in TAG_KEY_2_TAG:
                    val = TAG_KEY_2_TAG[tag]
                    if val:
                        custom_tags.append(val)
                else:
                    print(f'invalid tag key: {tag}')
        tags = custom_tags

    tree = ET.parse(xml_file)
    root = tree.getroot()
    apps = root.findall('./gd:Extensions/iq:IQAppExt/iq:Apps/iq:App', NS)
    # print('AppId,StoreId,FileName,AppName,Version,AppType')
    for app in apps:
        if manifest_app_id is None or app.find('iq:AppId', NS).text == manifest_app_id:
            # print(f'{app.find('iq:AppId', NS).text},{app.find('iq:StoreId', NS).text},{app.find('iq:FileName', NS).text},{app.find('iq:AppName', NS).text},{app.find('iq:Version', NS).text},{app.find('iq:AppType', NS).text}')
            line = ''
            for tag in tags:
                if line:
                    line += ','
                line += app.find(f'iq:{tag}', NS).text
            print(f'{line}')


def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'ha:m:f:', ['help', 'app-id', 'manifest', 'format'])
    except getopt.GetoptError as e:
        print(e)
        usage()
        sys.exit(1)
    manifest_app_id = None
    format = None
    for opt, arg in opts:
        if opt == '-h' or opt == '--help':
            usage()
            sys.exit(0)
        if opt == '-a' or opt == '--app-id':
            manifest_app_id = arg
        if opt == '-m' or opt == '--manifest':
            manifest_app_id = get_manifest_app_id(arg)
        if opt == '-f' or opt == '--format':
            format = arg
    xml_file = argv[len(argv) - 1]
    parse_garmin_device_xml(xml_file, manifest_app_id, format)


if __name__ == '__main__':
    main(sys.argv[1:])
