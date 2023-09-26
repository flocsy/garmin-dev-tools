#!/usr/bin/env python3

import sys
import os
import os.path
import re
import xml.etree.ElementTree as ET
import json
import warnings
import math
import datetime
import getopt
import shutil
# from packaging import version

SDK_DIR = f"{os.environ.get('HOME')}/Library/Application Support/Garmin/ConnectIQ"
if not os.path.isdir(SDK_DIR):
    sys.exit(f"Missing CIQ SDK: {SDK_DIR}")

CSV_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/csv'
DEVICE_2_MIN_VERSION_CSV = f"{CSV_DIR}/device2min-version.csv"
if not os.path.exists(DEVICE_2_MIN_VERSION_CSV):
    sys.exit(f"Missing: {DEVICE_2_MIN_VERSION_CSV}")

SOURCE_DEVICES_DIR = 'source-devices'

MONKEY_JUNGLE = 'monkey.jungle'
TEMPLATE = MONKEY_JUNGLE.replace('.jungle', '.template.jungle')

if not os.path.exists(TEMPLATE):
    sys.exit(f"Missing template file: {TEMPLATE}")

MANIFEST='manifest.xml'

GENERATROR_SIGNATURE=f"https://github.com/flocsy/garmin-dev-tools/tree/main/monkey-generator/ ©2022-{datetime.date.today().year} by flocsy"
COLOR_RED = '\033[91m'
COLOR_YELLOW = '\033[93m'
COLOR_RESET = '\033[00m'

SDK_DEVICES_DIR = f"{SDK_DIR}/Devices"
ALL_DEVICES = os.listdir(f"{SDK_DEVICES_DIR}")
ALL_DEVICES.sort()
# print(f"{ALL_DEVICES}")

NS = {'iq': 'http://www.garmin.com/xml/connectiq'}

APP_TYPE = ''
MIN_API_LEVEL = '1.0.0'
MANIFEST_DEVICES = []
MANIFEST_LANGS = []
IS_BETA = False

DEVICES = {}

DEVICE_MIN_VERSIONS = {}
with open(DEVICE_2_MIN_VERSION_CSV) as csv:
    for line in csv:
        dev, min_version = line.strip().split(':')
        DEVICE_MIN_VERSIONS[dev] = min_version

MULTI_FEATURE_DIR_SEPARATOR = '_AND_'
ALL_FEATURES = sorted(filter(lambda dir: MULTI_FEATURE_DIR_SEPARATOR not in dir, os.listdir('features'))) if os.path.isdir('features') else []
print(f"ALL_FEATURES: {ALL_FEATURES}")

def get_languages(device):
    langs = set()
    for partNumber in device['compiler']['partNumbers']:
        for lang in partNumber['languages']:
            langs.add(lang['code'])
    languages = sorted(list(langs))
    # print(f"{device['dev']} languages: {languages}")
    return languages

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]

# CIQ_VERSIONS = set()
# def get_ciq_apis(device):
#     global CIQ_VERSIONS
#     maxCiqVersions = set()
#     for partNumber in device['compiler']['partNumbers']:
#         maxCiqVersions.add(partNumber['connectIQVersion'])
#     maxCiqVersions = sorted(list(maxCiqVersions), key=natural_sort_key)
#     # print(f"{device['dev']}: maxCiqVersions: {maxCiqVersions}")
#     # CIQ_VERSIONS.update(maxCiqVersions)
#     # CIQ_VERSIONS |= set(maxCiqVersions)
#     return maxCiqVersions


def read_all_devices():
    global DEVICES, CIQ_VERSIONS
    for dev in ALL_DEVICES:
        device = {'dev': dev}
        with open(f"{SDK_DEVICES_DIR}/{dev}/compiler.json") as compiler_json:
            device['compiler'] = json.load(compiler_json)
        with open(f"{SDK_DEVICES_DIR}/{dev}/simulator.json") as simulator_json:
            device['simulator'] = json.load(simulator_json)
        device['languages'] = get_languages(device)
        # maxCiqVersions = get_ciq_apis(device)
        # CIQ_VERSIONS.update(maxCiqVersions)
        device['minVersion'] = DEVICE_MIN_VERSIONS[dev]
        if device['minVersion'] is None:
            print_error(f"{dev}: missing from DEVICE_MIN_VERSIONS")
        device['memory'] = {}
        for app_type in device['compiler']['appTypes']:
            device['memory'][app_type['type']] = app_type['memoryLimit']
        # print(f"{dev}: {device['memory']}")
        DEVICES[dev] = device
        # print(device)
    CIQ_VERSIONS = sorted(list(set(DEVICE_MIN_VERSIONS.values())), key=natural_sort_key)
    print(f"device min CIQ versions: {CIQ_VERSIONS}")
read_all_devices()

def print_error(msg):
    print(f"{COLOR_RED}{msg}{COLOR_RESET}")


def print_warn(msg):
    print(f"{COLOR_YELLOW}{msg}{COLOR_RESET}")


def camel_case(s):
    s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return ''.join([s[0].lower(), s[1:]])


def device_has_app_type(device, app_type):
    dev = DEVICES[device]
    for app_type_obj in dev['compiler']['appTypes']:
        if app_type_obj['type'] == app_type:
            return True
    return False


def parse_manifest(manifest):
    global APP_TYPE, MIN_API_LEVEL, MANIFEST_DEVICES, MANIFEST_LANGS, IS_BETA
    IS_BETA = '-prod' not in manifest
    print(f"IS_BETA: {IS_BETA}")
    tree = ET.parse(manifest)
    # root = tree.getroot()
    application = tree.find('./iq:application', NS)

    APP_TYPE = camel_case(application.get('type'))
    print(f"APP_TYPE: {APP_TYPE}")
    MIN_API_LEVEL = application.get('minApiLevel') or application.get('minSdkVersion')
    print(f"MIN_API_LEVEL: {MIN_API_LEVEL}")

    devices = []
    for product in application.findall('./iq:products/iq:product', NS):
        device = product.get('id')
        if device in ALL_DEVICES:
            devices.append(device)
        else:
            print_error(f"unknown device: {device}")
    print(f"MANIFEST_DEVICES: {devices}")
    MANIFEST_DEVICES = devices

    devices_set = set(devices)
    missing_devices = [d for d in ALL_DEVICES if d not in devices_set and device_has_app_type(d, APP_TYPE) and not d.endswith('preview')]
    if len(missing_devices) > 0:
        print_error(f"MISSING_DEVICES: {missing_devices}")

    langs = []
    for lang in application.findall('./iq:languages/iq:language', NS):
        langs.append(lang.text)
    print(f"MANIFEST_LANGS: {langs}")
    MANIFEST_LANGS = langs

FUNCTIONS = []
FEATURE_2_FUNCTION = {}

def pre_register(func):
    global FEATURE_2_FUNCTION
    feature = getattr(func, '__name__', repr(func))
    FEATURE_2_FUNCTION[feature] = func

def register(func):
    global FUNCTIONS
    FUNCTIONS.append(func)


def add(sourcePathArr, resourcePathArr, excludeAnnotationsArr, langsDict, featureArr):
    if featureArr[0] != '': sourcePathArr.append(featureArr[0])
    if featureArr[1] != '': resourcePathArr.append(featureArr[1])
    if featureArr[2] != '': excludeAnnotationsArr.append(featureArr[2])
    if len(featureArr) >= 4:
        # print(f"add: {featureArr[3]}")
        langsDict.update(featureArr[3])


def usage():
    print("Usage: monkey-generator.py [-h | --help] [-j <monkey.jungle> | --jungle=<monkey.jungle>] [-t <template> | --template=<template>] [-c | --clean] [-a | --all-devices]")


MEMORY_SIZES = {16384, 32768, 49152, 65536, 98304, 114688, 131072, 135168, 262144, 524288, 786432, 1048576, 1310720, 2359296}
# MEMORY_2_K = {16384: '16K', 32768: '32K', 65536: '64K', 131072: '128K', 262144: '256K'}
MEMORY_2_K = {}
K_2_MEMORY = {}
# for limit in MEMORY_2_K:
#     k = MEMORY_2_K[limit]
#     K_2_MEMORY[k] = limit
for limit in MEMORY_SIZES:
    k = f"{int(limit / 1024)}K"
    MEMORY_2_K[limit] = k
    K_2_MEMORY[k] = limit
MEMORY_ORDER = sorted(list(MEMORY_2_K))
print(f"MEMORY_ORDER: {MEMORY_ORDER}")
print(f"K_2_MEMORY: {K_2_MEMORY}")

FEATURES_BY_MEMORY = {}
FEATURE_ATTRIBUTES = ['min_ciq', 'max_ciq', 'min_color_depth', 'is_beta']
FEATURE_CONSTRAINS = {}
USED_CIQ_VERSIONS = []


def main(argv):
    global MONKEY_JUNGLE, TEMPLATE, MANIFEST, CIQ_VERSIONS, USED_CIQ_VERSIONS, FEATURES_BY_MEMORY, FEATURE_CONSTRAINS
    generate_devices = 'manifest'

    try:
        opts, args = getopt.getopt(argv, 'hj:t:ca', ['help', 'jungle', 'template', 'clean', 'all-devices'])
    except getopt.GetoptError as e:
        print(e)
        usage()
        sys.exit(1)
    for opt, arg in opts:
        if opt == '-h' or opt == '--help':
            usage()
            sys.exit(0)
        if opt == '-j' or opt == '--jungle':
            MONKEY_JUNGLE = arg
            TEMPLATE = MONKEY_JUNGLE.replace('.jungle', '.template.jungle')
        if opt == '-t' or opt == '--template':
            TEMPLATE = arg
        if opt == '-c' or opt == '--clean':
            shutil.rmtree(SOURCE_DEVICES_DIR)
            sys.exit(0)
        if opt == '-a' or opt == '--all-devices':
            generate_devices = 'all'

    with open(MONKEY_JUNGLE, 'w') as output:
        output.write(f"# GENERATED from {TEMPLATE} by {GENERATROR_SIGNATURE}\n\n");

        with open(TEMPLATE, 'r') as template:
            for line in template:
                output.write(line)
                line = line.strip()
                # print(f"{line}")
                if line.startswith('project.manifest'):
                    MANIFEST = line.split('=', 2)[1].strip().split(' ', 1)[0]
                    print("MANIFEST: " + MANIFEST)
                elif line.startswith('monkey_generator_features_memoryCommon'):
                    memory_str, features_str = line.split('=', 2)
                    features = features_str.strip().split(';')
                    FEATURES_BY_MEMORY['common'] = features
                elif line.startswith('monkey_generator_features_memory'):
                    memory_str, features_str = line.split('=', 2)
                    memory = memory_str.replace('monkey_generator_features_memory', '').strip()
                    features = features_str.strip().split(';')
                    FEATURES_BY_MEMORY[memory] = features
                elif line.startswith('monkey_generator_feature_'):
                    feature_str, value = line.split('=', 2)
                    feature_data = feature_str.strip().replace('monkey_generator_feature_', '')
                    for data in FEATURE_ATTRIBUTES:
                        if feature_data.endswith(data):
                            feature = feature_data.replace(f"_{data}", '')
                            if feature not in FEATURE_CONSTRAINS:
                                FEATURE_CONSTRAINS[feature] = {}
                            FEATURE_CONSTRAINS[feature][data] = value.strip()
                elif line.startswith('monkey_generator_used_ciq_versions'):
                    used_ciq_versions = line.split('=', 2)[1].strip().split(';')
                    #  .split(' ', 1)[0]
                    used_ciq_versions = sorted(used_ciq_versions, key=natural_sort_key)
                    print("used_ciq_versions: " + str(used_ciq_versions))
                    USED_CIQ_VERSIONS = used_ciq_versions
                    ciq_versions = set(CIQ_VERSIONS)
                    ciq_versions.update(used_ciq_versions)
                    CIQ_VERSIONS = sorted(list(ciq_versions), key=natural_sort_key)
                    # print(f"CIQ versions: {CIQ_VERSIONS}")
                elif line.startswith('monkey_generator_register'):
                    register_features = line.split('=', 2)[1].strip().split(';')
                    for feature in register_features:
                        if feature in FEATURE_2_FUNCTION:
                            register(FEATURE_2_FUNCTION[feature])

        print(f"FEATURES_BY_MEMORY: {FEATURES_BY_MEMORY}")
        print(f"FEATURE_CONSTRAINS: {FEATURE_CONSTRAINS}")

        parse_manifest(MANIFEST)

        output.write("\n# GENERATED #\n\n");

        # print(f"{MONKEY_JUNGLE}")
        devices = ALL_DEVICES if generate_devices == 'all' else MANIFEST_DEVICES
        devices.insert(0, 'base')
        print(f"devices ({generate_devices}): {devices}")
        for dev in devices:
            # sourcePathArr = ['source']
            sourcePathArr = []
            # resourcePathArr = ['resources']
            resourcePathArr = []
            excludeAnnotationsArr = []
            langsDict = {}

            # print(f"{dev}.add")
            # add(sourcePathArr, resourcePathArr, excludeAnnotationsArr, number_font(device))
            for func in FUNCTIONS:
                # print(f"{dev}.add: {func}")
                add(sourcePathArr, resourcePathArr, excludeAnnotationsArr, langsDict, func(dev))

            if langsDict and 'eng' in langsDict:
                resourcePathArr.append(';'.join(langsDict['eng']))

            if len(sourcePathArr) > 0: output.write(f"{dev}.sourcePath=$({dev}.sourcePath);{';'.join(sourcePathArr)}\n")
            if len(resourcePathArr) > 0: output.write(f"{dev}.resourcePath=$({dev}.resourcePath);{';'.join(resourcePathArr)}\n")
            if len(excludeAnnotationsArr) > 0: output.write(f"{dev}.excludeAnnotations=$({dev}.excludeAnnotations);{';'.join(excludeAnnotationsArr)}\n")
            if langsDict:
                for lang in langsDict:
                    # print(f"{dev}: {lang} = {langsDict[lang]}")
                    # if lang == 'eng':
                    #     output.write(f"{dev}.lang.DEFAULT=$({dev}.lang.DEFAULT);{';'.join(langsDict[lang])}\n")
                    output.write(f"{dev}.lang.{lang}=$({dev}.lang.{lang});{';'.join(langsDict[lang])}\n")


def languages(dev):
    if dev == 'base':
        return ['', '', '']
    device = DEVICES[dev]
    hebrewExcludeAnnotation = 'no_hebrew' if 'heb' in device['languages'] else 'hebrew'
    return ['', '', hebrewExcludeAnnotation]
pre_register(languages)

NO_SPACE_IN_NUMBER_FONT=['edge130','edge130plus','edge_520','edge520plus','edge530','edge820','edge830','edge_1000','edge1030','edge1030bontrager','edge1030plus','edgeexplore', 'fr735xt', 'oregon7xx', 'vivoactive_hr']
def number_font(dev):
    return [has_directory('source-features/number_font/' + ('no_space' if dev in NO_SPACE_IN_NUMBER_FONT else 'has_space')), '', ''] if dev != 'base' else ['', '', '']
pre_register(number_font)

def get_color_depth(device):
    return device['compiler']['bitsPerPixel'];

def color_depth(dev):
    if dev == 'base':
        return ['', '', '']
    device = DEVICES[dev]
    colorDepth = device['compiler']['bitsPerPixel'];
    return [has_directory(f"source-features/color_depth/{colorDepth}bpp"), '', 'color' if colorDepth == 1 else 'no_color']
pre_register(color_depth)

def device_field2hash(device, field):
    display_location = device['simulator']['display']['location']
    # width_bits = math.ceil(math.log2(display_location['width']))
    # height_bits = math.ceil(math.log2(display_location['height']))

    # field_name = f"\"{layout_name}\"[{field_idx}]"
    l = field['location']
    obs = sorted(field['obscurity'])
    # o = ''
    obscurity_flags = 0
    for side in obs:
        # o += side[0]
        obscurity_flags |= OBSCURITY_TO_NUMBER[side]
    if l['height'] >= 1000:
        sys.exit(f"{dev}: need to fix the hash, because 1000 <= height = {l['height']}")
    # hash = (((l['width'] << height_bits) | l['height']) << 4) | obscurity_flags
    hash = (l['width'] * 1000 + l['height']) * 100 + obscurity_flags
    # key = f"{hash}:{l['width']}:{l['height']}:{obscurity_flags}:{o}"
    # comment = f"{l['width']}x{l['height']}@{o}"
    return hash


# def datafield2hash_mc():
    # display_location = device['simulator']['display']['location']
    # width_bits = math.ceil(math.log2(display_location['width']))
    # height_bits = math.ceil(math.log2(display_location['height']))
    # hash = (((l['width'] << height_bits) | l['height']) << 4) | obscurity_flags
    # "function datafield2hash(dc as Graphics.Dc) as Dictionary \{\n"\
        # f"   return (((width << {height_bits}) | height) << 4) | obscurityFlags;\n"\
    # return \
    #     "(:inline)\n"\
    #     "function datafield2hash(width as Number, height as Number, obscurityFlags as DataField.Obscurity) as Number {\n"\
    #     f"   return (width * 1000 + height) * 100 + obscurityFlags;\n"\
    #     "}\n"\
    #     "(:inline)\n"\
    #     "function datafield_hash2dict(width as Number, height as Number, obscurityFlags as DataField.Obscurity) as Dictionary? {\n"\
    #     f"   return DATAFIELD_HASH_2_DICT[datafield2hash(width, height, obscurityFlags)] as Dictionary?;\n"\
    #     "}\n"\
    #     "(:inline)\n"\
    #     "function datafield_label_font(width as Number, height as Number, obscurityFlags as DataField.Obscurity) as Graphics.FontDefinition? {\n"\
    #     f"   var dict = DATAFIELD_HASH_2_DICT[datafield2hash(width, height, obscurityFlags)];\n"\
    #     f"   return dict == null ? null : dict[:label_font] as Graphics.FontDefinition?;\n"\
    #     "}\n"
        # "(:datafield_hash, :inline)\n"\
        # "function datafield_hash2dict(width as Number, height as Number, obscurityFlags as DataField.Obscurity) as Array? {\n"\
        # f"   return DATAFIELD_HASH_2_LABEL_FONT[datafield2hash(width, height, obscurityFlags)] as Array?;\n"\
        # "}\n"\
        # "(:datafield_hash, :inline)\n"\
        # "function datafield_label_font(width as Number, height as Number, obscurityFlags as DataField.Obscurity) as Graphics.FontDefinition? {\n"\
        # f"  var dict = DATAFIELD_HASH_2_LABEL_FONT;\n"\
        # f"  var hash = datafield2hash(width, height, obscurityFlags);\n"\
        # f"  return dict.hasKey(hash) ? dict[hash] as Graphics.FontDefinition? : DEFAULT_LABEL_FONT;\n"\
        # "}\n"\
        # "(:datafield_hash, :inline)\n"\
        # "function datafield_label_x(width as Number, height as Number, obscurityFlags as DataField.Obscurity) as Number {\n"\
        # f"  var dict = DATAFIELD_HASH_2_LABEL_X;\n"\
        # f"  var hash = datafield2hash(width, height, obscurityFlags);\n"\
        # f"  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_LABEL_X;\n"\
        # "}\n"\
        # "(:datafield_hash, :inline)\n"\
        # "function datafield_label_y(width as Number, height as Number, obscurityFlags as DataField.Obscurity) as Number {\n"\
        # f"  var dict = DATAFIELD_HASH_2_LABEL_Y;\n"\
        # f"  var hash = datafield2hash(width, height, obscurityFlags);\n"\
        # f"  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_LABEL_Y;\n"\
        # "}\n"
        # "(:datafield_hash, :inline)\n"\
        # "function datafield_data_font(hash as Number) as Graphics.FontDefinition? {\n"\
        # f"  var dict = DATAFIELD_HASH_2_DATA_FONT;\n"\
        # f"  return dict.hasKey(hash) ? dict[hash] as Graphics.FontDefinition? : DEFAULT_DATA_FONT;\n"\
        # "}\n"\
    # return \
    #     "(:datafield_hash, :inline)\n"\
    #     "function datafield_hash(width as Number, height as Number, obscurityFlags as DataField.Obscurity) as Number {\n"\
    #     "  return (width * 1000 + height) * 100 + obscurityFlags;\n"\
    #     "}\n"\
    #     "(:datafield_hash, :datafield_label_font, :inline)\n"\
    #     "function datafield_label_font(hash as Number) as Graphics.FontDefinition? {\n"\
    #     "  var dict = DATAFIELD_HASH_2_LABEL_FONT;\n"\
    #     "  return dict.hasKey(hash) ? dict[hash] as Graphics.FontDefinition? : DEFAULT_LABEL_FONT;\n"\
    #     "}\n"\
    #     "(:datafield_hash, :datafield_label_x, :inline)\n"\
    #     "function datafield_label_x(hash as Number) as Number {\n"\
    #     "  var dict = DATAFIELD_HASH_2_LABEL_X;\n"\
    #     "  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_LABEL_X;\n"\
    #     "}\n"\
    #     "(:datafield_hash, :datafield_label_y, :inline)\n"\
    #     "function datafield_label_y(hash as Number) as Number {\n"\
    #     "  var dict = DATAFIELD_HASH_2_LABEL_Y;\n"\
    #     "  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_LABEL_Y;\n"\
    #     "}\n"\
    #     "(:datafield_hash, :datafield_data_x, :inline)\n"\
    #     "function datafield_data_x(hash as Number) as Number {\n"\
    #     "  var dict = DATAFIELD_HASH_2_DATA_X;\n"\
    #     "  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_DATA_X;\n"\
    #     "}\n"\
    #     "(:datafield_hash, :datafield_data_y, :inline)\n"\
    #     "function datafield_data_y(hash as Number) as Number {\n"\
    #     "  var dict = DATAFIELD_HASH_2_DATA_Y;\n"\
    #     "  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_DATA_Y;\n"\
    #     "}\n"


FONT_ORDER = ['-', 'xtiny', 'simExtNumber6', 'tiny', 'simExtNumber2', 'small', 'medium', 'simExtNumber1', 'large', 'numberMild', 'numberMedium', 'numberHot',
        'simExtNumber3', 'numberThaiHot', 'simExtNumber4', 'simExtNumber5']
def font_order(font):
    return FONT_ORDER.index(font)

FONT_TO_MC_FONT = {'-': '', 'xtiny': 'XTINY', 'tiny': 'TINY', 'small': 'SMALL', 'medium': 'MEDIUM', 'large': 'LARGE',
        'numberMild': 'NUMBER_MILD', 'numberMedium': 'NUMBER_MEDIUM', 'numberHot': 'NUMBER_HOT', 'numberThaiHot': 'NUMBER_THAI_HOT',
        'simExtNumber1': {'edgeexplore2': 'MEDIUM', 'venusq2': 'XTINY', 'venusq2m': 'XTINY'},
        'simExtNumber2': {'legacyherocaptainmarvel': 'TINY', 'legacyherofirstavenger': 'TINY', 'legacysagadarthvader': 'TINY', 'legacysagarey': 'TINY',
                'vivoactive4': 'TINY', 'vivoactive4s': 'TINY'},
        'simExtNumber5': {'edge540': 'MEDIUM', 'edge840': 'MEDIUM'},
        'simExtNumber6': {'approachs62': 'XTINY', 'edge540': 'SMALL', 'edge840': 'SMALL'}
}
def font2mc_font(font, dev):
    # return f"Graphics.FONT_{font.upper()}" if font not in FONT_TO_MC_FONT else\
    #     (f"Graphics.FONT_{FONT_TO_MC_FONT[font]}" if FONT_TO_MC_FONT[font] != '' else 'null')
    if font in FONT_TO_MC_FONT:
        if type(FONT_TO_MC_FONT[font]) == str:
            if FONT_TO_MC_FONT[font] == '':
                return 'null'
            else:
                return f"Graphics.FONT_{FONT_TO_MC_FONT[font]}"
        elif type(FONT_TO_MC_FONT[font]) == dict and dev in FONT_TO_MC_FONT[font]:
            return f"Graphics.FONT_{FONT_TO_MC_FONT[font][dev]}"
        else:
            print_error(f"missing font: {font} for {dev}")
            return f"Graphics.FONT_{font.upper()}"
    else:
        print_error(f"missing font: {font} for {dev}")
        return f"Graphics.FONT_{font.upper()}"
    # return if font in FONT_TO_MC_FONT and FONT_TO_MC_FONT[font] != ''
    # return 'Graphics.FONT_' + (FONT_TO_MC_FONT[font] if font in FONT_TO_MC_FONT else font.upper())

def get_most_frequent_value(dict):
    usages = {}
    for val in dict.values():
        if val not in usages:
            usages[val] = 0
        usages[val] += 1
    arr = []
    for key, val in usages.items():
        arr.append([val, key])
    arr.sort(reverse = True)
    return arr[0][1]

def get_only_value(dict):
    values = set(dict.values())
    return next(iter(values)) if len(values) == 1 else None

JUSTIFICATION_TO_MC = {'right': 'TEXT_JUSTIFY_RIGHT', 'center': 'TEXT_JUSTIFY_CENTER', 'left': 'TEXT_JUSTIFY_LEFT', 'vcenter': 'TEXT_JUSTIFY_VCENTER'}
def justification2mc(justification):
    if justification is None:
        return 'null'
    mc_just = JUSTIFICATION_TO_MC[justification]
    if mc_just is None:
        warnings.warn(f"Unknown justification: {justification}")
    return f"Graphics.{mc_just}"

OBSCURITY_TO_NUMBER = {'left': 1, 'top': 2, 'right': 4, 'bottom': 8}
def label_font(dev):
    if dev == 'base':
        # device_dir = f"{SOURCE_DEVICES_DIR}/_common"
        # device_file = f"{device_dir}/label_font.mc"
        # print(device_file)
        # os.makedirs(device_dir, 0o755, True)
        # with open(device_file, 'w') as output:
        #     output.write(f"// GENERATED common by {GENERATROR_SIGNATURE}\n\n");
        #     output.write("import Toybox.Lang;\n")
        #     output.write("import Toybox.Graphics;\n")
        #     output.write("import Toybox.WatchUi;\n")
        #     output.write(datafield2hash_mc() + '\n')
        return ['', '', '']

    device = DEVICES[dev]
    if 'layouts' not in device['simulator']:
        print(f"{dev}: no layouts")
        return ['', '', '']

    # print(device)
    default_label_font = ''
    default_label_justification = ''
    default_label_x = 0
    default_label_y = 0
    # default_data_font = ''
    default_data_justification = ''
    default_data_x = 0
    default_data_y = 0
    # fields = {}
    font2field = {}
    hash2label_font = {}
    hash2label_justification = {}
    hash2label_x = {}
    hash2label_y = {}
    # hash2data_font = {}
    hash2data_justification = {}
    hash2data_x = {}
    hash2data_y = {}
    hash2comment = {}
    key2fonts = {}
    display_location = device['simulator']['display']['location']
    # width_bits = math.ceil(math.log2(display_location['width']))
    height_bits = math.ceil(math.log2(display_location['height']))
    # print(f"w:{display_location['width']}:{width_bits}, h:{display_location['height']}:{height_bits}")
    for layout in device['simulator']['layouts']:
        for datafield in layout['datafields']['datafields']:
            layout_name = datafield['name']
            field_idx = 0
            field = '' # here to be able to capture field in except:
            try:
                for field_idx, field in enumerate(datafield['fields']):
                    field_name = f"\"{layout_name}\"[{field_idx}]"
                    location = field['location']
                    obs = sorted(field['obscurity'])
                    o = ''
                    obscurity_flags = 0
                    for side in obs:
                        o += side[0]
                        obscurity_flags |= OBSCURITY_TO_NUMBER[side]
                    # hash = (((location['width'] << height_bits) | location['height']) << 4) | obscurity_flags
                    hash = device_field2hash(device, field)
                    key = f"{hash}:{location['width']}:{location['height']}:{obscurity_flags}:{o}"
                    comment = f"{location['width']}x{location['height']}@{o}"
                    hash2comment[hash] = comment
                    data = field['data']
                    data_font = data['font']
                    hash2data_justification[hash] = data['justification']
                    hash2data_x[hash] = data['x']
                    hash2data_y[hash] = data['y']
                    # hash2data_font[hash] = data['font']
                    if field['labelDisabled']:
                        label_font = '-'
                        # print(f"{dev}: disabled label: {field_name}: {field}")
                    else:
                        label = field['label']
                        label_font = label['font']
                        hash2label_justification[hash] = label['justification']
                        hash2label_x[hash] = label['x']
                        hash2label_y[hash] = label['y']
                    if label_font not in font2field:
                        font2field[label_font] = []
                    hash2label_font[hash] = label_font
                    font2field[label_font].append(field_name)
                    # print(f"{dev}: default_label_font:{default_label_font}, label_font:{label_font}")
                    if default_label_font == '':
                        default_label_font = label_font
                    elif default_label_font != label_font:
                        if default_label_font == '-':
                            default_label_font = label_font
                    # if default_label_justification == '':
                    #     default_label_justification = label['justification']
                        # # sys.exit(f"{dev}: multiple label fonts: {default_label_font} != {label_font}")
                        # ## print(f"{COLOR_RED}{dev}: multiple label fonts: {default_label_font} != {label_font}{COLOR_RESET}")
                        # if layout_name not in fields:
                        #     fields[layout_name] = {-1: default_label_font}
                        #     ## print(f"added: fields[{layout_name}] = {fields[layout_name]}")
                        # fields[layout_name][field_idx] = label_font
                        # # print(f"fields[{layout_name}]: {fields[layout_name]}; field_idx: {field_idx}")

                    if key in key2fonts:
                        if key2fonts[key][0] == label_font:
                            key2fonts[key][1].append(field_name)
                        else:
                            print_warn(f"{dev}: conflicting key: {key}: {key2fonts[key]} vs [{label_font}] ({field_name})")
                    else:
                        key2fonts[key] = [label_font, [field_name]]
                    # print(f"{dev}:{key}:{label_font} ({field_name})")
            except Exception as e:
                sys.exit(f"{COLOR_RED}Error: {dev}: {e=} in {field_name}: {field}{COLOR_RESET}")
    # print(f"{dev}: {key2fonts}")

    # get the label_font that is used in most fields to save memory. The only device where this is different: vivoactive_hr: xtiny => small
    default_label_font = get_most_frequent_value(hash2label_font)

    increase_hebrew_label_font = False
    if 'heb' in device['languages']:
        fontSet = None
        # print(f"{dev}::")
        for partNumber in device['compiler']['partNumbers']:
            lng = list(filter(lambda lang: lang['code'] == 'heb', partNumber['languages']))
            # print(f"{dev}: {partNumber['number']} {lng}")
            if len(lng) > 0:
                lang = lng[0]
                fontSet = lang['fontSet']
                default_label_font_font = next(font for font in next(fonts for fonts in device['simulator']['fonts'] if fonts['fontSet'] == fontSet)['fonts'] if font['name'] == default_label_font)
                increase_hebrew_label_font = '_CDPG_ROBOTO_13B' in default_label_font_font['filename']
        # print(f"{dev}: {default_label_font_font['filename']}, increase_hebrew_label_font: {increase_hebrew_label_font}")

    # if len(font2field) > 1:
    #     # sys.exit(f"{dev}: multiple label fonts: {fonts}");
    #     fonts = list(font2field.keys())
    #     fonts.sort(key=font_order)
    #     f2f = {}
    #     for label_font in fonts:
    #         f2f[label_font] = font2field[label_font]
    #     # print_warn(f"{dev}: multiple label fonts: {f2f}");
    #     old_label_font = fonts[0] if fonts[0] != '-' else fonts[1]
    #     if default_label_font != old_label_font: # the only device where this is different: vivoactive_hr: xtiny => small
    #         print(f"{dev}: different: {old_label_font} => {default_label_font}")

    # default_label_justification = get_only_value(hash2label_justification)
    # print(f"{dev}: {default_label_font} {mc_font} {hash2label_font} {default_label_justification}")
    # if default_label_justification is None:
    #     print(f"{dev}: {default_label_font} {default_label_justification}")
    default_label_x = get_most_frequent_value(hash2label_x)
    default_label_y = get_most_frequent_value(hash2label_y)
    default_label_justification = get_most_frequent_value(hash2label_justification)

    default_data_x = get_most_frequent_value(hash2data_x)
    default_data_y = get_most_frequent_value(hash2data_y)
    default_data_justification = get_most_frequent_value(hash2data_justification)

    device_dir = f"{SOURCE_DEVICES_DIR}/{dev}"
    device_file = f"{device_dir}/label_font.mc"
    os.makedirs(device_dir, 0o755, True)
    with open(device_file, 'w') as output:
        output.write(f"// GENERATED for {dev} by {GENERATROR_SIGNATURE}\n\n");
        output.write("import Toybox.Lang;\n")
        output.write("import Toybox.Graphics;\n\n")

        if 'heb' in device['languages']:
            output.write(f"(:datafield, :hebrew) const INCREASE_HEBREW_LABEL_FONT_SIZE = {'true' if increase_hebrew_label_font else 'false'};\n")
        output.write(f"(:datafield) const DEFAULT_LABEL_FONT = {font2mc_font(default_label_font, dev)};\n")
        output.write("(:datafield, :datafield_hash, :datafield_label_font) const DATAFIELD_HASH_2_LABEL_FONT = {\n")
        # for hash, label_font in hash2label_font.items():
        for hash in sorted(hash2label_font):
            label_font = hash2label_font[hash]
            if label_font != default_label_font:
                output.write(f"  {hash} /*{hash2comment[hash]}*/ => {font2mc_font(label_font, dev)},\n")
        output.write("} as Dictionary<Number, Graphics.FontDefinition?>;\n\n")

        loc = locals()
        for field_part in ['label', 'data']:
            CAPITAL = field_part.upper()
            # print(f"field_part: {field_part}, CAPITAL: {CAPITAL}, loc: {loc}, default_x: {default_x}")

            # print(f"{loc[f"default_{field_part}_x"]}")
            default_x = loc[f"default_{field_part}_x"]
            output.write(f"(:datafield, :datafield_hash, :datafield_{field_part}_x) const DEFAULT_{CAPITAL}_X = {default_x};\n")
            output.write(f"(:datafield, :datafield_hash, :datafield_{field_part}_x) const DATAFIELD_HASH_2_{CAPITAL}_X = {{\n")
            # for hash, x in loc[f"hash2{field_part}_x"].items():
            for hash in sorted(loc[f"hash2{field_part}_x"]):
                x = loc[f"hash2{field_part}_x"][hash]
                if x != loc[f"default_{field_part}_x"]:
                    output.write(f"  {hash} /*{hash2comment[hash]}*/ => {x},\n")
            output.write("} as Dictionary<Number, Number>;\n\n")

            default_y = loc[f"default_{field_part}_y"]
            output.write(f"(:datafield, :datafield_hash, :datafield_{field_part}_y) const DEFAULT_{CAPITAL}_Y = {default_y};\n")
            output.write(f"(:datafield, :datafield_hash, :datafield_{field_part}_y) const DATAFIELD_HASH_2_{CAPITAL}_Y = {{\n")
            # for hash, y in loc[f"hash2{field_part}_y"].items():
            for hash in sorted(loc[f"hash2{field_part}_y"]):
                y = loc[f"hash2{field_part}_y"][hash]
                if y != loc[f"default_{field_part}_y"]:
                    output.write(f"  {hash} /*{hash2comment[hash]}*/ => {y},\n")
            output.write("} as Dictionary<Number, Number>;\n\n")

            output.write(f"(:datafield, :datafield_hash, :datafield_{field_part}_justification) const DEFAULT_{CAPITAL}_JUSTIFICATION = {justification2mc(loc[f'default_{field_part}_justification'])};\n")
            if get_only_value(loc[f"hash2{field_part}_justification"]) is None:
                # print(f"{dev}: DATAFIELD_HASH_2_LABEL_JUSTIFICATION")
                output.write(f"(:datafield, :datafield_hash, :datafield_{field_part}_justification) const DATAFIELD_HASH_2_{CAPITAL}_JUSTIFICATION = {{\n")
                # for hash, j in loc[f"hash2{field_part}_justification"].items():
                for hash in sorted(loc[f"hash2{field_part}_justification"]):
                    j = loc[f"hash2{field_part}_justification"][hash]
                    if j != loc[f"default_{field_part}_justification"]:
                        output.write(f"  {hash} /*{hash2comment[hash]}*/ => {justification2mc(j)},\n")
                output.write("} as Dictionary<Number, Number>;\n\n")
                output.write(f"(:datafield, :datafield_hash, :datafield_{field_part}_justification, :inline)\n"\
                    f"function datafield_{field_part}_justification(hash as Number) as Number {{\n"\
                    f"  var dict = DATAFIELD_HASH_2_{CAPITAL}_JUSTIFICATION;\n"\
                    f"  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_{CAPITAL}_JUSTIFICATION;\n"\
                    "}\n\n")
            else:
                output.write(f"(:datafield, :datafield_hash, :datafield_{field_part}_justification, :inline)\n"\
                    f"function datafield_{field_part}_justification(hash as Number) as Number {{\n"\
                    f"  return DEFAULT_{CAPITAL}_JUSTIFICATION;\n"\
                    "}\n\n")


        # output.write("(:datafield_hash)\n")
        # output.write("const DATAFIELD_HASH_2_DICT = {\n")
        # for hash, label_font in hash2label_font.items():
        #     output.write(f" {hash} /*{hash2comment[hash]}*/ => {{\n")
        #     output.write(f"     :label_font => {font2mc_font(label_font, dev)},\n")
        #     output.write("  },\n")
        # output.write("} as Dictionary<Number, Dictionary<Symbol, Graphics.FontDefinition?>>;\n")

    # return default_label_font
    sourceDirs = list(filter(None, [has_directory('source-features/common'), has_directory(f"{SOURCE_DEVICES_DIR}/{dev}")]))
    return [';'.join(sourceDirs), '', '']
pre_register(label_font)


def memory_annotations(dev):
    if dev == 'base':
        return ['', '', '']
    device = DEVICES[dev]
    source_path_arr = []
    resource_path_arr = []
    exclude_annotations_arr = []
    langs = {}
    if APP_TYPE not in device['memory']:
        sys.exit(f"{dev}: no app-type: {APP_TYPE}")
    memory_limit = device['memory'][APP_TYPE]
    memory_k = MEMORY_2_K[memory_limit]
    if memory_k is None:
        sys.exit(f"{dev}: Unknown memory limit: {APP_TYPE}: {memory_limit}")
    for memory in MEMORY_ORDER:
        memory_k = MEMORY_2_K[memory]
        if memory < memory_limit:
            exclude_annotations_arr.append(f"memory{memory_k}minus")
            exclude_annotations_arr.append(f"memory{memory_k}")
        if memory == memory_limit:
            exclude_annotations_arr.append(f"memory{memory_k}minus")
        if memory > memory_limit:
            exclude_annotations_arr.append(f"memory{memory_k}")
            exclude_annotations_arr.append(f"memory{memory_k}plus")
    return ['', '', ';'.join(exclude_annotations_arr)]
pre_register(memory_annotations)


def ciq_api(dev):
    # global CIQ_VERSIONS
    if dev == 'base':
        return ['', '', '']
    device = DEVICES[dev]
    minVersion = device['minVersion']
    annotations = []
    has_api = True
    for ver in CIQ_VERSIONS:
        if ver in USED_CIQ_VERSIONS:
            api = ('no_' if has_api else '') + 'ciq_' + ver.replace('.', '_')
            annotations.append(api)
        if ver == minVersion:
            has_api = False
    # print(f"{dev}: {minVersion} => {annotations}")
    return ['', '', ';'.join(annotations)]
pre_register(ciq_api)

def features_by_memory(memory_limit):
    memory_idx = MEMORY_ORDER.index(memory_limit)
    if memory_idx is None:
        sys.exit(f"Unknown memory limit: {memory_limit}")
    while memory_idx >= 0:
        memory = MEMORY_ORDER[memory_idx]
        memory_k = MEMORY_2_K[memory]
        if memory_k is None:
            sys.exit(f"Unknown memory size: {memory}")
        if memory_k in FEATURES_BY_MEMORY:
            break
        memory_idx -= 1
    # print(f"MEMORY_ORDER: {MEMORY_ORDER}, MEMORY_2_K: {MEMORY_2_K}, FEATURES_BY_MEMORY: {FEATURES_BY_MEMORY}, memory_k: {memory_k}")
    common_features = FEATURES_BY_MEMORY['common'] if 'common' in FEATURES_BY_MEMORY else []
    memory_features = FEATURES_BY_MEMORY[memory_k] if memory_k in FEATURES_BY_MEMORY else []
    return common_features + memory_features

def has_directory(dir):
    return dir if os.path.isdir(dir) else ''
    # return dir.replace('+', '\+') if os.path.isdir(dir) else ''

def versiontuple(v):
    return tuple(map(int, (v.split("."))))


def get_multi_feature_dirs(dev, features_dir, base_dir, features):
    base_dir_path = f"{features_dir}{base_dir}"
    multi_feature_dirs = sorted(filter(lambda dir: MULTI_FEATURE_DIR_SEPARATOR in dir, os.listdir(base_dir_path))) if os.path.isdir(base_dir_path) else []
    # print(f"{dev}: multi_feature_dirs in {base_dir_path}: {multi_feature_dirs}")

    # multi_features = {}
    # for multi_feature_dir in multi_feature_dirs:
    #     dir_features = multi_feature_dir.split(MULTI_FEATURE_DIR_SEPARATOR)
    #     if dir_features[0] not in multi_features:
    #         multi_features[dir_features[0]] = set()
    #     multi_features[dir_features[0]].update(dir_features)
    #     # multi_features[dir_features[0]].remove(dir_features[0])

    add_feature_and_ = {}
    # potential_multi_feature_dirs = {}
    multi_dirs = []
    for multi_feature_dir in multi_feature_dirs:
        dir_features = multi_feature_dir.split(MULTI_FEATURE_DIR_SEPARATOR)
        add_feature_and_[dir_features[0]] = 0
        add_dir = True
        for feature in dir_features:
            if feature == '':
                add_feature_and_[dir_features[0]] += 1
            # print(f"{dev}: checking: {feature}")
            if feature not in features:
                add_dir = False
                break
        if add_dir:
            # print(f"{dev}: adding: {multi_feature_dir}")
            # features.append(multi_feature_dir)
            # potential_multi_feature_dirs[multi_feature_dir] = dir_features
            multi_dirs.append(f"{multi_feature_dir}")
            add_feature_and_[dir_features[0]] -= 1
    for feature in add_feature_and_:
        if add_feature_and_[feature] == 1:
            print_warn(f"{dev}: adding directory: {feature}{MULTI_FEATURE_DIR_SEPARATOR}")
            # features.append(f"{feature}{MULTI_FEATURE_DIR_SEPARATOR}")
            # potential_multi_feature_dirs[f"{feature}{MULTI_FEATURE_DIR_SEPARATOR}"] = list(feature)
            multi_dirs.append(f"{feature}{MULTI_FEATURE_DIR_SEPARATOR}")
        # else:
        #     print(f"{dev}: not adding directory: {feature}{MULTI_FEATURE_DIR_SEPARATOR}")
    # print(f"{dev}: multi_dirs in {base_dir}: {multi_dirs}")
    return multi_dirs


def add_multi_feature_dirs(dev, features_dir, base_dir, features):
    multi_dirs = get_multi_feature_dirs(dev, features_dir, base_dir, features)
    for dir in multi_dirs:
        features.append(f"{base_dir}{dir}")


def add_set(dev, features_dir, set_dir, features):
    potential_multi_feature_dirs = get_multi_feature_dirs(dev, features_dir, set_dir, features)
    # potential_multi_feature_dirs = {}
    for potential_dir in potential_multi_feature_dirs:
        potential_dir_features = potential_dir.split(MULTI_FEATURE_DIR_SEPARATOR)
        # potential_dir_features = potential_multi_feature_dirs[potential_dir]
        # print(f"{dev}: {potential_dir}: {potential_dir_features}")
        potential_dir_features_set = set(potential_dir_features)
        include_potential_dir = True
        for dir in potential_multi_feature_dirs:
            if dir != potential_dir:
                # dir_features = potential_multi_feature_dirs[dir]
                dir_features = dir.split(MULTI_FEATURE_DIR_SEPARATOR)
                dir_features_set = set(dir_features)
                if len(dir_features_set - potential_dir_features_set) > 0 and len(potential_dir_features_set - dir_features_set) == 0:
                    include_potential_dir = False
        if include_potential_dir:
            # print(f"{dev}: including: {set_dir}{potential_dir}")
            features.append(f"{set_dir}{potential_dir}")
        # else:
        #     print(f"{dev}: not including: {potential_dir}")


def add_sets(dev, features_dir, base_dir, features):
    dir_path = f"{features_dir}{base_dir}"
    if os.path.isdir(dir_path):
        set_dirs = sorted(os.listdir(dir_path))
        for set_dir in set_dirs:
            add_set(dev, features_dir, f"{base_dir}{set_dir}/", features)
            # dirs = sorted(filter(lambda dir: MULTI_FEATURE_DIR_SEPARATOR in dir, os.listdir(f"{base_dir}/{set_dir}")))
            # print(f"{base_dir}/{set_dir}: dirs: {dirs}")
            # for dir in dirs:
            #     set_features = get_multi_dir_features(f"{base_dir}/{set_dir}/{dir}", features)


def features(dev):
    if dev == 'base':
        return [has_directory('features/base/source'), has_directory('features/base/resources'), 'base']
    device = DEVICES[dev]
    source_path_arr = []
    resource_path_arr = []
    exclude_annotations_arr = []
    langs = {}
    memory_limit = device['memory'][APP_TYPE]
    features = []
    # features = {}
    for feature_or_not in features_by_memory(memory_limit):
        if feature_or_not.startswith('no_'):
            feature = feature_or_not.replace('no_', '')
            has_feature = False
        else:
            feature = feature_or_not
            has_feature = True

        # if feature != 'user_zones' and feature != 'no_user_zones':
        #     continue
        # print(f"{dev}: {feature_or_not}: {feature}: {has_feature}")

        if has_feature and feature in FEATURE_CONSTRAINS:
            for attr in FEATURE_CONSTRAINS[feature]:
                val = FEATURE_CONSTRAINS[feature][attr]
                # print(f"{dev}: {feature}: {attr}: {val} => ?")
                if attr == 'min_ciq' and versiontuple(device['minVersion']) < versiontuple(val):
                    has_feature = False
                    # print(f"{dev}: {feature}: {attr}: {val} => {has_feature}")
                if attr == 'max_ciq' and versiontuple(val) <= versiontuple(device['minVersion']):
                    has_feature = False
                    # print(f"{dev}: {feature}: {attr}: {val} => {has_feature}")
                if attr == 'min_color_depth' and get_color_depth(device) < int(val):
                    has_feature = False
                    # print(f"{dev}: {feature}: {attr}: {get_color_depth(device)} < {val} => {has_feature}")
                if attr == 'is_beta' and not IS_BETA:
                    has_feature = False
        # print(f"{dev}: {feature}: => {has_feature}")
            # if has_feature:
            #     features.append(feature)
        # features[feature] = has_feature
        feature_or_not = ('' if has_feature else 'no_') + feature
        features.append(feature_or_not)

    add_multi_feature_dirs(dev, 'features/', '', features)
    add_sets(dev, 'features/', 'sets/', features)

    # print(f"{dev}: {features}")

    settings_dirs = []
    for feature_or_not in features:
        dir = has_directory(f"features/{feature_or_not}/source")
        if dir != '' and feature_or_not != 'base': source_path_arr.append(dir)
        dir = has_directory(f"features/{feature_or_not}/resources")
        if dir != '' and feature_or_not != 'base': resource_path_arr.append(dir)
        if feature_or_not != 'base' and MULTI_FEATURE_DIR_SEPARATOR not in feature_or_not:
            exclude_annotation = feature_or_not.replace('no_', '') if feature_or_not.startswith('no_') else f"no_{feature_or_not}"
            exclude_annotations_arr.append(exclude_annotation)
        for lang in MANIFEST_LANGS:
            dir = has_directory(f"features/{feature_or_not}/lang-{lang}")
            # print(f"{dev}: {feature}: {lang}, {dir}")
            if dir != '':
                if lang not in langs:
                    langs[lang] = []
                langs[lang].append(dir)
        dir = has_directory(f"features/{feature_or_not}/settings")
        if dir != '':
            settings_dirs.append(dir)

    # print(f"{dev}: settings in: {settings_dirs}")
    settings_files = {}
    for settings_dir in settings_dirs:
        for file in os.listdir(settings_dir):
            if file in settings_files:
                sys.exit(f"{dev}: multiple settings file with the same name: {settings_files[file]}/{file} and {settings_dir}/{file}")
            settings_files[file] = settings_dir
    sorted_settings_files = sorted(settings_files.keys())
    # print(f"{sorted_settings_files}")
    for file in sorted_settings_files:
        resource_path_arr.append(f"{settings_files[file]}/{file}")

    result = [';'.join(source_path_arr), ';'.join(resource_path_arr), ';'.join(exclude_annotations_arr), langs]
    # print(f"{dev}: {result}")
    return result
pre_register(features)


# def settings(dev):
#     if dev == 'base':
#         return ['', '', '']
#     device = DEVICES[dev]
#     return ['', '', '']
# pre_register(settings)


if __name__ == '__main__':
    main(sys.argv[1:])
