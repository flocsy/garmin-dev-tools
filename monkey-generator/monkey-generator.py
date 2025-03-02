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
from enum import IntEnum
from inspect import getframeinfo, stack
import uuid
# from packaging import version

LOG_LINE_NUMBER = False
LOG_LEVEL = -1
USE_MODULES = False

# def get_caller(nth_caller = 1):
#     return getframeinfo(stack()[nth_caller][0])

def log(log_level, min_level, msg, nth_caller = 1):
    if log_level < 0:
        caller = getframeinfo(stack()[nth_caller][0])
        prefix = f"{caller.filename}:{caller.lineno}: "
        print(f"{COLOR_RED}{prefix}ERROR: log_level: {log_level}{COLOR_RESET}")
    if log_level >= min_level:
        prefix = ''
        if (LOG_LINE_NUMBER):
            caller = getframeinfo(stack()[nth_caller][0])
            prefix = f"{caller.filename}:{caller.lineno}: "
        print(f"{prefix}{msg}")

LOG_LEVEL_ALWAYS = 0
LOG_LEVEL_BASIC = 1
LOG_LEVEL_OUTPUT = 2
LOG_LEVEL_PARSING = 3
LOG_LEVEL_INPUT = 4
LOG_LEVEL_DEBUG = 10

CIQ_SDK_HOME = os.environ.get('CIQ_SDK_HOME')
if not CIQ_SDK_HOME:
    CIQ_SDK_HOME = f"{os.environ.get('HOME')}/Library/Application Support/Garmin/ConnectIQ"
if not os.path.isdir(CIQ_SDK_HOME):
    sys.exit(f"Missing CIQ SDK: {CIQ_SDK_HOME}")

CSV_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/csv'
DEVICE_2_MIN_VERSION_CSV = f"{CSV_DIR}/device2min-version.csv"
if not os.path.exists(DEVICE_2_MIN_VERSION_CSV):
    sys.exit(f"Missing: {DEVICE_2_MIN_VERSION_CSV}")

FEATURES_SRC_DIR = os.path.dirname(os.path.realpath(__file__)) + '/features'
GENERATED_DIR = 'gen'
GENERATED_DEVICES_DIR = f'{GENERATED_DIR}/devices'
GENERATED_FEATURES_DIR = f'{GENERATED_DIR}/features'
SOURCE_FEATURES_DIR = 'source-features'
RESOURCES_FEATURES_DIR = 'resources-features'

MONKEY_JUNGLE = 'monkey.jungle'
TEMPLATE = MONKEY_JUNGLE.replace('.jungle', '.template.jungle')
MONKEY_GENERATOR_CONF_FILE = 'monkey-generator.conf'
MONKEY_GENERATOR_REPLACE = {}
MONKEY_GENERATOR_CONF = {}

MANIFEST='manifest.xml'

GENERATROR_SIGNATURE=f"https://github.com/flocsy/garmin-dev-tools/tree/main/monkey-generator/ ©2022-{datetime.date.today().year} by flocsy"
COLOR_RED = '\033[91m'
COLOR_YELLOW = '\033[93m'
COLOR_RESET = '\033[00m'

SDK_DEVICES_DIR = f"{CIQ_SDK_HOME}/Devices"
# ALL_DEVICES = os.listdir(f"{SDK_DEVICES_DIR}")
# ALL_DEVICES = filter(lambda d: not d.startswith('.'), os.listdir(f"{SDK_DEVICES_DIR}"))
ALL_DEVICES = [d for d in os.listdir(f"{SDK_DEVICES_DIR}") if not d.startswith('.')]

ALL_DEVICES.sort()
# log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{ALL_DEVICES}")

NS = {'iq': 'http://www.garmin.com/xml/connectiq'}

APP_TYPE = ''
MIN_API_LEVEL = '1.0.0'
MANIFEST_DEVICES = []
MISSING_DEVICES = []
MANIFEST_LANGS = []
BASE = {}
IS_BETA = False

DEVICES = {}

LANGUAGES = ["ara", "bul", "ces", "dan", "deu", "dut", "eng", "est", "fin", "fre", "gre", "heb", "hrv", "hun", "ind", "ita", "jpn", "kor", "lav", "lit", "nob", "pol", "por", "ron", "rus", "slo", "slv", "spa", "swe", "tha", "tur", "ukr", "vie", "zhs", "zht", "zsm"]
LANG_CODE3_2_LANG_CODE2 = {"ara":"ar", "bul":"bg", "ces":"cs", "dan":"da", "deu":"de", "dut":"nl", "eng":"en", "est":"et", "fin":"fi", "fre":"fr", "gre":"el", "heb":"he", "hrv":"hr", "hun":"hu", "ind":"in", "ita":"it", "jpn":"ja", "kor":"ko", "lav":"lv", "lit":"lt", "nob":"no", "pol":"pl", "por":"pt", "ron":"ro", "rus":"ru", "slo":"sk", "slv":"sl", "spa":"es", "swe":"sv", "tha":"th", "tur":"tr", "ukr":"uk", "vie":"vi", "zhs":"zh_CN", "zht":"zh_TW", "zsm":"ms", "unknown":"unknown"}
MEMORY_2_K = {}
MEMORY_ORDER = []
FEATURES_BY_MEMORY = {}
FEATURE_ATTRIBUTES = ['min_ciq', 'max_ciq', 'min_color_depth', 'is_beta', 'is', 'has', 'min_memory', 'json', 'key_behavior', 'key_id']
FEATURE_CONSTRAINS = {'beta': {'is_beta': True}}
FILTER_CONSTRAINS = {}
USED_CIQ_VERSIONS = []

OBSCURITY_TO_NUMBER = {'left': 1, 'top': 2, 'right': 4, 'bottom': 8}

DEVICE_MIN_VERSION = {}
def read_device_2_min_version_csv():
    with open(DEVICE_2_MIN_VERSION_CSV) as csv:
        for line in csv:
            dev, min_versions = line.strip().split(':')
            DEVICE_MIN_VERSION[dev] = min_versions
read_device_2_min_version_csv()

MULTI_FEATURE_DIR_SEPARATOR = '_AND_'

def print_error_log(log_level, min_level, msg, nth_caller = 2):
    log(log_level, min_level, f"{COLOR_RED}{msg}{COLOR_RESET}", nth_caller)

def print_error(msg):
    print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, msg, nth_caller = 3)

def print_warn_log(log_level, min_level, msg, nth_caller = 2):
    log(log_level, min_level, f"{COLOR_YELLOW}{msg}{COLOR_RESET}", nth_caller)

def print_warn(msg):
    print_warn_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, msg, nth_caller = 3)

def get_languages(device):
    langs = set()
    for partNumber in device['compiler']['partNumbers']:
        for lang in partNumber['languages']:
            langs.add(lang['code'])
    languages = sorted(list(langs))
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{device['dev']} languages: {languages}")
    return languages

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]

def escape_mc_string(str):
    return str.replace('\\', '\\\\').replace('"', '\\"')

CIQ_VERSIONS = set()
def get_ciq_apis(device):
    global CIQ_VERSIONS
    maxCiqVersions = set()
    for partNumber in device['compiler']['partNumbers']:
        maxCiqVersions.add(partNumber['connectIQVersion'])
    maxCiqVersions = sorted(list(maxCiqVersions), key=natural_sort_key)
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{device['dev']}: maxCiqVersions: {maxCiqVersions}")
    # CIQ_VERSIONS.update(maxCiqVersions)
    # CIQ_VERSIONS |= set(maxCiqVersions)
    return maxCiqVersions


def read_all_devices():
    global DEVICES, CIQ_VERSIONS
    for dev in ALL_DEVICES:
        device = {'dev': dev}
        with open(f"{SDK_DEVICES_DIR}/{dev}/compiler.json") as compiler_json:
            device['compiler'] = json.load(compiler_json)
        with open(f"{SDK_DEVICES_DIR}/{dev}/simulator.json") as simulator_json:
            device['simulator'] = json.load(simulator_json)
        device['languages'] = get_languages(device)
        maxCiqVersions = get_ciq_apis(device)
        CIQ_VERSIONS.update(maxCiqVersions)
        device['minVersion'] = maxCiqVersions[0]
        if DEVICE_MIN_VERSION[dev] < maxCiqVersions[0]:
            log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: compiler: {maxCiqVersions[0]} > csv: {DEVICE_MIN_VERSION[dev]}")
            DEVICE_MIN_VERSION[dev] = maxCiqVersions[0]
        else:
            log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: compiler: {maxCiqVersions[0]}, csv: {DEVICE_MIN_VERSION[dev]}")
        device['minVersion'] = DEVICE_MIN_VERSION[dev]
        if device['minVersion'] is None:
            print_error(f"{dev}: missing from DEVICE_MIN_VERSION")
        device['memory'] = {}
        for app_type in device['compiler']['appTypes']:
            device['memory'][app_type['type']] = app_type['memoryLimit']
        # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {device['memory']}")
        DEVICES[dev] = device
        # log(LOG_LEVEL, LOG_LEVEL_BASIC, device)
    CIQ_VERSIONS = sorted(list(set(DEVICE_MIN_VERSION.values())), key=natural_sort_key)
    log(LOG_LEVEL, LOG_LEVEL_BASIC, f"device min CIQ versions: {CIQ_VERSIONS}")


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
    global APP_TYPE, MIN_API_LEVEL, MANIFEST_DEVICES, MANIFEST_LANGS, IS_BETA, MISSING_DEVICES
    IS_BETA = '-prod' not in manifest and ('ENV' not in MONKEY_GENERATOR_REPLACE or MONKEY_GENERATOR_REPLACE['ENV'] == 'beta')
    log(LOG_LEVEL, LOG_LEVEL_BASIC, f"IS_BETA: {IS_BETA}")
    tree = ET.parse(manifest)
    # root = tree.getroot()
    root = tree.find('./iq:application', NS)
    if root is not None:
        APP_TYPE = camel_case(root.get('type'))
    else:
        root = tree.find('./iq:barrel', NS)
        if root:
            APP_TYPE = 'Barrel'
    log(LOG_LEVEL, LOG_LEVEL_BASIC, f"APP_TYPE: {APP_TYPE}")
    MIN_API_LEVEL = root.get('minApiLevel') or root.get('minSdkVersion')
    log(LOG_LEVEL, LOG_LEVEL_BASIC, f"MIN_API_LEVEL: {MIN_API_LEVEL}")

    devices = []
    for product in root.findall('./iq:products/iq:product', NS):
        device = product.get('id')
        if device in ALL_DEVICES:
            devices.append(device)
        else:
            print_error(f"unknown device: {device}")
    MANIFEST_DEVICES = devices
    log(LOG_LEVEL, LOG_LEVEL_BASIC, f"MANIFEST_DEVICES: {MANIFEST_DEVICES}")

    devices_set = set(devices)
    missing_devices = [d for d in ALL_DEVICES if d not in devices_set \
        and device_has_app_type(d, APP_TYPE) \
        and not d.endswith('preview') \
        and DEVICE_MIN_VERSION[d] >= MIN_API_LEVEL \
        and not has_feature_by_constraints(d, FILTER_CONSTRAINS)[False] ]
    if len(missing_devices) > 0:
        MISSING_DEVICES = missing_devices
        # print_error(f"MISSING_DEVICES: {missing_devices}")

    langs = []
    for lang in root.findall('./iq:languages/iq:language', NS):
        langs.append(lang.text)
    log(LOG_LEVEL, LOG_LEVEL_BASIC, f"MANIFEST_LANGS: {langs}")
    MANIFEST_LANGS = langs

FUNCTIONS = []
FEATURE_2_DEPENDENCIES = {}
FEATURE_2_FUNCTION = {}
FEATURE_2_GEN_SUB_DIR = {}
FEATURE_2_REGISTER_VALIDATION_FUNCTION = {}
CONSTS = {}

def pre_register(func, gen_sub_dir = None, validation_func = None, dependencies = []):
    # global FEATURE_2_FUNCTION
    feature = getattr(func, '__name__', repr(func))
    FEATURE_2_FUNCTION[feature] = func
    if gen_sub_dir:
        FEATURE_2_GEN_SUB_DIR[feature] = gen_sub_dir
    if validation_func:
        FEATURE_2_REGISTER_VALIDATION_FUNCTION[feature] = validation_func
    if dependencies:
        FEATURE_2_DEPENDENCIES[feature] = dependencies

def register(func):
    global FUNCTIONS
    if func not in FUNCTIONS:
        FUNCTIONS.append(func)
        feature = getattr(func, '__name__', repr(func))
        if feature in FEATURE_2_GEN_SUB_DIR:
            gen_sub_dir = FEATURE_2_GEN_SUB_DIR[feature]
            copy_gen_directory_if_not_exists(gen_sub_dir)
        if feature in FEATURE_2_REGISTER_VALIDATION_FUNCTION:
            validation_func = FEATURE_2_REGISTER_VALIDATION_FUNCTION[feature]
            validation_func()
        if feature in FEATURE_2_DEPENDENCIES:
            for dependency_feature in FEATURE_2_DEPENDENCIES[feature]:
                log(LOG_LEVEL, LOG_LEVEL_BASIC, f"adding dependency of {feature}: {dependency_feature}")
                register(FEATURE_2_FUNCTION[dependency_feature])


def add(sourcePathArr, resourcePathArr, excludeAnnotationsArr, langsDict, featureArr):
    splitAndAppendIfNotContains(sourcePathArr, featureArr[0], ';')
    splitAndAppendIfNotContains(resourcePathArr, featureArr[1], ';')
    splitAndAppendIfNotContains(excludeAnnotationsArr, featureArr[2], ';')
    if len(featureArr) >= 4:
        # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"add: {featureArr[3]}")
        # langsDict.update(featureArr[3])
        for lang, dirs in featureArr[3].items():
            if lang not in langsDict:
                langsDict[lang] = dirs
            else:
                langsDict[lang].extend(dirs)

def splitAndAppendIfNotContains(array, csv, separator):
    for item in csv.split(separator):
        if item and item not in array:
            array.append(item)

def usage():
    print("Usage: monkey-generator.py [-h | --help] [-j <monkey.jungle> | --jungle=<monkey.jungle>] [-t <template> | --template=<template>] [-c | --clean] [-a | --all-devices]")

def parse_memory_sizes():
    global MEMORY_2_K, MEMORY_ORDER
    MEMORY_SIZES = set()
    for dev in DEVICES:
        device = DEVICES[dev]
        if APP_TYPE in DEVICES[dev]['memory']:
            limit = DEVICES[dev]['memory'][APP_TYPE]
            MEMORY_SIZES.add(limit)
    MEMORY_SIZES = sorted(list(MEMORY_SIZES))
    for limit in MEMORY_SIZES:
        k = f"{int(limit / 1024)}K"
        MEMORY_2_K[limit] = k
        # K_2_MEMORY[k] = limit
    MEMORY_ORDER = sorted(list(MEMORY_2_K))
    log(LOG_LEVEL, LOG_LEVEL_BASIC, f"MEMORY_ORDER: {MEMORY_ORDER}")
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"K_2_MEMORY: {K_2_MEMORY}")


def replace_placeholders(str):
    for placeholder in MONKEY_GENERATOR_REPLACE:
        if f'{{{placeholder}}}' in str:
            str = str.replace('{%s}' % placeholder, MONKEY_GENERATOR_REPLACE[placeholder])
        if f'{{{placeholder}?' in str:
            str = re.sub(r'\{%s\?([^:]*):([^}]*)\}' % placeholder, r'\1', str)
    str = re.sub(r'\{[A-Z]+\?([^:]*):([^}]*)\}', r'\2', str)
    return str


def add_manifest_id_to_map(lang, lang_uuid, env='prod'):
    if not lang_uuid:
        lang_uuid = str(uuid.uuid4())
    with open(MONKEY_GENERATOR_CONF['manifest_id_map']) as manifest_id_map_file:
        manifest_id_map = json.load(manifest_id_map_file)
        manifest_id_map[lang] = lang_uuid
        print(manifest_id_map)
    if lang in manifest_id_map:
        tmp_file = f"{MONKEY_GENERATOR_CONF['manifest_id_map']}.tmp"
        with open(tmp_file, 'w') as manifest_id_map_file:
            json.dump(manifest_id_map, manifest_id_map_file)
            os.rename(tmp_file, MONKEY_GENERATOR_CONF['manifest_id_map'])
            log(LOG_LEVEL, LOG_LEVEL_BASIC, f'successfully added "{lang}": "{uuid}" to {MONKEY_GENERATOR_CONF["manifest_id_map"]}')


def generate_manifest():
    with open(MONKEY_GENERATOR_CONF['manifest_id_map']) as manifest_id_map_file:
        manifest_id_map = json.load(manifest_id_map_file)
        lang = MONKEY_GENERATOR_REPLACE['LANG']
        env = MONKEY_GENERATOR_REPLACE['ENV'] if 'ENV' in MONKEY_GENERATOR_REPLACE else 'prod'
        if lang not in manifest_id_map:
            print_error(f"missing language in '{MONKEY_GENERATOR_CONF['manifest_id_map']}': {lang}. You can generate a manifest_id: monkey-generator.py --manifest-id-for-lang {lang} [<UUID>]")
            sys.exit()
        if not manifest_id_map[lang]:
            print_error(f"empty language in '{MONKEY_GENERATOR_CONF['manifest_id_map']}': {lang}")
            sys.exit()
        manifest_ids = manifest_id_map[lang]
        if env not in manifest_id_map[lang]:
            print_error(f"missing env in '{MONKEY_GENERATOR_CONF['manifest_id_map']}': [{lang}][{env}]. You can generate a manifest_id: monkey-generator.py --manifest-id-for-lang {lang} [<UUID> [<ENV:prod|beta>]]")
            sys.exit()
        if not manifest_id_map[lang][env]:
            print_error(f"empty env in '{MONKEY_GENERATOR_CONF['manifest_id_map']}': [{lang}][{env}]. You can generate a manifest_id: monkey-generator.py --manifest-id-for-lang {lang} [<UUID> [<ENV:prod|beta>]]")
            sys.exit()
        manifest_id = manifest_id_map[lang][env]
    log(LOG_LEVEL, LOG_LEVEL_BASIC, f"generating {MANIFEST} with id: {manifest_id}")
    with open(MONKEY_GENERATOR_CONF['manifest_xml_template'], 'r') as manifest_template:
        with open(MANIFEST, 'w') as manifest:
            for line in manifest_template:
                if 'iq:application' in line and ' id="' in line:
                    line = re.sub(r' id="([^"]+)"', ' id="%s"' % manifest_id, line)
                manifest.write(line)
                if line == '<?xml version="1.0"?>\n':
                    manifest.write(f"<!-- GENERATED from '{MONKEY_GENERATOR_CONF['manifest_xml_template']}' by {GENERATROR_SIGNATURE} -->\n")

def get_conf(conf):
    return MONKEY_GENERATOR_CONF[conf] if conf in MONKEY_GENERATOR_CONF else ''


def get_base_dirs():
    return get_conf("base_dir").split(';')


def get_base_dir():
    return get_base_dirs()[0]


def parse_monkey_generator_conf():
    global TEMPLATE
    if os.path.exists(MONKEY_GENERATOR_CONF_FILE):
        with open(MONKEY_GENERATOR_CONF_FILE, 'r') as monkey_generator_conf:
            for line in monkey_generator_conf:
                line = line.strip()
                if line and line[0] != '#':
                    key, val = line.split('=', 2)
                    key = key.strip()
                    val = val.strip()
                    if re.match(r'^[A-Z0-9_]+$', key):
                        MONKEY_GENERATOR_REPLACE[key] = val
                    else:
                        MONKEY_GENERATOR_CONF[key] = val
        log(LOG_LEVEL, LOG_LEVEL_BASIC, f"MONKEY_GENERATOR_CONF: {MONKEY_GENERATOR_CONF}")
        log(LOG_LEVEL, LOG_LEVEL_BASIC, f"MONKEY_GENERATOR_REPLACE: {MONKEY_GENERATOR_REPLACE}")


def main(argv):
    global LOG_LEVEL, LOG_LINE_NUMBER, MONKEY_JUNGLE, TEMPLATE, MANIFEST, CIQ_VERSIONS, USED_CIQ_VERSIONS, FEATURES_BY_MEMORY, FEATURE_CONSTRAINS, FILTER_CONSTRAINS

    generate_devices = 'manifest'
    try:
        opts, args = getopt.getopt(argv, 'hj:t:cad:vlm:', ['help', 'jungle', 'template', 'clean', 'all-devices', 'debug', 'verbose', 'log-line-number', 'manifest-id-for-lang'])
    except getopt.GetoptError as e:
        print_error(e)
        usage()
        sys.exit(1)
    LOG_LEVEL = LOG_LEVEL_ALWAYS
    for opt, arg in opts:
        if opt == '-h' or opt == '--help':
            usage()
            sys.exit(0)
        if opt == '-c' or opt == '--clean':
            shutil.rmtree(GENERATED_DEVICES_DIR)
            shutil.rmtree(GENERATED_FEATURES_DIR)
            sys.exit(0)
        if opt == '-a' or opt == '--all-devices':
            generate_devices = 'all'
        if opt == '-d' or opt == '--debug':
            LOG_LEVEL = int(arg)
        if opt == '-v' or opt == '--verbose':
            LOG_LEVEL = 1
        if opt == '-l' or opt == '--log-line-number':
            LOG_LINE_NUMBER = True
    parse_monkey_generator_conf()
    for opt, arg in opts:
        if opt == '-m' or opt == '--manifest-id-for-lang':
            lang = arg
            i = argv.index(opt)
            uuid = argv[i + 2] if len(argv) > i + 2 and argv[i + 1] == arg else ''
            env = argv[i + 3] if len(argv) > i + 3 and argv[i + 1] == arg else ''
            print(f"lang: {lang}, opts: {opts}, argv: {argv}, i: {i}, uuid: {uuid}, env: {env}, a[i+1]: {argv[i+1]}")
            # add_manifest_id_to_map(lang, uuid, env)
            sys.exit(0)
    if 'manifest_xml_template' in MONKEY_GENERATOR_CONF:
        generate_manifest()
    if 'monkey_jungle_template' in MONKEY_GENERATOR_CONF:
        TEMPLATE = MONKEY_GENERATOR_CONF['monkey_jungle_template']
    for opt, arg in opts:
        if opt == '-j' or opt == '--jungle':
            MONKEY_JUNGLE = arg
            TEMPLATE = MONKEY_JUNGLE.replace('.jungle', '.template.jungle')
        if opt == '-t' or opt == '--template':
            TEMPLATE = arg

    if not os.path.exists(TEMPLATE):
        sys.exit(f"Missing template file: {TEMPLATE}")

    # ALL_FEATURES = sorted(filter(lambda dir: MULTI_FEATURE_DIR_SEPARATOR not in dir, os.listdir('features'))) if os.path.isdir('features') else []
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"ALL_FEATURES: {ALL_FEATURES}")
    read_all_devices()

    # placeholder = 'LANG'
    # line = 'base.sourcePath = {LANG?../../source:source};{LANG?../../gen/{LANG}/source:gen/eng/source}'
    # print(line)
    # #  % MONKEY_GENERATOR_CONF[placeholder]
    # line = re.sub(r'\{%s\?([^:]*):([^}]*)\}' % placeholder, r'\2', line)
    # # line = re.sub(r'\{%s?\([^:]*\):\([^}]*\)\}' % placeholder, 'X\1Y', line)
    # print(line)
    # sys.exit("foo")

    with open(MONKEY_JUNGLE, 'w') as output:
        output.write(f"# GENERATED from '{TEMPLATE}' by {GENERATROR_SIGNATURE}\n\n");

        with open(TEMPLATE, 'r') as template:
            for line in template:
                if line[0] != '#':
                    if '#' in line and line[0] != '#':
                        print_warn_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"comments are only allowed at the beginning of the line: {line}")
                    orig_line = line
                    line = replace_placeholders(line)
                    # for placeholder in MONKEY_GENERATOR_REPLACE:
                    #     if f'{{{placeholder}}}' in line:
                    #         line = line.replace('{%s}' % placeholder, MONKEY_GENERATOR_REPLACE[placeholder])
                    #     if f'{{{placeholder}?' in line:
                    #         line = re.sub(r'\{%s\?([^:]*):([^}]*)\}' % placeholder, r'\1', line)
                    # line = re.sub(r'\{[A-Z]+\?([^:]*):([^}]*)\}', r'\2', line)
                    if (line != orig_line):
                        output.write(f'# {orig_line}')
                else:
                    line = '#' + line
                # output.write(line)
                line = line.strip()
                # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{line}")
                write_line = False
                if line.startswith('project.manifest'):
                    if 'manifest_xml_template' in MONKEY_GENERATOR_CONF:
                        output.write(f"# {line}\n")
                        line = 'project.manifest = manifest.xml # GENERATED'
                    else:
                        MANIFEST = line.split('=', 2)[1].strip().split(' ', 1)[0]
                    write_line = True
                    log(LOG_LEVEL, LOG_LEVEL_BASIC, "MANIFEST: " + MANIFEST)
                    parse_manifest(MANIFEST)
                elif line.startswith('base.'):
                    base_key, val = line.split('=', 2)
                    base_key = base_key.strip()
                    val = val.strip()
                    base, key = base_key.split('.', 1)
                    if key not in BASE:
                        BASE[key] = []
                    BASE[key].append(val)
                elif line.startswith('monkey_generator_features_memoryCommon'):
                    memory_str, features_str = line.split('=', 1)
                    features = features_str.strip().split(';')
                    FEATURES_BY_MEMORY['common'] = features
                    # write_line = True
                elif line.startswith('monkey_generator_features_memory'):
                    memory_str, features_str = line.split('=', 1)
                    memory = memory_str.replace('monkey_generator_features_memory', '').strip()
                    features = features_str.strip().split(';')
                    FEATURES_BY_MEMORY[memory] = features
                    # write_line = True
                elif line.startswith('monkey_generator_feature_'):
                    if '#' in line:
                        line, comment = line.split('#', 1)
                    line = line.strip()
                    value = ''
                    if ('=' in line):
                        feature_str, value = line.split('=', 1)
                    else:
                        feature_str = line
                    feature_data = feature_str.strip().replace('monkey_generator_feature_', '')
                    feature = None
                    for data in FEATURE_ATTRIBUTES:
                        if feature_data.endswith(data):
                            feature = feature_data.replace(f"_{data}", '')
                            if feature not in FEATURE_CONSTRAINS:
                                FEATURE_CONSTRAINS[feature] = {}
                            FEATURE_CONSTRAINS[feature][data] = value.strip()
                    if not feature:
                        print_error(f"unknown feature: {feature_str}")
                elif line.startswith('monkey_generator_filter_device_'):
                    if '#' in line:
                        line, comment = line.split('#', 1)
                    line = line.strip()
                    filter_str, value = line.split('=', 1)
                    filter_data = filter_str.strip().replace('monkey_generator_filter_device_', '')
                    my_filter = None
                    for data in FEATURE_ATTRIBUTES:
                        if filter_data.endswith(data):
                            my_filter = filter_data.replace(f"_{data}", '')
                            feature = value.strip()
                            # if filter not in FILTER_CONSTRAINS:
                            #     FILTER_CONSTRAINS[filter] = {}
                            # if feature not in FILTER_CONSTRAINS[filter]:
                            #     FILTER_CONSTRAINS[filter][feature] = []
                            # FILTER_CONSTRAINS[filter][feature] = feature
                            if feature not in FILTER_CONSTRAINS:
                                FILTER_CONSTRAINS[feature] = {}
                            FILTER_CONSTRAINS[feature][my_filter] = feature
                    if not my_filter:
                        print_error(f"unknown filter: {filter_str}")
                elif line.startswith('monkey_generator_used_ciq_versions'):
                    used_ciq_versions = line.split('=', 1)[1].strip().split(';')
                    #  .split(' ', 1)[0]
                    used_ciq_versions = sorted(used_ciq_versions, key=natural_sort_key)
                    log(LOG_LEVEL, LOG_LEVEL_BASIC, "used_ciq_versions: " + str(used_ciq_versions))
                    USED_CIQ_VERSIONS = used_ciq_versions
                    ciq_versions = set(CIQ_VERSIONS)
                    ciq_versions.update(used_ciq_versions)
                    CIQ_VERSIONS = sorted(list(ciq_versions), key=natural_sort_key)
                    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"CIQ versions: {CIQ_VERSIONS}")
                elif line.startswith('monkey_generator_register'):
                    register_features = line.split('=', 2)[1].strip().split(';')
                    for feature in register_features:
                        if feature in FEATURE_2_FUNCTION:
                            register(FEATURE_2_FUNCTION[feature])
                elif line.startswith('monkey_generator_const_'):
                    if '#' in line:
                        line, comment = line.split('#', 1)
                    line = line.strip()
                    const_str, json_path = line.split('=', 2)
                    const_data = const_str.strip().replace('monkey_generator_const_', '')
                    const_type = re.sub(r'_.*', '', const_data)
                    const_name = const_data.replace(f"{const_type}_", '')
                    const_value = None
                    if const_type == 'font':
                        register(const_font)
                    else:
                        print_error(f"unknown const_type: {const_type}")
                        sys.exit(1)
                    if const_type not in CONSTS:
                        CONSTS[const_type] = {}
                    CONSTS[const_type][const_name] = json_path.strip()
                elif line.startswith('monkey_generator_placeholder'):
                    if '#' in line:
                        line, comment = line.split('#', 1)
                    line = line.strip()
                    cmd, placeholders_str = line.split('=', 1)
                    placeholders_str = placeholders_str.strip()
                    placeholders = placeholders_str.split(';')
                    for placeholder_pair in placeholders:
                        key, val = placeholder_pair.split('=')
                        if key not in MONKEY_GENERATOR_REPLACE:
                            MONKEY_GENERATOR_REPLACE[key] = val
                    log(LOG_LEVEL, LOG_LEVEL_BASIC, f"MONKEY_GENERATOR_REPLACE: {MONKEY_GENERATOR_REPLACE}")
                else:
                    write_line = True

                if not write_line:
                    line = '# ' + line
                output.write(f"{line}\n")

        log(LOG_LEVEL, LOG_LEVEL_BASIC, f"FEATURES_BY_MEMORY: {FEATURES_BY_MEMORY}")
        log(LOG_LEVEL, LOG_LEVEL_BASIC, f"FEATURE_CONSTRAINS: {FEATURE_CONSTRAINS}")
        log(LOG_LEVEL, LOG_LEVEL_BASIC, f"FILTER_CONSTRAINS: {FILTER_CONSTRAINS}")

        parse_memory_sizes()

        # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{MONKEY_JUNGLE}")
        devices = ALL_DEVICES if generate_devices == 'all' else MANIFEST_DEVICES
        original_devices = devices.copy()
        devices_to_exclude = []
        incompatible_devices = []
        if FILTER_CONSTRAINS:
            devices_to_exclude_reason = {}
            # unknown_filters = set()
            for dev in ALL_DEVICES:
                for my_filter in FILTER_CONSTRAINS:
                    has_feature_obj = has_feature_by_constraints(dev, FILTER_CONSTRAINS, my_filter)
                    if has_feature_obj[False]:
                        devices_to_exclude.append(dev)
                        devices_to_exclude_reason[dev] = has_feature_obj[False]
                        break
                # device = DEVICES[dev]
                # for attr in FILTER_CONSTRAINS['include_device']:
                #     val = FILTER_CONSTRAINS['include_device'][attr]
                #     if attr == 'min_memory' and device['memory'][APP_TYPE] < int(val):
                #         print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}: excluding device because memory: {device['memory'][APP_TYPE]} < min_memory: {val}")
                #         devices_to_exclude.append(dev)
                #     else:
                #         unknown_filters.add(attr)
            # if unknown_filters:
            #     print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"unknown filters: {unknown_filters}")
            if devices_to_exclude:
                incompatible_devices_details = []
                for dev in devices_to_exclude:
                    if dev in devices:
                        devices.remove(dev)
                        incompatible_devices.append(f"{dev}:{','.join([f.split(':')[0] for f in devices_to_exclude_reason[dev]])}")
                        incompatible_devices_details.append(f"{dev}:{devices_to_exclude_reason[dev]}")
                        devices_to_exclude.remove(dev)
                    if dev in MISSING_DEVICES:
                        MISSING_DEVICES.remove(dev)
                if incompatible_devices:
                    print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"filtered out {len(incompatible_devices)} incompatible devices from {MANIFEST}: {incompatible_devices_details}")
        if MISSING_DEVICES:
            print_error(f"MISSING_DEVICES: {MISSING_DEVICES}")


        read_devices_datafield_hash_data(devices)
        output.write(f"\n# GENERATED #\n");
        output.write(f"# excluded {len(devices_to_exclude)} devices that are incompatible and are not in {MANIFEST}: {', '.join(devices_to_exclude)}\n");
        output.write(f"# filtered out {len(incompatible_devices)} incompatible devices by constraints from {MANIFEST}: {', '.join(incompatible_devices)}\n");
        output.write(f"# included {len(devices)} devices\n\n");
        original_devices.insert(0, 'base')
        log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"devices ({generate_devices}): {devices}")
        for dev in original_devices:
            if dev not in devices and dev != 'base':
                output.write(f"{dev}.sourcePath=incompatible\n")
                continue

            # if dev == 'base':
            #     continue
            log(LOG_LEVEL, LOG_LEVEL_OUTPUT, f"{dev}:")
            # sourcePathArr = ['source']
            sourcePathArr = []
            # resourcePathArr = ['resources']
            resourcePathArr = []
            excludeAnnotationsArr = []
            langsDict = {}

            if dev == 'base':
                if 'sourcePath' in BASE:
                    sourcePathArr.extend(BASE['sourcePath'])
                if 'resourcePath' in BASE:
                    resourcePathArr.extend(BASE['resourcePath'])
                if 'excludeAnnotations' in BASE:
                    excludeAnnotationsArr.extend(BASE['excludeAnnotations'])
                conf_base_dir = get_base_dir()
                for dir in sorted(filter(lambda d: d.startswith('resources-'), os.listdir(conf_base_dir if conf_base_dir else '.'))):
                    lang = dir.replace('resources-', '')
                    if lang in LANGUAGES:
                        if lang not in langsDict:
                            langsDict[lang] = []
                        langsDict[lang].append(f'{conf_base_dir}{dir}')
            else:
                sourcePathArr.append(f"$({dev}.sourcePath)")
                resourcePathArr.append(f"$({dev}.resourcePath)")
                excludeAnnotationsArr.append(f"$({dev}.excludeAnnotations)")

            for func in FUNCTIONS:
                # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}.add: {func}")
                add(sourcePathArr, resourcePathArr, excludeAnnotationsArr, langsDict, func(dev))

            for lang in LANGUAGES:
                if f"lang.{lang}" in BASE:
                    if lang not in langsDict:
                        langsDict[lang] = []
                    langsDict[lang].extend(BASE[f"lang.{lang}"])

            if langsDict:
                if '' in langsDict:
                    default_language = ''
                elif 'eng' in langsDict:
                    default_language = 'eng'
                else:
                    default_language = False
                if default_language != False:
                    resourcePathArr.append(';'.join(langsDict[default_language]))

            min_required_elements = 0 if dev == 'base' else 1
            if len(sourcePathArr) > min_required_elements:
                # output.write(f"{dev}.sourcePath=$({dev}.sourcePath);{';'.join(sourcePathArr)}\n")
                output.write(f"{dev}.sourcePath={';'.join(sourcePathArr)}\n")
            if len(resourcePathArr) > min_required_elements:
                # output.write(f"{dev}.resourcePath=$({dev}.resourcePath);{';'.join(resourcePathArr)}\n")
                output.write(f"{dev}.resourcePath={';'.join(resourcePathArr)}\n")
            if len(excludeAnnotationsArr) > min_required_elements:
                # output.write(f"{dev}.excludeAnnotations=$({dev}.excludeAnnotations);{';'.join(excludeAnnotationsArr)}\n")
                output.write(f"{dev}.excludeAnnotations={';'.join(excludeAnnotationsArr)}\n")
            if langsDict:
                for lang in langsDict:
                    if lang != default_language:
                        # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {lang} = {langsDict[lang]}")
                        # if lang == 'eng':
                        #     output.write(f"{dev}.lang.DEFAULT=$({dev}.lang.DEFAULT);{';'.join(langsDict[lang])}\n")
                        output.write(f"{dev}.lang.{lang}=$({dev}.lang.{lang});{';'.join(langsDict[lang])}\n")


def generate_lang_strings(lang_code_length):
    conf_base_dir = get_base_dir()
    # for lang in LANGUAGES:
    for lang in MANIFEST_LANGS + ['unknown']:
        # lang_dir = f"resources-{lang}"
        lang_dir = f"{conf_base_dir}{GENERATED_FEATURES_DIR}/lang/lang-{lang}"
        lang_code = LANG_CODE3_2_LANG_CODE2[lang] if lang_code_length == 2 else lang
        os.makedirs(lang_dir, 0o755, True)
        with open(f"{lang_dir}/strings-lang-{lang}.xml", 'w') as output:
            output.write(f"<strings>\n");
            output.write(f'\t<string id="lang{lang_code_length}">{lang_code}</string>\n');
            output.write(f"</strings>");
def generate_lang_strings2():
    generate_lang_strings(2)
def generate_lang_strings3():
    generate_lang_strings(3)
def lang(dev, lang_code_length):
    conf_base_dir = get_base_dir()
    if dev == 'base':
        dst_dir = f'{conf_base_dir}{GENERATED_FEATURES_DIR}/lang'
        # hasSystemLanguage = has_method(dev, 'systemLanguage');
        # if hasSystemLanguage:
        #     return [has_directory(f"{conf_base_dir}{GENERATED_FEATURES_DIR}/lang/source"), has_directory(f"{conf_base_dir}{GENERATED_FEATURES_DIR}/lang/resources"), 'no_system_language']
        # else:
        # lang_dirs = {}
        lang_dirs = {'': [f"{conf_base_dir}{GENERATED_FEATURES_DIR}/lang/lang-unknown"]}
        for lang in MANIFEST_LANGS:
            lang_dirs[lang] = [f"{conf_base_dir}{GENERATED_FEATURES_DIR}/lang/lang-{lang}"]
        resource_dir = '' # has_directory(f"{conf_base_dir}{GENERATED_FEATURES_DIR}/lang/lang-unknown")
        return [has_directory(f"{conf_base_dir}{GENERATED_FEATURES_DIR}/lang/source"), resource_dir, f'lang{5 - lang_code_length}', lang_dirs]
    else:
        return ['', '', '']
def lang2(dev):
    return lang(dev, 2)
def lang3(dev):
    return lang(dev, 3)
pre_register(lang2, 'lang/source', generate_lang_strings2)
pre_register(lang3, 'lang/source', generate_lang_strings3)


def languages(dev):
    if dev == 'base':
        return ['', '', '']
    device = DEVICES[dev]
    hebrewExcludeAnnotation = 'no_hebrew' if 'heb' in device['languages'] else 'hebrew'
    return ['', '', hebrewExcludeAnnotation]
pre_register(languages)

# npx cft-font-info fr230 | jq '.fonts | keys[] as $font | {font: $font} + .[$font] |  {font:.font, chars:[.charInfo[].char]|join("")}'
# npx cft-font-info fr230 | jq '.fonts | map_values([.charInfo[].char]|join(""))'
# npx cft-font-info fr230 | jq '.devices + (.fonts | map_values([.charInfo[].char]|join("")))'
# npx cft-font-info fr230 | jq '{devices: .devices, chars: (.fonts | map_values([.charInfo[].char]|join("")))}'
# npx cft-font-info fr230 | jq '{devices: .devices, chars: (.fonts[] |= ([.charInfo[].char]|add))}'

FONTS_JSON_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/font-analyzer/chars'
def number_font(dev):
    if dev == 'base':
        return ['', '', '']
    common_chars = None
    with open(f"{FONTS_JSON_DIR}/{dev}.chars.json") as chars_json_file:
        chars_json = json.load(chars_json_file)
        # print(f"{chars_json['fonts']}")
        # ''.join(set(word_1).intersection(word_2))
        if len(chars_json['fonts']) > 0:
            for font in chars_json['fonts']:
                chars = chars_json['fonts'][font]
                # print(f"chars: {chars}")
                if common_chars == None:
                    common_chars = set(chars)
                else:
                    common_chars = common_chars.intersection(chars)
        else:
            print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}: empty \"fonts\" in {chars_json_file.name}")
        is_missing = False
        missing_mc_fonts = set()
        missing_number_mc_fonts = set()
        for fontSetArea in chars_json['devices'][dev]['fontSets']:
            missing_from_fontset = {}
            for mc_font in chars_json['devices'][dev]['fontSets'][fontSetArea]:
                font = chars_json['devices'][dev]['fontSets'][fontSetArea][mc_font]
                if font not in chars_json['fonts']:
                    print_error_log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: missing font chars for fontSet: {fontSetArea}: {mc_font}: {font}")
                    # print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}: missing: devices.{dev}.fontSets.{fontSetArea}.{mc_font}: \"{font}\"")
                    missing_from_fontset[mc_font] = font
                    is_missing = True
                    missing_mc_fonts.add(mc_font)
                    if 'NUMBER' in mc_font:
                        missing_number_mc_fonts.add(mc_font)
                else:
                    log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: found font chars for fontSet: {fontSetArea}: {mc_font}: {font}")
            if missing_from_fontset:
                # print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}: missing: devices.{dev}.fontSets.{fontSetArea}: {missing_from_fontset}")
                print_error_log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: {fontSetArea}: {missing_from_fontset} MISSING")
        if is_missing:
            if missing_number_mc_fonts:
                print_warn_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}: some number font chars are missing: {missing_number_mc_fonts}")
            print_error_log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: some font chars are missing: {missing_mc_fonts}")
        else:
            print_warn_log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: no font chars are missing")
    if common_chars:
        # print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}: {common_chars}")
        if '\x00' in common_chars:
            common_chars.remove('\x00')
        if '\x02' in common_chars:
            common_chars.remove('\x02')
        common_chars = list(common_chars)
        common_chars.sort()

        # with open(f"{FONTS_JSON_DIR}/{dev}.fonts.json") as fonts_json_file:
        #     fonts_json = json.load(fonts_json_file)
        #     for char in common_chars:
        #         charInfo = fonts_json['fonts']['']

        # from_c = -1
        # to_c = -1
        # for c in common_chars:
        #     if to_c != ord(c) - 1:
        #         if from_c != to_c and to_c > from_c + 3:
        #             print(f"chars: {to_c-from_c+1}:[{from_c} {chr(from_c)}, {to_c} {chr(to_c)}]")
        #         from_c = ord(c)
        #     to_c = ord(c)
        # if from_c != to_c and to_c > from_c + 3:
        #     print(f"chars: {to_c-from_c+1}:[{from_c} {chr(from_c)}, {to_c} {chr(to_c)}]")
        common_chars = ''.join(common_chars)
        # print(f"{dev}: common_chars: {common_chars}")
        device = DEVICES[dev]
        memory_limit = device['memory'][APP_TYPE]
        if (memory_limit / len(common_chars) < 372): # 16K / 44 = 372
            if dev == 'fr920xt':
                orig_len = len(common_chars)
                common_chars = " !\"#$%&'()*+,-./0123456789:;"
                print_warn_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}[{memory_limit}]: common_chars[{orig_len} => {len(common_chars)}]: replaced with: \"{common_chars}\"")
            else:
                print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}[{memory_limit}]: common_chars[{len(common_chars)}]: \"{common_chars}\"")
        else:
            log(LOG_LEVEL, LOG_LEVEL_INPUT, f"{dev}: common_chars[{len(common_chars)}]: \"{common_chars}\"")
    else:
        common_chars = ''
        print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}: no common_chars")
    has_space = common_chars and ' ' in common_chars
    has_lower_case_abc = 'abcdefghijklmnopqrstuvwxyz' in common_chars
    has_upper_case_abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' in common_chars

    device_dir = f"{GENERATED_DEVICES_DIR}/{dev}"
    device_file = f"{device_dir}/chars.mc"
    os.makedirs(device_dir, 0o755, True)
    with open(device_file, 'w') as output:
        # output.write(f"// GENERATED for {dev} by {GENERATROR_SIGNATURE}\n\n");
        output.write(f"// GENERATED by {GENERATROR_SIGNATURE}\n\n")
        # output.write("import Toybox.Lang;\n")

        # if USE_MODULES:
        #     output.write("module Flocsy {\n")
        #     output.write("\tmodule DataFieldLayout {\n\n")

        output.write(f"const NUMBER_FONT_HAS_SPACE = {'true' if has_space else 'false'};\n")
        output.write(f"const NUMBER_FONT_HAS_LOWER_CASE_ABC = {'true' if has_lower_case_abc else 'false'};\n")
        output.write(f"const NUMBER_FONT_HAS_UPPER_CASE_ABC = {'true' if has_upper_case_abc else 'false'};\n")
        output.write(f"const NUMERIC_CHARS = \"{escape_mc_string(common_chars)}\"; // [{len(common_chars)}]\n")
        output.write(f"const NUMERIC_CHARS_UNKNOWN = {'true' if len(common_chars) == 0 else 'false'};\n")

        # if USE_MODULES:
        #     output.write("\t}\n")
        #     output.write("}\n")


    sourceDirs = list(filter(None, [has_directory(f"{GENERATED_FEATURES_DIR}/number_font"), has_directory(f"{GENERATED_DEVICES_DIR}/{dev}")]))
    return [';'.join(sourceDirs), '', '']
pre_register(number_font, 'number_font', dependencies=['ciq_api'])

def get_color_depth(device):
    return device['compiler']['bitsPerPixel'];

def get_all_color_depths():
    color_depth = set()
    for dev in DEVICES:
        device = DEVICES[dev]
        colorDepth = device['compiler']['bitsPerPixel']
        color_depth.add(colorDepth)
    all_color_depth = sorted(list(color_depth))
    return all_color_depth;

def check_color_depth_src_dir():
    missing = False
    dst_dir = f'{SOURCE_FEATURES_DIR}/color_depth'
    dirs = []
    for color_depth in get_all_color_depths():
        dirs.append(f'{dst_dir}/{color_depth}bpp')
    if os.path.isdir(dst_dir):
        for bpp_dir in dirs:
            if os.path.isdir(bpp_dir):
                if not os.listdir(bpp_dir):
                    missing = True
                    print_error(f"no files in: {bpp_dir}\n\tAdd file(s) to it")
            else:
                missing = True
                print_error(f"missing directory: {bpp_dir}\n\tCreate directory: {bpp_dir}")
    else:
        missing = True
        print_error(f"missing directory: {dst_dir}/\n\tCreate directories: {dirs}")

def color_depth(dev):
    if dev == 'base':
        return ['', '', '']
    device = DEVICES[dev]
    colorDepth = device['compiler']['bitsPerPixel'];
    return [has_directory(f"{SOURCE_FEATURES_DIR}/color_depth/{colorDepth}bpp"), '', '']
pre_register(color_depth, None, check_color_depth_src_dir)


def get_color_palette_dirs(device):
    if 'palette' not in device['compiler']:
        return [f"{device['compiler']['displayType']}-{device['compiler']['bitsPerPixel']}bpp", f"{device['compiler']['bitsPerPixel']}bpp"]
    color_palette = device['compiler']['palette']['colors'];
    palette_size = len(list(filter(lambda c: c != 'TRANSPARENT', color_palette)))
    match palette_size:
        case 64 | 66:
            return [f"{device['compiler']['displayType']}-64colors", '64colors']
        case 14:
            return [f"{device['compiler']['displayType']}-14colorsA" if '5500AA' in color_palette else f"{device['compiler']['displayType']}-14colorsB", '14colors']
        case 8 | 2:
            return [f"{device['compiler']['displayType']}-{palette_size}colors", f"{palette_size}colors"]
        case _:
            print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{device['dev']}: unknown color palette: {color_palette}")
            return [f"{device['compiler']['displayType']}-{device['compiler']['bitsPerPixel']}bpp-?", f"{palette_size}colors-?"]

def get_all_color_palettes():
    color_palette_set = set()
    color_palette_list = []
    for dev in DEVICES:
        device = DEVICES[dev]
        color_palette_dirs = get_color_palette_dirs(device)
        if str(color_palette_dirs) not in color_palette_set:
            color_palette_list.append(color_palette_dirs)
            color_palette_set.add(str(color_palette_dirs))
    all_color_palettes = sorted(list(color_palette_list))
    return all_color_palettes;

def check_color_palette_src_dir():
    missing = False
    conf_base_dir = get_base_dir()
    dst_dir = f'{conf_base_dir}features/color_palette'
    dirs = []
    palettes = get_all_color_palettes()
    for color_palette in palettes:
        dirs.append(f'{dst_dir}/{color_palette}')
    if os.path.isdir(dst_dir):
        for color_palette in palettes:
            # dirs.append(f'{dst_dir}/{color_palette}')
            has_dir = False
            for colors_dir in color_palette:
                dir_path = f'{dst_dir}/{colors_dir}'
                if os.path.isdir(dir_path):
                    has_dir = True
                    if not os.listdir(dir_path):
                        missing = True
                        print_error(f"no files in: {dir_path}\n\tAdd file(s) to it")
            if not has_dir:
                missing = True
                print_error(f"missing directory under: {dst_dir}\n\tCreate at least one directory from: {color_palette}")
    else:
        missing = True
        print_error(f"missing directory: {dst_dir}/\n\tCreate directories: {dirs}")

def color_palette(dev):
    if dev == 'base':
        return ['', '', '']
    conf_base_dir = get_base_dir()
    device = DEVICES[dev]
    color_palette_dirs = get_color_palette_dirs(device)
    for color_palette_dir in color_palette_dirs:
        path = has_directory(f"{conf_base_dir}features/color_palette/{color_palette_dir}")
        if path:
            log(LOG_LEVEL, LOG_LEVEL_OUTPUT, f"{dev}: color_palette: {color_palette_dirs} => {color_palette_dir}")
            return [path, '', '']
    print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{device['dev']}: missing color palette directory: {color_palette_dirs}")
    return ['', '', '']
pre_register(color_palette, None, check_color_palette_src_dir)


def color(dev):
    if dev == 'base':
        return ['', '', '']
    device = DEVICES[dev]
    colorDepth = device['compiler']['bitsPerPixel'];
    return ['', '', 'color' if colorDepth == 1 else 'no_color']
pre_register(color)

def menu2(dev):
    if dev == 'base':
        return ['', '', '']
    conf_base_dir = get_base_dir()
    minConnectIQVersion = DEVICE_MIN_VERSION[dev]
    has_menu2 = minConnectIQVersion >= '3.0.0'
    log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: minConnectIQVersion: {minConnectIQVersion} => {'menu2' if has_menu2 else 'menu'}")
    # return ['', has_directory(f"{RESOURCES_FEATURES_DIR}/menu2/{'menu2' if has_menu2 else 'menu'}"), 'menu;no_menu2' if has_menu2 else 'menu2']
    return ['', has_directory(f"{conf_base_dir}features/menu2/{'menu2' if has_menu2 else 'menu'}"), 'menu;no_menu2' if has_menu2 else 'menu2']
# pre_register(menu2, None, check_color_depth_src_dir)
pre_register(menu2)

def field2obscurity_flags_str(field):
    obs = sorted(field['obscurity'])
    o = ''
    for side in obs:
        o += side[0]
    return o

def field2obscurity_flags_int(field):
    obs = sorted(field['obscurity'])
    obscurity_flags = 0
    for side in obs:
        obscurity_flags |= OBSCURITY_TO_NUMBER[side]
    return obscurity_flags

def field2hash(field):
    if field['location']['height'] >= 1000:
        sys.exit(f"{dev}: device_field2hash: need to fix the hash, because 1000 <= height = {field['location']['height']}")
    obscurity_flags = field2obscurity_flags_int(field)
    # hash = (((l['width'] << height_bits) | l['height']) << 4) | obscurity_flags
    hash = (field['location']['width'] * 1000 + field['location']['height']) * 100 + obscurity_flags
    return hash

FONT_ORDER = ['-', 'xtiny', 'glanceFont', 'simExtNumber6', 'tiny', 'simExtNumber2', 'small', 'glanceNumberFont', 'medium', 'simExtNumber1', 'large', 'numberMild', 'numberMedium', 'numberHot',
        'simExtNumber3', 'numberThaiHot', 'simExtNumber4', 'simExtNumber5']
def font_order(font):
    return FONT_ORDER.index(font)

def to_mc_value(python_value):
    if isinstance(python_value, list):
        return [to_mc_value(o) for o in python_value]
    if python_value is None: return 'null /*conflict*/'
    if python_value is False: return 'false /*no value*/'
    return python_value

def destring_arr_values(arr):
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"destring_arr_values: {arr}")
    if isinstance(arr, list):
        return '[' + ', '.join([str(v) for v in arr]) + ']'
    else:
        return arr

def destring_dict_values(map):
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"destring_dict_values: {map}")
    if isinstance(map, dict):
        return '{' + ', '.join([f"{k}: {str(map[k])}" for k in map]) + '}'
    else:
        return map

def destring_arr_dict_values(arr):
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"destring_arr_dict_values: {arr}")
    # if isinstance(arr, list):
    result = {}
    for my_dict in arr:
        if isinstance(my_dict, dict):
            for key in my_dict:
                if key not in result:
                    val = my_dict[key]
                    result[key] = to_mc_value(val)
                else:
                    return arr
        else:
            return arr
    return destring_dict_values(result)
    # else:
    #     return arr

FONT_TO_MC_FONT = {#'-': '',
        'xtiny': 'XTINY', 'tiny': 'TINY', 'small': 'SMALL', 'medium': 'MEDIUM', 'large': 'LARGE',
        'numberMild': 'NUMBER_MILD', 'numberMedium': 'NUMBER_MEDIUM', 'numberHot': 'NUMBER_HOT', 'numberThaiHot': 'NUMBER_THAI_HOT',
        'glanceFont': 'GLANCE', 'glanceNumberFont': 'GLANCE_NUMBER',
        'auxiliaryFont1': 'AUX1', 'auxiliaryFont2': 'AUX2', 'auxiliaryFont3': 'AUX3', 'auxiliaryFont4': 'AUX4', 'auxiliaryFont5': 'AUX5',
        'auxiliaryFont6': 'AUX6', 'auxiliaryFont7': 'AUX7', 'auxiliaryFont8': 'AUX8', 'auxiliaryFont9': 'AUX9',
        'simExtNumber1': {'edge1050': 'LARGE', 'edgeexplore2': 'MEDIUM', 'fenix843mm': 'XTINY', 'fenix847mm': 'XTINY', 'fenixe': 'XTINY', 'fr265': 'XTINY', 'venusq2': 'XTINY', 'venusq2m': 'XTINY'},
        'simExtNumber2': {'fenix8solar47mm': 'XTINY', 'fr965': 'XTINY', 'legacyherocaptainmarvel': 'TINY', 'legacyherofirstavenger': 'TINY', 'legacysagadarthvader': 'TINY', 'legacysagarey': 'TINY',
                'vivoactive4': 'TINY', 'vivoactive4s': 'TINY'},
        'simExtNumber5': {'edge540': 'MEDIUM', 'edge840': 'MEDIUM', 'edge1050': 'MEDIUM'},
        'simExtNumber6': {'approachs62': 'XTINY', 'edge540': 'SMALL', 'edge840': 'SMALL'}
}
def font2mc_font(font, dev):
    # return f"Graphics.FONT_{font.upper()}" if font not in FONT_TO_MC_FONT else\
    #     (f"Graphics.FONT_{FONT_TO_MC_FONT[font]}" if FONT_TO_MC_FONT[font] != '' else 'null')
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, "{dev}: font: {font}")
    if font is False or font is None:
        return to_mc_value(font)
    elif font in FONT_TO_MC_FONT:
        if type(FONT_TO_MC_FONT[font]) == str:
            if FONT_TO_MC_FONT[font] == '':
                return to_mc_value(None)
            else:
                return f"Graphics.FONT_{FONT_TO_MC_FONT[font]}"
        elif type(FONT_TO_MC_FONT[font]) == dict and dev in FONT_TO_MC_FONT[font]:
            return f"Graphics.FONT_{FONT_TO_MC_FONT[font][dev]}"
        else:
            print_error(f"missing font: {font} for {dev}")
            # raise ValueError(f"1 missing font: {font} for {dev}")
            return f"Graphics.FONT_{font.upper()}"
    else:
        print_error(f"missing font: {font} for {dev}")
        # raise ValueError(f"2 missing font: {font} for {dev}")
        return f"Graphics.FONT_{font.upper()}"
    # return if font in FONT_TO_MC_FONT and FONT_TO_MC_FONT[font] != ''
    # return 'Graphics.FONT_' + (FONT_TO_MC_FONT[font] if font in FONT_TO_MC_FONT else font.upper())

def get_most_frequent_value_and_occurrences(dict):
    usages = {}
    for val in dict.values():
        if val not in usages:
            usages[val] = 0
        usages[val] += 1
    arr = []
    for key, val in usages.items():
        arr.append([val, key])
    arr.sort(reverse = True)
    return arr[0][1], arr[0][0]

def get_most_frequent_value(dict):
    return get_most_frequent_value_and_occurrences(dict)[0]

def get_first_most_frequent_value(gen):
    return gen['most_frequent_value'][0] if isinstance(gen['most_frequent_value'], list) else gen['most_frequent_value']

def get_only_value(dict):
    values = set(dict.values())
    return next(iter(values)) if len(values) == 1 else None

JUSTIFICATION_TO_MC = {'right': 'TEXT_JUSTIFY_RIGHT', 'center': 'TEXT_JUSTIFY_CENTER', 'left': 'TEXT_JUSTIFY_LEFT', 'vcenter': 'TEXT_JUSTIFY_VCENTER'}
def justification2mc(justification):
    if justification is False or justification is None:
        return to_mc_value(justification)
    mc_just = JUSTIFICATION_TO_MC[justification]
    if mc_just is None:
        warnings.warn(f"Unknown justification: {justification}")
    return f"Graphics.{mc_just}"


def to_short_field_name(long_name):
    return long_name.replace(' Fields ', '').replace(' Fields', '').replace(' Field', '').replace('[', '.').replace(']', '')


def solve_quadratic(a, b, c):
    # x1,x2 = (-b +- sqrt(b^2 - 4*a*c)) / 2*a
    log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"solve_quadratic(a: {a}, b: {b}, c: {c}): q^2: {b*b - 4*a*c}")
    q = math.sqrt(b*b - 4*a*c)
    return (-b + q) / (2*a), (-b - q) / (2*a)

def intersect_circle_with_horizontal_line(display_h, origo_y, radius, line_y, field_x, field_w, obscurity_flags, \
        obscurity_flags_str, field_y, log_prefix, value_prefix):
    # for the top and bottom horizontal line calculate where they cross the circle
    # distance(origo_x, origo_y, field_x, field_y)
    # circle: x^2 + y^2 = r^2
    # display: (x - ox)^2 + (y - oy)^2 = r^2
    # horizontal line1: y = field_y, line2: y = (field_y + field_h)

    # # (x - ox)^2 + (y - oy)^2 = r^2
    # # (x - ox)^2              = r^2 - (y - oy)^2
    # # x^2 - 2*x*ox + ox^2 = r^2 - (y^2 - 2*y*oy + oy^2) = r^2 - y^2 + 2*y*oy - oy^2
    # # x^2 + (-2*ox)x -(r^2 - y^2 + 2*y*oy - oy^2 - ox^2) = 0
    # # B = -2*ox
    # # C = r^2 - y^2 + 2*y*oy - oy^2 - ox^2
    # # x^2 + B*x = C
    # # x^2 + B*x - C = 0
    # # x^2 + C*x - (C-B)*x - C = 0
    # # x*(x + C) -(C-B)*(x + C) = 0
    # # (x-(C-B))*(x + C) = 0
    # # (x + B-C)*(x + C) = 0
    # # x1 = C - B, x2 = -C
    # # x1 = r^2 - y^2 + 2*y*oy - oy^2 - ox^2 + 2*ox, x2 = - (r^2 - y^2 + 2*y*oy - oy^2 - ox^2)
    # # x1 = r^2 - y*y + y*2*oy - oy^2 - ox^2 + 2*ox, x2 = - r^2 + y^2 - 2*y*oy + oy^2 + ox^2
    # # r = dw/2, oy = dh/2, ox = dw/2
    # # x1 = (dw/2)^2 - y*y + y*2*(dh/2) - (dh/2)^2 - (dw/2)^2 + 2*(dw/2),   x2 = -(dw/2)^2 + y^2 - y*2*(dh/2) + (dh/2)^2 + (dw/2)^2
    # # x1 = (dw/2)^2 - y*y + y*dh - (dh/2)^2 - (dw/2)^2 + dw,   x2 = -(dw/2)^2 + y^2 - y*dh + (dh/2)^2 + (dw/2)^2
    # # dw = dh
    # # x1 = (dw/2)^2 - y*y + y*dh - (dw/2)^2 - (dw/2)^2 + dw,   x2 = -(dw/2)^2 + y^2 - y*dw + (dw/2)^2 + (dw/2)^2
    # # x1 = -y*y + y*dw - (dw/2)^2 + dw,   x2 = y^2 - y*dw + (dw/2)^2
    # # x1 = -y*y + y*dw - (dw/2)^2 + dw,   x2 = -(y*y + y*dw - (dw/2)^2)
    # # x1 = y*dw - y*y - (dw/2)^2 + dw,   x2 = -(y*y + y*dw - (dw/2)^2)
    # x1 = -field_y*field_y + display_w*field_y - radius*radius + display_w
    # x2 = -field_y*field_y - display_w*field_y + radius*radius

    # (x - ox)^2 + (y - oy)^2 = r^2
    # (x - ox)^2 + (y - oy)^2 - r^2 = 0
    # (x^2 - 2*ox*x + ox^2) + (y - oy)^2 - r^2 = 0
    # 1*x^2 + (-2*ox)*x + (ox^2 + (y - oy)^2 - r^2) = 0
    # A*x^2 + B*x + C = 0
    # A=1, B=-2*ox, C=ox^2 + (y - oy)^2 - r^2
    # x1,x2 = (-B +- sqrt(B^2 - 4*A*C)) / 2*A
    # x1,x2 = (2*ox +- sqrt(4*ox^2 - 4*(ox^2 + (y - oy)^2 - r^2))) / 2
    # x1,x2 = (2*ox +- sqrt(4*ox^2 - 4*ox^2 - 4*(y - oy)^2 + 4*r^2)) / 2
    # x1,x2 = (2*ox +- sqrt(-4*(y - oy)^2 + 4*r^2)) / 2
    #@ x1,x2 = (2*ox +- sqrt(-4*(y^2 -2*y*oy + oy^2) + 4*r^2)) / 2
    # x1,x2 = (2*ox +- sqrt(4*r^2 - 4*(y - oy)^2)) / 2
    # x1,x2 = (2*ox +- sqrt(4*(r^2 - (y - oy)^2))) / 2
    # x1,x2 = (display_w +- sqrt(4*(radius*radius - (field_y - origo_y)^2))) / 2
    ##@ x1 = (2*ox + sqrt(-4*(y^2 - (2*oy)*y) + 4*r^2)) / 2   ,   x2 = (2*ox - sqrt(-4*(y^2 - (2*oy)*y) + 4*r^2)) / 2

    # q = math.sqrt(4*(radius*radius - (line_y - origo_y)*(line_y - origo_y)))
    # x1 = int((display_h + q) / 2)
    # x2 = int((display_h - q) / 2)
    # C = ox^2 + (y - oy)^2 - r^2 = ox^2 + y^2 - 2*oy*y + oy^2 - r^2 = origo_y*origo_y + (y-origo_y)*(y-origo_y) - radius*radius = 
    x1, x2 = solve_quadratic(1, -display_h, origo_y*origo_y + (line_y-origo_y)*(line_y-origo_y) - radius*radius)
    inside_field = []
    if field_x <= x1 and x1 <= field_x + field_w:
        inside_field.append(int(x1))
    if field_x <= x2 and x2 <= field_x + field_w:
        inside_field.append(int(x2))
    bounding_box_x = max(field_x, min(inside_field)) if obscurity_flags & OBSCURITY_TO_NUMBER['left'] and inside_field else field_x
    bounding_box_w = min(field_x + field_w, max(inside_field)) - bounding_box_x if obscurity_flags & OBSCURITY_TO_NUMBER['right'] and inside_field else field_w
    print_warn_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{log_prefix}: obscurity_flags: {obscurity_flags_str}({obscurity_flags}), inside_field: {inside_field}, field_x: {field_x}, field_y: {field_y}, field_w: {field_w}, r: {radius}, x1: {'%.2f' % x1}, x2: {'%.2f' % x2}, min: {'%.2f' % min(inside_field) if inside_field else '-'}, max: {'%.2f' % max(inside_field) if inside_field else '-'} => {value_prefix}_x: {'%.2f' % bounding_box_x}, {value_prefix}_w: {'%.2f' % bounding_box_w}")
    return bounding_box_x, bounding_box_w

# def intersect_circle_with_line(display_h, origo_y, radius, line_slope, line_y):
#     x1, x2 = solve_quadratic(1 + line_slope*line_slope, -2*origo_y + 2 * line_slope * (line_y - origo_y), origo_y*origo_y + line_y*line_y - 2*line_y*origo_y + origo_y*origo_y - radius*radius) # + origo_y*origo_y - radius*radius)
#     y1 = line_slope * x1 + line_y
#     y2 = line_slope * x2 + line_y

def intersect_circle_with_line_in_field(display_h, origo_y, radius, line_slope, line_y, field_x, field_y, field_w, field_h, obscurity_flags, \
        obscurity_flags_str, log_prefix, value_prefix):
    # for the top and bottom horizontal line calculate where they cross the circle
    # distance(origo_x, origo_y, field_x, field_y)
    # circle: x^2 + y^2 = r^2
    # display: (x - ox)^2 + (y - oy)^2 = r^2
    ## horizontal line1: y = field_y, line2: y = (field_y + field_h)
    # generic line: y = line_slope * x + line_y

    # circle: (x - ox)^2 + (y - oy)^2 = r^2
    # circle: (x - ox)^2 + (y - oy)^2 - r^2 = 0
    # circle: (x^2 - 2*ox*x + ox^2) + (y - oy)^2 - r^2 = 0
    # circle: 1*x^2 + (-2*ox)*x + (ox^2 + (y - oy)^2 - r^2) = 0
    # intersection: 1*x^2 + (-2*ox)*x + (ox^2 + (line_slope * x + line_y - oy)^2 - r^2) = 0
    # intersection: 1*x^2 + (-2*ox)*x + (ox^2 + (line_slope^2 * x^2 + 2 * line_slope * x * (line_y - oy) + (line_y - oy)^2) - r^2) = 0
    # intersection: 1*x^2 + (-2*ox)*x + (ox^2 + (line_slope^2 * x^2 + 2 * line_slope * x * (line_y - oy) + (line_y^2 - 2*line_y*oy + oy^2)) - r^2) = 0
    # intersection: 1*x^2 + (-2*ox)*x + ox^2 + line_slope^2 * x^2 + 2 * line_slope * (line_y - oy) * x + line_y^2 - 2*line_y*oy + oy^2 - r^2 = 0
    # intersection: (1 + line_slope^2) * x^2 + (-2*ox + 2 * line_slope * (line_y - oy)) * x + (ox^2 + line_y^2 - 2*line_y*oy + oy^2 - r^2) = 0
    # intersection: (1 + line_slope^2) * x^2 + (-2*ox + 2 * line_slope * (line_y - oy)) * x + (ox^2 + line_y^2 - 2*line_y*oy) = 0
    # A*x^2 + B*x + C = 0
    # x1,x2 = (-B +- sqrt(B^2 - 4*A*C)) / 2*A
    # A=1 + line_slope^2, B=-2*ox + 2 * line_slope * (line_y - oy), C=ox^2 + line_y^2 - 2*line_y*oy
    # x1,x2 = (2*ox - 2 * line_slope * (line_y - oy) +- sqrt((-2*ox + 2 * line_slope * (line_y - oy))^2 - 4*(1 + line_slope^2)*(ox^2 + line_y^2 - 2*line_y*oy))) / 2 * (1 + line_slope^2)


    # q = math.sqrt(4*(radius*radius - (line_y - origo_y)*(line_y - origo_y)))
    # x1 = int((display_h + q) / 2)
    # x2 = int((display_h - q) / 2)
    x1, x2 = solve_quadratic(1 + line_slope*line_slope, -2*origo_y + 2 * line_slope * (line_y - origo_y),
        origo_y*origo_y + line_y*line_y - 2*line_y*origo_y + origo_y*origo_y - radius*radius) # + origo_y*origo_y - radius*radius)
    y1 = line_slope * x1 + line_y
    y2 = line_slope * x2 + line_y
    inside_field = []
    if field_x <= x1 and x1 <= field_x + field_w and field_y <= y1 and y1 <= field_y + field_h:
        inside_field.append(int(x1))
    if field_x <= x2 and x2 <= field_x + field_w and field_y <= y2 and y2 <= field_y + field_h:
        inside_field.append(int(x2))
    bounding_box_x = max(field_x, min(inside_field)) if obscurity_flags & OBSCURITY_TO_NUMBER['left'] and inside_field else field_x
    bounding_box_w = min(field_x + field_w, max(inside_field)) - bounding_box_x if obscurity_flags & OBSCURITY_TO_NUMBER['right'] and inside_field else field_w
    print_warn_log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"intersect_circle_with_line_in_field: {log_prefix}: obscurity_flags: {obscurity_flags_str}({obscurity_flags}), inside_field: {inside_field}, field_x: {field_x}, field_y: {field_y}, field_w: {field_w}, r: {radius}, line_slope: {'%.2f' % line_slope}, line_y: {line_y}, x1: {'%.2f' % x1}, x2: {'%.2f' % x2}, min: {'%.2f' % min(inside_field) if inside_field else '-'}, max: {'%.2f' % max(inside_field) if inside_field else '-'} => {value_prefix}_x: {'%.2f' % bounding_box_x}, {value_prefix}_w: {'%.2f' % bounding_box_w}")
    return bounding_box_x, bounding_box_w

# TODO: generate bounding_box(x, y, w, h) relative to dc for "worst case" (i.e: 7.1|7.4|8.1|8.3|8.5 194x82@l => bounding_box: [30, 0, 164,82]) using the data in simulator.json
# 1. calculate the conflictng fields (aka datafield_detector)
# 2. calculate which one is the "worst" (smallest w, smallest h) using field['location'], field['obscurity']
# 3. calculate the position and size of the bounding_box
# 4. retrieve and write to mc file: bounding_box_x, bounding_box_y, bounding_box_w, bounding_box_h
#    'bounding_box_x': get_datafield_hash_data_values(dev, 'bounding_box_x', lambda field: field['location']['x'], max_delta, log_level = log_level),
def calculate_bounding_box(dev, field, resolution):
    display_w = resolution['width']
    display_h = resolution['height']
    origo_x = int(display_w / 2)
    origo_y = int(display_h / 2)
    radius = int(display_h / 2)

    quarter_box_side = int(math.sqrt(radius*radius/2)) # 2*s^2=r^2 s=sqrt(r^2/2)

    field_x = field['location']['x']
    field_y = field['location']['y']
    field_w = field['location']['width']
    field_h = field['location']['height']

    bounding_box_x = field_x
    bounding_box_y = field_y
    bounding_box_w = field_w
    bounding_box_h = field_h

    obscurity_flags = field2obscurity_flags_int(field)
    obscurity_flags_str = field2obscurity_flags_str(field)
    # OBSCURITY_TO_NUMBER = {'left': 1, 'top': 2, 'right': 4, 'bottom': 8}
    match obscurity_flags:
        case 1 | 4 | 5:
        # case 1: "l", // left: middle-left field
        # case 4: # "r", // right: middle-right field
        # case 5: # "rl", // right-left: middle, full width field on round screen
            # # calculate where the top edge of the field intersects the circle
            # y = field_y
            # bounding_box_top_x, bounding_box_top_w = intersect_circle_with_horizontal_line(display_h, origo_y, radius, field_y, field_x, field_w, obscurity_flags, obscurity_flags_str, field_y, f"calculate_bounding_box: {field['gen']['short_name']}", 'bounding_box_top')
            bounding_box_top_x, bounding_box_top_w = intersect_circle_with_line_in_field(display_h, origo_y, radius, 0, field_y, field_x, field_y, field_w, field_h, obscurity_flags, obscurity_flags_str, f"calculate_bounding_box: {field['gen']['short_name']}", 'bounding_box_top')

            # # calculate where the bottom edge of the field intersects the circle
            # y = field_y + field_h
            # bounding_box_bottom_x, bounding_box_bottom_w = intersect_circle_with_horizontal_line(display_h, origo_y, radius, field_y + field_h, field_x, field_w, obscurity_flags, obscurity_flags_str, field_y, f"calculate_bounding_box: {field['gen']['short_name']}", 'bounding_box_bottom')
            bounding_box_bottom_x, bounding_box_bottom_w = intersect_circle_with_line_in_field(display_h, origo_y, radius, 0, field_y + field_h, field_x, field_y, field_w, field_h, obscurity_flags, obscurity_flags_str, f"calculate_bounding_box: {field['gen']['short_name']}", 'bounding_box_bottom')

            bounding_box_x = int(max(bounding_box_top_x, bounding_box_bottom_x))
            bounding_box_w = int(min(bounding_box_top_w, bounding_box_bottom_w))

            if field_x != bounding_box_x or field_w != bounding_box_w:
                # print_warn_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"calculate_bounding_box: {field['gen']['short_name']}: bounding_box_top_x: {bounding_box_top_x}, bounding_box_bottom_x: {bounding_box_bottom_x}")
                print_warn_log(LOG_LEVEL, LOG_LEVEL_INPUT, f"calculate_bounding_box: {field['gen']['short_name']}: bounding_box_x: {field_x} => {bounding_box_x}, bounding_box_w: {field_w} => {bounding_box_w}")
            else:
                log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"calculate_bounding_box: {field['gen']['short_name']}: bounding_box_x: {field_x} => {bounding_box_x}, bounding_box_w: {field_w} => {bounding_box_w}")

        case 7: # "rtl", // right-top-left: top-arc | top-half
            # # sx/sy=field_w/field_h, sx^2+sy^2=r^2 ; sy=field_w/(field_h*sx) ; sx^2+(field_w/(field_h*sx))^2=r^2 ; sx^2+(fw^2/fh^2/sx^2)=r^2 ; sx!=0 | sx^4+fw^2/fh^2-r^2*sx^2=0
            # # x1,x2 = (-B +- sqrt(B^2 - 4*A*C)) / 2*A
            # # (sx^2)^2-r^2*(sx^2)+fw^2/fh^2=0 ; A=1,B=-r^2,C=fw^2/fh^2 ; (sx^2)1,2 = (r^2 +- sqrt(r^4-4*fw^2/fh^2)) / 2
            # # (sx^2)1 = (r^2 + sqrt(r^4-4*fw^2/fh^2)) / 2, (sx^2)2 = (r^2 - sqrt(r^4-4*fw^2/fh^2)) / 2
            # # sx1 = sqrt((r^2 + sqrt(r^4-4*fw^2/fh^2)) / 2), sx2 = sqrt((r^2 - sqrt(r^4-4*fw^2/fh^2)) / 2)
            # r2 = radius*radius
            # b = math.sqrt(r2*r2 - 4 * field_w * field_w / (field_h * field_h))
            # sx1 = math.sqrt((r2 + b) / 2)
            # sy1 = field_w / (field_h * sx1)
            # if (r2 >- b):
            #     sx2 = math.sqrt((r2 - b) / 2)
            #     sy2 = field_w / (field_h * sx2)
            #     bounding_box_x, bounding_box_w = intersect_circle_with_horizontal_line(display_h, origo_y, radius, sy2, field_x, field_w, obscurity_flags, obscurity_flags_str, field_y, f"calculate_bounding_box: {field['gen']['short_name']}", 'bounding_box_sy2')

            # line: y = field_h/(field_w/2)*x + 0 ; -field_h/(field_w/2)*x + 2 * (field_y+field_h)
            bounding_box_x, bounding_box_w = intersect_circle_with_line_in_field(display_h, origo_y, radius, field_h / (field_w / 2), 0, field_x, field_y, field_w, field_h, obscurity_flags, obscurity_flags_str, f"calculate_bounding_box: {field['gen']['short_name']}", 'bounding_box')
            bounding_box_x2, bounding_box_w = intersect_circle_with_line_in_field(display_h, origo_y, radius, -field_h / (field_w / 2), 2 * (field_y + field_h), field_x, field_y, field_w, field_h, obscurity_flags, obscurity_flags_str, f"calculate_bounding_box: {field['gen']['short_name']}", 'bounding_box')
            bounding_box_w = bounding_box_x2 - bounding_box_x
            bounding_box_y = int((field_h / (field_w / 2)) * (field_x + bounding_box_x)) + 0
            bounding_box_h = field_h - bounding_box_y
            log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"calculate_bounding_box: {field['gen']['short_name']}: bounding_box_x: {'%.2f' % bounding_box_x}, bounding_box_y: {'%.2f' % bounding_box_y}, bounding_box_w: {'%.2f' % bounding_box_w}, bounding_box_h: {'%.2f' % bounding_box_h}")

        case 13: # "brl", // bottom-right-left: bottom-arc | bottom-half
            # line: y = field_h/(field_w/2)*x + display_h - 2 * (field_h) ; -field_h/(field_w/2)*x + display_h
            bounding_box_x, bounding_box_w = intersect_circle_with_line_in_field(display_h, origo_y, radius, -field_h / (field_w / 2), display_h, field_x, field_y, field_w, field_h, obscurity_flags, obscurity_flags_str, f"calculate_bounding_box: {field['gen']['short_name']}", 'bounding_box')
            bounding_box_x2, bounding_box_w = intersect_circle_with_line_in_field(display_h, origo_y, radius, field_h / (field_w / 2), display_h -2 * (field_h), field_x, field_y, field_w, field_h, obscurity_flags, obscurity_flags_str, f"calculate_bounding_box: {field['gen']['short_name']}", 'bounding_box')
            bounding_box_w = bounding_box_x2 - bounding_box_x
            bounding_box_h = int((-field_h / (field_w / 2)) * (bounding_box_x)) + display_h - field_y
            log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"calculate_bounding_box: {field['gen']['short_name']}: bounding_box_x: {'%.2f' % bounding_box_x}, bounding_box_y: {'%.2f' % bounding_box_y}, bounding_box_w: {'%.2f' % bounding_box_w}, bounding_box_h: {'%.2f' % bounding_box_h}")

        case 3: # "tl", // top-left: top-left-arc
            bounding_box_x = origo_x - quarter_box_side
            bounding_box_y = origo_y - quarter_box_side
            bounding_box_w = quarter_box_side
            bounding_box_h = quarter_box_side
        case 6: # "rt", // right-top: top-right-arc
            bounding_box_x = origo_x
            bounding_box_y = origo_y - quarter_box_side
            bounding_box_w = quarter_box_side
            bounding_box_h = quarter_box_side
        case 9: # "bl", // bottom-left: bottom-left-arc
            bounding_box_x = origo_x - quarter_box_side
            bounding_box_y = origo_y
            bounding_box_w = quarter_box_side
            bounding_box_h = quarter_box_side
        case 12: # "br", // bottom-right: bottom-right-arc
            bounding_box_x = origo_x
            bounding_box_y = origo_y
            bounding_box_w = quarter_box_side
            bounding_box_h = quarter_box_side
        case 15: # "brtl", // bottom-right-top-left: full-screen field on round device
            bounding_box_x = origo_x - quarter_box_side
            bounding_box_y = origo_y - quarter_box_side
            bounding_box_w = 2 * quarter_box_side
            bounding_box_h = 2 * quarter_box_side

        case 0: # "", no obscurity: rectangle field, IMHO can't exist on round device but can on semi-octagon
            x = 0 # noop
        # # case 2: # "t", // top: IMHO can't exist
        # # case 8: # "b", // bottom: IMHO can't exist
        # # case 10: # "bt", // bottom-top: IMHO can't exist
        # # case 11: # "btl", // bottom-top-left: IMHO can't exist
        # # case 14: # "brt", // bottom-right-top: IMHO can't exist
        case _:
            print_error(f"{dev}: calculate_bounding_boxes: unknown obscurity_flags on round device in field:{field['gen']['short_name']}: {obscurity_flags_str}({obscurity_flags})")
    # convert absolute coordinates to relative to the field
    return {'x': bounding_box_x - field_x, 'y': bounding_box_y - field_y, 'width': bounding_box_w, 'height': bounding_box_h}

def calculate_bounding_boxes(dev):
    device = DEVICES[dev]
    shape = device['simulator']['display']['shape']
    location = device['simulator']['display']['location']
    resolution = device['compiler']['resolution']
    if shape == 'round' and resolution['width'] != resolution['height']:
        print_error(f"{dev}: compiler.resolution: width: {resolution['width']} != height: {resolution['height']}")
    if resolution['width'] != location['width'] or resolution['height'] != location['height']:
        print_error(f"{dev}: compiler.resolution: {resolution} != simulator.display.location: {location}")
    log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: calculate_bounding_boxes: shape: {shape}, resolution: {resolution}, location: {location}")

    for layout in device['simulator']['layouts']:
        for datafield in layout['datafields']['datafields']:
            for field in datafield['fields']:
                if 'func' not in field['gen']:
                    field['gen']['func'] = {}
                if 'bounding_box' not in field['gen']['func']:
                    field['gen']['func']['bounding_box'] = {}
                gen = field['gen']['func']['bounding_box']
                gen['display_shape'] = shape

                match shape:
                    case 'rectangle':
                        obscurity_flags = field2obscurity_flags_int(field)
                        if obscurity_flags != 0:
                            print_error(f"{dev}: calculate_bounding_boxes: unknown obscurity_flags on rectangle device in field:{field['gen']['short_name']}: {obscurity_flags}")
                        gen.update(field['location'])
                    case 'round' | 'semi-round' | 'semi-octagon':
                        gen.update(calculate_bounding_box(dev, field, resolution))
                    case _:
                        print_error(f"{dev}: calculate_bounding_boxes: unknown display shape: {shape}")
                # log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"calculate_bounding_boxes: {field['gen']['short_name']}: location: {field['location']}")
                # log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"calculate_bounding_boxes: {field['gen']['short_name']}: {gen}")
    # log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"calculate_bounding_boxes: {hash2bounding_box}")

def datafield_layout(dev):
    if dev == 'base':
        return ['', '', '']

    device = DEVICES[dev]
    if 'layouts' not in device['simulator']:
        print_error(f"{dev}: no layouts")
        return ['', '', '']

    calculate_bounding_boxes(dev)

    max_delta = 3
    log_level = LOG_LEVEL
    # log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"datafield_layout: {dev}")
    # log(log_level, LOG_LEVEL_OUTPUT, f"{dev}:")
    result = {
        'label_font': get_datafield_hash_data_font_values(dev, 'label_font', lambda field: field['label']['font'] if has_label(field) else False, log_level = log_level),
        'label_x': get_datafield_hash_data_values(dev, 'label_x', 'min', lambda field: field['label']['x'] if has_label(field) else False, max_delta, log_level = log_level),
        'label_y': get_datafield_hash_data_values(dev, 'label_y', 'min', lambda field: field['label']['y'] if has_label(field) else False, max_delta, log_level = log_level),
        'label_justification': get_datafield_hash_data_justification_values(dev, 'label_justification', lambda field: field['label']['justification'] if has_label(field) else False, log_level = log_level),
        'data_x': get_datafield_hash_data_values(dev, 'data_x', 'min', lambda field: field['data']['x'], max_delta, log_level = log_level),
        'data_y': get_datafield_hash_data_values(dev, 'data_y', 'min', lambda field: field['data']['y'], max_delta, log_level = log_level),
        'data_justification': get_datafield_hash_data_justification_values(dev, 'data_justification', lambda field: field['data']['justification'], log_level = log_level),
        'bounding_box_x': get_datafield_hash_data_values(dev, 'bounding_box_x', 'max', lambda field: field['gen']['func']['bounding_box']['x'], max_delta = 1000, log_level = log_level),
        'bounding_box_y': get_datafield_hash_data_values(dev, 'bounding_box_y', 'max', lambda field: field['gen']['func']['bounding_box']['y'], max_delta = 1000, log_level = log_level),
        'bounding_box_width': get_datafield_hash_data_values(dev, 'bounding_box_width', 'min', lambda field: field['gen']['func']['bounding_box']['width'], max_delta = 1000, log_level = log_level),
        'bounding_box_height': get_datafield_hash_data_values(dev, 'bounding_box_height', 'min', lambda field: field['gen']['func']['bounding_box']['height'], max_delta = 1000, log_level = log_level),
    }

    increase_hebrew_label_font = False
    prefix = ''
    if 'heb' in device['languages']:
        fontSet = None
        # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}::")
        for partNumber in device['compiler']['partNumbers']:
            lng = list(filter(lambda lang: lang['code'] == 'heb', partNumber['languages']))
            # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {partNumber['number']} {lng}")
            if len(lng) > 0:
                lang = lng[0]
                fontSet = lang['fontSet']
                # default_label_font_font = next(font for font in next(fonts for fonts in device['simulator']['fonts'] if fonts['fontSet'] == fontSet)['fonts'] if font['name'] == default_label_font)
                default_label_font_font = next(font for font in next(fonts for fonts in device['simulator']['fonts'] if fonts['fontSet'] == fontSet)['fonts'] if font2mc_font(font['name'], dev) == result['label_font']['most_frequent_value'])
                increase_hebrew_label_font = '_CDPG_ROBOTO_13B' in default_label_font_font['filename']
        # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {default_label_font_font['filename']}, increase_hebrew_label_font: {increase_hebrew_label_font}")

        prefix = f"(:datafield, :hebrew) const INCREASE_HEBREW_LABEL_FONT_SIZE = {'true' if increase_hebrew_label_font else 'false'};\n"

    generate_datafield_file(dev, 'datafield_layout.mc', result, prefix)

    sourceDirs = list(filter(None, [has_directory(f"{GENERATED_FEATURES_DIR}/datafield_layout"), has_directory(f"{GENERATED_DEVICES_DIR}/{dev}")]))
    return [';'.join(sourceDirs), '', '']
pre_register(datafield_layout, 'datafield_layout', dependencies=['languages'])


def datafield_detector(dev):
    if dev == 'base':
        return ['', '', '']

    device = DEVICES[dev]
    if 'display' not in device['simulator']:
        log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: no display shape")
        return ['', '', '']
    # is_rectangle = False
    # if device['simulator']['display']['shape'] == 'rectangle':
    #     is_rectangle = True
    #     print_warn(f"{dev}: datafield_detector: rectangle display");
    #     # sourceDirs = list(filter(None, [has_directory(f"{GENERATED_FEATURES_DIR}/rectangle"), has_directory(f"{GENERATED_DEVICES_DIR}/{dev}")]))
    #     # return [';'.join(sourceDirs), '', '']
    if 'layouts' not in device['simulator']:
        log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: no layouts")
        return ['', '', '']

    device_hash2layouts = {}
    for layout in device['simulator']['layouts']:
        for datafield in layout['datafields']['datafields']:
            layout_short_name = datafield['gen']['short_name']
            layout_status = 0
            for field in datafield['fields']:
                hash = field['gen']['hash']
                if hash not in device_hash2layouts:
                    device_hash2layouts[hash] = {}
                if layout_short_name not in device_hash2layouts[hash]:
                    device_hash2layouts[hash][layout_short_name] = []
                device_hash2layouts[hash][layout_short_name].append(field['gen']['short_name'])
    device_hash2statuses = {}
    for hash in device_hash2layouts:
        layouts = device_hash2layouts[hash]
        for layout_short_name in layouts:
            field_short_names = layouts[layout_short_name]
            if len(field_short_names) == 1:
                if len(layouts) == 1:
                    field_status = 0
                else:
                    field_status = 1
            else:
                field_status = 3
            if hash not in device_hash2statuses:
                device_hash2statuses[hash] = []
            device_hash2statuses[hash].append(field_status)

    hash_status_field_status_matrix = [
        # field_status:  0, 1, 2, 3
                        [0, 1, 4, 2], # hash_status: 0
                        [1, 1, 5, 2], # hash_status: 1
                        [2, 2, 6, 2], # hash_status: 2
                        [2, 2, 7, 3]  # hash_status: 3
        # note: outputs > 3 are not possible, and are there to detect errors
    ]
    device_hash2status = {}
    device_status = 0
    for hash in device_hash2statuses:
        hash_status = 0
        for field_status in device_hash2statuses[hash]:
            hash_status = hash_status_field_status_matrix[hash_status][field_status]
            if hash_status > 3:
                print_error(f"{dev}: datafield_detector: invalid status for hash: {hash}");
            device_status = hash_status_field_status_matrix[device_status][field_status]
            if device_status > 3:
                print_error(f"{dev}: datafield_detector: invalid status for device");
        device_hash2status[hash] = hash_status

    log_level = LOG_LEVEL
    # log(log_level, LOG_LEVEL_OUTPUT, f"{dev}:")
    result = {
        'field_names': get_datafield_hash_data_values(dev, 'field_names', 'concat', lambda field: field['gen']['short_name'], log_level = log_level),
        'field_status': get_datafield_hash_data_values(dev, 'field_status', 'min', lambda field: device_hash2status[field['gen']['hash']], log_level = log_level),
    }

    postfix = "(:datafield_detector)\n" + \
        f"const DEVICE_STATUS = {device_status};\n"
    generate_datafield_file(dev, 'datafield_detector.mc', result, '', postfix)

    sourceDirs = list(filter(None, [has_directory(f"{GENERATED_DEVICES_DIR}/common"), has_directory(f"{GENERATED_DEVICES_DIR}/{dev}")]))
    return [';'.join(sourceDirs), '', '']
pre_register(datafield_detector)


COMMON_TYPE = ' or Null'
COMMON_LABEL_TYPE = ' or Null or Boolean'
DICTIONARY_VALUE_TYPE = {
    'label_font': 'Graphics.FontDefinition' + COMMON_LABEL_TYPE,
    'label_x': 'Number' + COMMON_LABEL_TYPE,
    'label_y': 'Number' + COMMON_LABEL_TYPE,
    'label_justification': 'Number' + COMMON_LABEL_TYPE,
    'data_x': 'Number' + COMMON_TYPE,
    'data_y': 'Number' + COMMON_TYPE,
    'data_justification': 'Number' + COMMON_TYPE,
    'field_names': 'String',
    'field_status': 'Number',
    'bounding_box_x': 'Number' + COMMON_TYPE,
    'bounding_box_y': 'Number' + COMMON_TYPE,
    'bounding_box_width': 'Number' + COMMON_TYPE,
    'bounding_box_height': 'Number' + COMMON_TYPE,
}

def generate_datafield_file(dev, filename, result, prefix = '', postfix = ''):
    device_dir = f"{GENERATED_DEVICES_DIR}/{dev}"
    device_file = f"{device_dir}/{filename}"
    os.makedirs(device_dir, 0o755, True)
    with open(device_file, 'w') as output:
        # output.write(f"// GENERATED for {dev} by {GENERATROR_SIGNATURE}\n\n");
        output.write(f"// GENERATED by {GENERATROR_SIGNATURE}\n\n")
        output.write("import Toybox.Lang;\n")
        output.write("import Toybox.Graphics;\n\n")

        if USE_MODULES:
            output.write("module Flocsy {\n")
            output.write("\tmodule DataFieldLayout {\n\n")

        output.write(prefix)

        for key in result:
            gen = result[key]
            KEY = key.upper()
            default_value = to_mc_value(get_first_most_frequent_value(gen))
            output.write(f"(:datafield, :datafield_hash, :datafield_{key}) const DEFAULT_{KEY} = {default_value}; // {destring_arr_values(to_mc_value(gen['most_frequent_value'])) + ' ' if isinstance(gen['most_frequent_value'], list) else ''}x{gen['most_frequent_value_count']}\n")
            # if key.endswith('_justification'):
            #     output.write(f"(:datafield, :datafield_hash, :datafield_{key}) const HAS_DATAFIELD_HASH_2_{KEY} = {'false' if gen['default_value'] is not None else 'true'};\n")
            output.write(f"(:datafield, :datafield_hash, :datafield_{key}) const DATAFIELD_HASH_2_{KEY} = {{\n")
            for hash in gen['hash_map']:
                hash_obj = gen['hash_map'][hash]
                value = to_mc_value(hash_obj['value'])
                if value != default_value:
                    output.write(f"\t{hash} /*{hash_obj['hash_key']}*/ => {value}, // {destring_arr_dict_values(hash_obj['field_values'])}\n")
                else:
                    output.write(f"\t// {hash} /*{hash_obj['hash_key']}*/ => {value} /*default*/, // {destring_arr_dict_values(hash_obj['field_values'])}\n")
            output.write(f"}} as Dictionary<Number, {DICTIONARY_VALUE_TYPE[key]}>;\n\n")

        output.write(postfix)

        if USE_MODULES:
            output.write("\t}\n")
            output.write("}\n")


def read_datafield_hash_data(dev):
    log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"read_datafield_hash_data: {dev}")
    if dev == 'base':
        return

    device = DEVICES[dev]
    if 'layouts' not in device['simulator']:
        print_error(f"read_device_hash_data: {dev}: no layouts")
        return

    hash2hash_key = {}
    hash2fields = {}
    hash2layouts = {}
    hash2field_names = {}
    hash2status = {}

    for layout in device['simulator']['layouts']:
        for datafield in layout['datafields']['datafields']:
            layout_hash2field_names = {}
            layout_name = datafield['name']
            # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"layout: {layout_name}")
            layout_dict = {
                'long_name': layout_name,
                'short_name': to_short_field_name(layout_name),
                # 'status': 0
            }
            datafield['gen'] = layout_dict
            field_idx = 0
            field = '' # here to be able to capture field in except:
            try:
                for field_idx, field in enumerate(datafield['fields']):
                    gen = {}
                    field['gen'] = gen
                    field_name = f"{layout_name}[{field_idx}]"
                    short_field_name = to_short_field_name(field_name)
                    gen['long_name'] = field_name
                    gen['short_name'] = short_field_name
                    location = field['location']
                    # obs = sorted(field['obscurity'])
                    # o = ''
                    # obscurity_flags = 0
                    # for side in obs:
                    #     o += side[0]
                    #     obscurity_flags |= OBSCURITY_TO_NUMBER[side]
                    # obscurity_flags = field2obscurity_flags_int(field)
                    hash = field2hash(field)
                    o = field2obscurity_flags_str(field)
                    # long_key = f"{hash}:{location['width']}:{location['height']}:{obscurity_flags}:{o}"
                    hash_key = f"{location['width']}x{location['height']}@{o}"
                    gen['hash_key'] = hash_key
                    gen['hash'] = hash

                    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"field: {field}")
                    hash2hash_key[hash] = hash_key
                    if hash not in hash2fields:
                        hash2fields[hash] = []
                        hash2field_names[hash] = []
                        hash2layouts[hash] = []
                    # else:
                    #     if layout_dict['status'] < 1:
                    #         layout_dict['status'] = 1
                    hash2fields[hash].append(field)
                    hash2field_names[hash].append(short_field_name)
                    if layout_dict not in hash2layouts[hash]:
                        hash2layouts[hash].append(layout_dict)

                    if hash in layout_hash2field_names:
                        layout_hash2field_names[hash].append(short_field_name)
                        # layout_dict['status'] = 3
                    else:
                        layout_hash2field_names[hash] = [short_field_name]
            except Exception as e:
                sys.exit(f"{COLOR_RED}read_datafield_hash_data: Error: {dev}: {e=} in {field_name}: {field}{COLOR_RESET}")

# status:
#   0: value is known, field inside layout is known, layout is known
#   1: value is known, field inside layout is known, can be multiple layouts
#   2: value is known, can be multiple fields inside layout, layout is known
#   3: value is known, can be multiple fields inside layout, can be multiple layouts

#   0: can be multiple values, can be multiple fields inside layout, layout is known
#   1: can be multiple values, field inside layout is known, can be multiple layouts
#   2: value is known, can be multiple fields inside layout, layout is known
#   3: value is known, can be multiple fields inside layout, can be multiple layouts

#   4: can be multiple values

HashValueStatus = IntEnum('HashValueStatus', ['KNOWN_VALUE', 'UNKNOWN_VALUE'])
LayoutHashStatus = IntEnum('LayoutHashStatus', ['KNOWN_POSITION', 'UNKNOWN_POSITION'])
DeviceHashStatus = IntEnum('DeviceHashStatus', ['KNOWN_POSITION_AND_LAYOUT', 'KNOWN_POSITION_UNKNOWN_LAYOUT', 'UNKNOWN_POSITION_KNOWN_LAYOUT', 'UNKNOWN_POSITION_AND_LAYOUT'])
# LayoutStatus = Enum('LayoutStatus', ['KNOWN_VALUES', 'UNKNOWN_VALUES'])
# DeviceStatus = Enum('DeviceStatus', ['KNOWN_VALUES', 'UNKNOWN_VALUES'])
# HashValueStatus = Enum('HashValueStatus', ['KNOWN_VALUE_POSITION_LAYOUT', 'KNOWN_VALUE_POSITION_UNKNOWN_LAYOUT', 'KNOWN_VALUE_UNKNOWN_POSITION_KNOWN_LAYOUT',
#       'KNOWN_VALUE_UNKNOWN_POSITION_LAYOUT', 'UNKNOWN_VALUE'])
# HashValueStatus = Enum('HashValueStatus', ['KNOWN_VALUE', 'UNKNOWN_VALUE'])
# DeviceHashValueStatus = Enum('DeviceHashValueStatus', ['KNOWN_VALUE', 'UNKNOWN_VALUE'])

def is_numeric_array(arr):
    is_numeric = True
    for o in arr:
        is_numeric &= type(o) == int
    return is_numeric

def get_datafield_hash_data_values(dev, getter_func_name, multiple_values_aggregator, getter_func, max_delta = 0, log_level = LOG_LEVEL):
    # log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"get_datafield_hash_data_values(dev: {dev}, getter_func_name: {getter_func_name}, aggregator: {multiple_values_aggregator}, getter_func: {getter_func}, max_delta: {max_delta}, log_level: {log_level})")
    device = DEVICES[dev]

    # field2value = {}
    device_hash2values = {}
    device_value_counter = {}
    device_value_2_hashes = {}
    device_most_frequent_value_count = 0
    # device_value = None
    # device_status = HashValueStatus.KNOWN_VALUE
    device_hash2field_names = {}
    device_hash2field_values = {}
    hash2hash_key = {}
    layout2status = {}
    layout2value = {}
    log(log_level, LOG_LEVEL_INPUT, f"\t{getter_func_name} input:")
    for layout in device['simulator']['layouts']:
        for datafield in layout['datafields']['datafields']:
            layout_short_name = datafield['gen']['short_name']
            log(log_level, LOG_LEVEL_INPUT, f"\t\tlayout: {layout_short_name}")
            layout_hash2values = {}
            layout_value_counter = {}
            layout_most_frequent_value_count = 0
            layout_most_frequent_value = None
            layout_hash2field_values = {}
            # layout_hash2values = {}
            for field in datafield['fields']:
                hash = field['gen']['hash']
                hash2hash_key[hash] = field['gen']['hash_key']
                field_short_name = field['gen']['short_name']
                # log(log_level, LOG_LEVEL_DEBUG, field)
                value = getter_func(field)

                # field['gen']['value'] = value
                if 'func' not in field['gen']:
                    field['gen']['func'] = {}
                if getter_func_name not in field['gen']['func']:
                    field['gen']['func'][getter_func_name] = {}
                gen = field['gen']['func'][getter_func_name]
                gen['value'] = value

                # field2value[field_short_name] = value
                log(log_level, LOG_LEVEL_INPUT, f"\t\t\tfield: {field_short_name} ({hash}): {getter_func_name}: {value}")

                if hash not in layout_hash2values:
                    layout_hash2values[hash] = []
                if value not in layout_hash2values[hash]:
                    layout_hash2values[hash].append(value)
                if value not in layout_value_counter:
                    layout_value_counter[value] = 0
                layout_value_counter[value] += 1
                if layout_value_counter[value] > layout_most_frequent_value_count:
                    layout_most_frequent_value = value
                    layout_most_frequent_value_count = layout_value_counter[value]

                if hash not in device_hash2values:
                    device_hash2values[hash] = []
                if value not in device_hash2values[hash]:
                    device_hash2values[hash].append(value)

                if value not in device_value_2_hashes:
                    device_value_2_hashes[value] = set()
                device_value_2_hashes[value].add(hash)

                # if value not in device_value_counter:
                #     device_value_counter[value] = 0
                # device_value_counter[value] += 1
                device_value_counter[value] = len(device_value_2_hashes[value])
                if device_value_counter[value] > device_most_frequent_value_count:
                    device_most_frequent_value_count = device_value_counter[value]

                if hash not in layout_hash2field_values:
                    layout_hash2field_values[hash] = []
                layout_hash2field_values[hash].append({field_short_name: value})
                gen['fields_with_same_hash_in_layout'] = layout_hash2field_values[hash]
                if hash not in device_hash2field_names:
                    device_hash2field_names[hash] = []
                device_hash2field_names[hash].append(field_short_name)
                if hash not in device_hash2field_values:
                    device_hash2field_values[hash] = []
                device_hash2field_values[hash].append({field_short_name: value})

            layout_value = False
            layout_status = HashValueStatus.KNOWN_VALUE
            layout_hash2status = {}
            for hash in layout_hash2values:
                hash_status = HashValueStatus.KNOWN_VALUE
                number_of_values_for_hash = len(layout_hash2values[hash])
                if number_of_values_for_hash > 1:
                    hash_status = HashValueStatus.UNKNOWN_VALUE
                layout_hash2status[hash] = hash_status

                if layout_status == HashValueStatus.KNOWN_VALUE:
                    if number_of_values_for_hash == 1 and (layout_value == layout_hash2values[hash][0] or layout_value == False):
                        layout_value = layout_hash2values[hash][0]
                    else:
                        layout_value = None
                        layout_status = HashValueStatus.UNKNOWN_VALUE
                    # print_error(f"{hash}: number_of_values_for_hash: {number_of_values_for_hash}, layout_value: {layout_value}, layout_hash2values[hash][0]: {layout_hash2values[hash][0]}")
            for field in datafield['fields']:
                hash = field['gen']['hash']
                field['gen']['func'][getter_func_name]['status'] = layout_hash2status[hash]

            if 'func' not in datafield['gen']:
                datafield['gen']['func'] = {}
            if getter_func_name not in datafield['gen']['func']:
                datafield['gen']['func'][getter_func_name] = {}
            gen = datafield['gen']['func'][getter_func_name]
            gen['status'] = layout_status
            gen['value'] = layout_value

            layout2status[layout_short_name] = layout_status
            layout2value[layout_short_name] = layout_value

    device_value = False
    device_status = HashValueStatus.KNOWN_VALUE
    device_hash2status = {}
    device_number_of_None_values = 0
    for hash in device_hash2values:
        hash_value = False
        hash_status = HashValueStatus.KNOWN_VALUE
        number_of_values_for_hash = len(device_hash2values[hash])
        if number_of_values_for_hash == 1:
            hash_value = device_hash2values[hash][0]
        else:
            hash_value = None
            hash_status = HashValueStatus.UNKNOWN_VALUE
            device_number_of_None_values += 1
        device_hash2status[hash] = hash_status
        if device_status == HashValueStatus.KNOWN_VALUE:
            if number_of_values_for_hash == 1 and (device_value == device_hash2values[hash][0] or device_value == False):
                device_value = device_hash2values[hash][0]
            else:
                device_value = None
                device_status = HashValueStatus.UNKNOWN_VALUE

    if log_level >= LOG_LEVEL_PARSING:
        log(log_level, LOG_LEVEL_PARSING, f"\t{getter_func_name} parser:")
        for layout in device['simulator']['layouts']:
            for datafield in layout['datafields']['datafields']:
                layout_short_name = datafield['gen']['short_name']
                # log(log_level, LOG_LEVEL_PARSING, f"\tlayout: {layout_short_name}")
                if layout_most_frequent_value_count > 1:
                    values = []
                    for value in layout_value_counter:
                        count = layout_value_counter[value]
                        if (count == layout_most_frequent_value_count):
                            values.append(value)
                    if is_numeric_array(values):
                        values.sort()
                    log(log_level, LOG_LEVEL_PARSING, f"\t\tlayout: {layout_short_name} ({datafield['gen']['func'][getter_func_name]['status'].name}): {layout_value}, most_frequent_value{'s' if len(values) > 1 else ''}({layout_most_frequent_value_count}x): {values if len(values) > 1 else values[0]}")
                else:
                    log(log_level, LOG_LEVEL_PARSING, f"\t\tlayout: {layout_short_name} ({datafield['gen']['func'][getter_func_name]['status'].name}): {layout_value}")
                for field in datafield['fields']:
                    hash = field['gen']['hash']
                    field_short_name = field['gen']['short_name']
                    # value = getter_func(field)
                    value = field['gen']['func'][getter_func_name]['value']
                    # log(log_level, LOG_LEVEL_PARSING, f"{dev}: {getter_func_name}: layout: {layout_short_name}: {getter_func_name} ({layout_status.name}): {layout_value}")
                    if field['gen']['func'][getter_func_name]['status'] == HashValueStatus.UNKNOWN_VALUE:
                        print_error_log(log_level, LOG_LEVEL_PARSING, f"\t\t\tfield: {field_short_name} ({hash} {field['gen']['hash_key']}): {getter_func_name}: {value} {field['gen']['func'][getter_func_name]['status'].name} {field['gen']['func'][getter_func_name]['fields_with_same_hash_in_layout']}")
                    else:
                        log(log_level, LOG_LEVEL_PARSING, f"\t\t\tfield: {field_short_name} ({hash} {field['gen']['hash_key']}): {getter_func_name}: {value} {field['gen']['func'][getter_func_name]['status'].name} {field['gen']['func'][getter_func_name]['fields_with_same_hash_in_layout']}")

    most_frequent_value_count = device_most_frequent_value_count
    values = []
    for value in device_value_counter:
        count = device_value_counter[value]
        if (count == device_most_frequent_value_count):
            values.append(value)
    values.sort()
    if device_number_of_None_values == device_most_frequent_value_count:
        values.append(None)
        most_frequent_value = values
    elif device_number_of_None_values > device_most_frequent_value_count:
        most_frequent_value = None
        values = [None]
        most_frequent_value_count = device_number_of_None_values
    most_frequent_value = values if len(values) > 1 else values[0]

    hashes = list(device_hash2values.keys())
    hashes.sort()
    result = {
        # 'dev': dev,
        # 'getter_func_name': getter_func_name
        'device_status': device_status,
        'default_value': device_value,
        'most_frequent_value': most_frequent_value,
        'most_frequent_value_count': most_frequent_value_count,
        'hash_map': {}
    }
    for hash in hashes:
        values = device_hash2values[hash]
        result['hash_map'][hash] = {
            'hash': hash,
            'hash_key': hash2hash_key[hash],
            'status': device_hash2status[hash],
            'value': None if len(values) > 1 else values[0],
            'values': values,
            'fields': device_hash2field_names[hash],
            'field_values': device_hash2field_values[hash],
        }
    # log(log_level, LOG_LEVEL_PARSING, f"{dev}: {getter_func_name}: {result}")
    if result['most_frequent_value_count'] > 1:
        log(log_level, LOG_LEVEL_OUTPUT, f"\t{getter_func_name} output: default_{getter_func_name}: {result['default_value']} ({result['device_status'].name}), most_frequent_value{'s' if len(values) > 1 else ''}({result['most_frequent_value_count']}x): {result['most_frequent_value']}")
    else:
        log(log_level, LOG_LEVEL_OUTPUT, f"\t{getter_func_name} output: default_{getter_func_name}: {result['default_value']} ({result['device_status'].name})")
    for hash in hashes:
        hash_map_val = result['hash_map'][hash]
        # log(log_level, LOG_LEVEL_DEBUG, f"{hash_map_val}")
        field_values = hash_map_val['field_values']
        value = hash_map_val['value']
        values = hash_map_val['values']
        dev_prefix = f"{dev}: " if log_level < 2 else ''
        # if len(values) >= LOG_LEVEL_OUTPUT:
        # log(log_level, LOG_LEVEL_PARSING, f"NO_MIN_USED? values: {values}")
        field_short_names = hash_map_val['fields']
        if len(values) > 1:
            if multiple_values_aggregator == 'min' or multiple_values_aggregator == 'max':
                if is_numeric_array(values):
                    min_values = min(values)
                    max_values = max(values)
                    avg_str = '%.2f' % (sum(values)/len(values))
                    delta = max_values - min_values
                    log(log_level, LOG_LEVEL_DEBUG, f"\thash: {hash} ({field_short_names}, {device_hash2status[hash].name}): {getter_func_name}: {f'{values}, min: {min_values}, avg: {avg_str}, max: {max_values}' if len(values) > 1 else values[0]}, aggregator: {multiple_values_aggregator}")
                    if delta > max_delta:
                        print_error_log(log_level, LOG_LEVEL_OUTPUT, f"{dev_prefix}\t\t{hash} ({hash_map_val['hash_key']}) ({hash_map_val['status'].name}): {getter_func_name}: {f'{value}, min: {min_values}, avg: {avg_str}, max: {max_values}'}, delta: {delta} > {max_delta}, aggregator: {multiple_values_aggregator} {field_values}")
                    else:
                        orig_value = hash_map_val['value']
                        hash_map_val['orig_value'] = orig_value
                        if multiple_values_aggregator == 'min':
                            value = f"{min(values)} /*min value*/"
                        elif multiple_values_aggregator == 'max':
                            value = f"{max(values)} /*max value*/"
                        hash_map_val['value'] = value
                        print_warn_log(log_level, LOG_LEVEL_OUTPUT, f"{dev_prefix}\t\t{hash} ({hash_map_val['hash_key']}) ({hash_map_val['status'].name}): {getter_func_name}: {f'{orig_value} -> {value}, min: {min_values}, avg: {avg_str}, max: {max_values}'}, delta: {delta} <= {max_delta}, aggregator: {multiple_values_aggregator} {field_values}")
                else:
                    print_error_log(log_level, LOG_LEVEL_OUTPUT, f"{dev_prefix}\t\t{hash} ({hash_map_val['hash_key']}) ({hash_map_val['status'].name}): {getter_func_name}: {value}, aggregator: {multiple_values_aggregator} {field_values}")
            elif multiple_values_aggregator == 'concat':
                orig_value = hash_map_val['value']
                hash_map_val['orig_value'] = orig_value
                value = '|'.join(values)
                hash_map_val['value'] = value
                log(log_level, LOG_LEVEL_OUTPUT, f"{dev_prefix}\t\t{hash} ({hash_map_val['hash_key']}) ({hash_map_val['status'].name}): {getter_func_name}: {orig_value} -> {value}, aggregator: {multiple_values_aggregator}, {field_values}")
            else:
                print_error(f"{dev_prefix} {getter_func_name}: unknown aggregator: {multiple_values_aggregator}")
        # else:
        #     log(log_level, LOG_LEVEL_OUTPUT, f"\t\t{hash} ({hash_map_val['hash_key']}) ({hash_map_val['status'].name}): {getter_func_name}: {value} {field_values}")
        if multiple_values_aggregator == 'concat':
            hash_map_val['value'] = '"' + escape_mc_string(str(hash_map_val['value'])) + '"'
    return result

def get_datafield_hash_data_font_values(dev, getter_func_name, getter_func, max_delta = 0, log_level = LOG_LEVEL):
    gen = get_datafield_hash_data_values(dev, getter_func_name, 'min', getter_func, max_delta, log_level)
    gen['orig_most_frequent_value'] = gen['most_frequent_value']
    gen['most_frequent_value'] = font2mc_font(get_first_most_frequent_value(gen), dev)
    for hash in gen['hash_map']:
        hash_obj = gen['hash_map'][hash]
        hash_obj['orig_value'] = hash_obj['value']
        hash_obj['value'] = font2mc_font(hash_obj['value'], dev)
    return gen

def get_datafield_hash_data_justification_values(dev, getter_func_name, getter_func, max_delta = 0, log_level = LOG_LEVEL):
    gen = get_datafield_hash_data_values(dev, getter_func_name, 'min', getter_func, max_delta, log_level)
    gen['orig_most_frequent_value'] = gen['most_frequent_value']
    gen['most_frequent_value'] = justification2mc(get_first_most_frequent_value(gen))
    for hash in gen['hash_map']:
        hash_obj = gen['hash_map'][hash]
        hash_obj['orig_value'] = hash_obj['value']
        hash_obj['value'] = justification2mc(hash_obj['value'])
    return gen

def has_label(field):
    return not field['labelDisabled']

def read_devices_datafield_hash_data(devices):
    log(LOG_LEVEL, LOG_LEVEL_DEBUG, "read_devices_datafield_hash_data")
    for dev in devices:
        if dev != 'base':
            read_datafield_hash_data(dev)


def memory_annotations(dev):
    if dev == 'base':
        return ['', '', '']
    device = DEVICES[dev]
    source_path_arr = []
    resource_path_arr = []
    exclude_annotations_arr = []
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
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {minVersion} => {annotations}")
    return ['', '', ';'.join(annotations)]
pre_register(ciq_api)

def is_feature_by_memory(feature):
    for memory_k in FEATURES_BY_MEMORY:
        if feature in FEATURES_BY_MEMORY[memory_k]:
            return True
    return False

def get_features_by_memory(memory_limit):
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
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"MEMORY_ORDER: {MEMORY_ORDER}, MEMORY_2_K: {MEMORY_2_K}, FEATURES_BY_MEMORY: {FEATURES_BY_MEMORY}, memory_k: {memory_k}")
    common_features = FEATURES_BY_MEMORY['common'] if 'common' in FEATURES_BY_MEMORY else []
    memory_features = FEATURES_BY_MEMORY[memory_k] if memory_k in FEATURES_BY_MEMORY else []
    return common_features + memory_features

def copy_gen_directory_if_not_exists(gen_sub_dir):
    conf_base_dir = get_base_dir()
    dst_dir = f"{conf_base_dir}{GENERATED_FEATURES_DIR}/{gen_sub_dir}"
    if not os.path.isdir(dst_dir):
        os.makedirs(GENERATED_FEATURES_DIR, 0o755, True)
        src_dir = f"{FEATURES_SRC_DIR}/{gen_sub_dir}"
        log(LOG_LEVEL, LOG_LEVEL_BASIC, f"copying {src_dir} to {dst_dir}")
        shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns('*.*-'))

def has_directory(dir):
    return dir if os.path.isdir(dir) else ''
    # return dir.replace('+', '\+') if os.path.isdir(dir) else ''

def versiontuple(v):
    return tuple(map(int, (v.split("."))))


def get_multi_feature_dirs(dev, features_dir, base_dir, features):
    base_dir_path = f"{features_dir}{base_dir}"
    multi_feature_dirs = sorted(filter(lambda dir: MULTI_FEATURE_DIR_SEPARATOR in dir, os.listdir(base_dir_path))) if os.path.isdir(base_dir_path) else []
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: multi_feature_dirs in {base_dir_path}: {multi_feature_dirs}")

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
            # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: checking: {feature}")
            if feature not in features:
                add_dir = False
                break
        if add_dir:
            # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: adding: {multi_feature_dir}")
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
        #     log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: not adding directory: {feature}{MULTI_FEATURE_DIR_SEPARATOR}")
    if multi_dirs:
        log(LOG_LEVEL, LOG_LEVEL_OUTPUT, f"{dev}: multi_dirs in {base_dir_path}: {multi_dirs}")
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
        # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {potential_dir}: {potential_dir_features}")
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
            # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: including: {set_dir}{potential_dir}")
            features.append(f"{set_dir}{potential_dir}")
        # else:
        #     log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: not including: {potential_dir}")


def add_sets(dev, features_dir, base_dir, features):
    dir_path = f"{features_dir}{base_dir}"
    if os.path.isdir(dir_path):
        set_dirs = sorted(os.listdir(dir_path))
        for set_dir in set_dirs:
            add_set(dev, features_dir, f"{base_dir}{set_dir}/", features)
            # dirs = sorted(filter(lambda dir: MULTI_FEATURE_DIR_SEPARATOR in dir, os.listdir(f"{base_dir}/{set_dir}")))
            # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{base_dir}/{set_dir}: dirs: {dirs}")
            # for dir in dirs:
            #     set_features = get_multi_dir_features(f"{base_dir}/{set_dir}/{dir}", features)

def has_method(dev, method):
    found = False
    # debug_files = [file for file in os.listdir(f"{SDK_DEVICES_DIR}/{dev}") if file.endswith('.debug.xml')]
    found = open(f"{SDK_DEVICES_DIR}/{dev}/{dev}.api.debug.xml", 'r').read().find(f'"{method}"') != -1
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: has_method: {method}: {found}")
    return found

def merge_feature_result(a, b):
    for trueOrFalse in b:
        if b[trueOrFalse]:
            a[trueOrFalse].extend(b[trueOrFalse])

def get_value_by_json_path(dev, feature, attr, json_path_str):
    device = DEVICES[dev]
    json_path = json_path_str.split('.')
    obj = device
    for key in json_path:
        idx = -1
        if '[' in key:
            if re.match(r'.*\[[0-9]*\]', key):
                # key = key.replace('[0]', '')
                # idx = 0
                idx = int(re.sub(r'.*\[([0-9]*)\]', r'\1', key))
                key = re.sub(r'\[[0-9]*\]', '', key)
        if key not in obj:
            obj = False
            # has_feature = False
            if op != False:
                print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}: {feature}: {attr}: {json_path_str} => no key: {key} (from {json_path_str})")
            break
        obj = obj[key]
        if idx >= 0:
            if idx < len(obj):
                obj = obj[idx]
            else:
                print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}: {feature}: {attr}: {json_path_str} => no index: {idx} in {key} (from {json_path_str})")
    # print(f"{dev}: key: {key}, obj: {obj}, has_feature1: {has_feature}")
    # if not obj:
    #     has_feature = False
    # print(f"{dev}: key: {key}, obj: {obj}, has_feature2: {has_feature}")
    # TODO: value = obj => need to set it somewhere in the jungle file or generate it into a const
    # print(f"{dev}: feature: {feature}, attr: {attr}, json_path_str: {json_path_str}, op: {op}, obj: {obj}")
    return obj


def get_bool_value_by_json_path(dev, feature, attr, json_path_str):
    op = True
    if json_path_str[0] == '!':
        op = False
        json_path_str = json_path_str[1:]
    return get_value_by_json_path(dev, feature, attr, json_path_str) == op


def has_feature_by_constraints(dev, constraints, feature = None):
    if dev == 'base':
        return False
    has_constraints = {True: [], False: []}
    if feature is None:
        for f in constraints:
            merge_feature_result(has_constraints, has_feature_by_constraints(dev, constraints, f))
    elif feature in constraints:
        device = DEVICES[dev]
        for attr in constraints[feature]:
            has_feature = True
            no_feature_reason = ''
            val = constraints[feature][attr]
            # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {feature}: {attr}: {val} => ?")
            if attr == 'min_ciq' and versiontuple(device['minVersion']) < versiontuple(val):
                has_feature = False
                # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {feature}: {attr}: {val} => {has_feature}")
            elif attr == 'max_ciq' and versiontuple(val) <= versiontuple(device['minVersion']):
                has_feature = False
                # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {feature}: {attr}: {val} => {has_feature}")
            elif attr == 'min_color_depth' and get_color_depth(device) < int(val):
                has_feature = False
                # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {feature}: {attr}: {get_color_depth(device)} < {val} => {has_feature}")
            elif attr == 'is_beta' and not IS_BETA:
                has_feature = False
            elif attr == 'is' and int(val) == 0:
                has_feature = False
            elif attr == 'has' and not has_method(dev, val):
                has_feature = False
            elif attr == 'min_memory' and (APP_TYPE not in device['memory'] or device['memory'][APP_TYPE] < int(val)):
                has_feature = False
                # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {feature}: {attr}: {val} => {has_feature}")
            elif attr == 'json':
                # if isinstance(val, list):
                #     obj = True
                #     for json_path in val:
                #         obj &= get_value_by_json_path(dev, feature, attr, json_path)
                # else:
                obj = get_bool_value_by_json_path(dev, feature, attr, val)
                # print(f"{dev}: feature: {feature}, attr: {attr}, val: {val}, obj: {obj}")
                if not obj:
                    has_feature = False
                # print(f"{dev}: key: {key}, obj: {obj}, has_feature2: {has_feature}")
            elif attr == 'key_behavior':
                if 'keys' not in device['simulator']:
                    has_feature = False
                    no_feature_reason = 'no_keys'
                    break
                behaviors = val.split(';')
                for behavior in behaviors:
                    # if not next((key for key in device['simulator']['keys'] if 'behavior' in key and key['behavior'] == behavior), None):
                    #     has_feature = False
                    has_behavior = False
                    for key in device['simulator']['keys']:
                        if 'behavior' in key and key['behavior'] == behavior:
                            has_behavior = True
                            # no_feature_reason += (',' if no_feature_reason else '') + f'no_key_{key["id"]}'
                    if not has_behavior:
                        has_feature = False
                        no_feature_reason += (';' if no_feature_reason else '') + f'{behavior}'
                # no_feature_reason = f"no_behavior:{no_feature_reason}"
            elif attr == 'key_id':
                if 'keys' not in device['simulator']:
                    has_feature = False
                    no_feature_reason = 'no_keys'
                    break
                key_ids = val.split(';')
                for key_id in key_ids:
                    # if not next((key for key in device['simulator']['keys'] if 'behavior' in key and key['behavior'] == behavior), None):
                    #     has_feature = False
                    has_key_id = False
                    for key in device['simulator']['keys']:
                        if 'id' in key and key['id'] == key_id:
                            has_key_id = True
                            # no_feature_reason += (',' if no_feature_reason else '') + f'no_key_{key["id"]}'
                    if not has_key_id:
                        has_feature = False
                        no_feature_reason += (';' if no_feature_reason else '') + f'{key_id}'
            # if feature != attr:
            #     print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}: has_feature_by_constraints: feature: {feature} != attr: {attr}")
            # has_constraints[has_feature].append(f"{feature}:{attr + ':' if feature != attr else ''}{val}:{no_feature_reason}")
            has_constraints[has_feature].append(f"{feature}:{attr + ':' if feature != attr else ''}{no_feature_reason if no_feature_reason else val}")
    else:
        print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"unknown feature: '{feature}' in constraints: {constraints}")

    # log(LOG_LEVEL, LOG_LEVEL_INPUT, f"{dev}: {'no_' if not has_feature else ''}{feature}")
    log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: has_feature_by_constraints: {feature}: {has_constraints}")
    return has_constraints

def features(dev):
    for conf_base_dir in get_base_dirs():
        if dev == 'base':
            return [has_directory(f'{conf_base_dir}features/base/source'), has_directory(f'{conf_base_dir}features/base/resources'), 'base']
        device = DEVICES[dev]
        if APP_TYPE not in device['memory']:
            return [has_directory(f'{conf_base_dir}features/base/source'), has_directory(f'{conf_base_dir}features/base/resources'), 'base']
        memory_limit = device['memory'][APP_TYPE]
        source_path_arr = []
        resource_path_arr = []
        exclude_annotations_arr = []
        langs = {}
        features = []
        # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: features: memory_limit: {memory_limit}: {get_features_by_memory(memory_limit)}")
        features_by_memory = get_features_by_memory(memory_limit)
        all_features = list(features_by_memory)
        all_features.extend(f for f in FEATURE_CONSTRAINS.keys() if f not in all_features and f"no_{f}" not in all_features)
        features_to_check = []
        for feature in all_features:
            is_by_memory = is_feature_by_memory(feature)
            if not is_by_memory or (is_by_memory and feature in features_by_memory):
                features_to_check.append(feature)
        for feature_or_not in features_to_check:
            has_constraints = {True: [], False: []}
            if feature_or_not.startswith('no_'):
                feature = feature_or_not.replace('no_', '')
                has_feature = False
                # TODO: debug if the has_feature &= line below works when has_feature = False
            else:
                feature = feature_or_not
                has_feature = True

            # if feature != 'user_zones' and feature != 'no_user_zones':
            #     continue
            # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {feature_or_not}: {feature}: {has_feature}")

            # has_feature &= has_feature_by_constraints(dev, FEATURE_CONSTRAINS, feature)
            # merge_feature_result(has_constraints, has_feature_by_constraints(dev, FEATURE_CONSTRAINS, feature))
            # log(LOG_LEVEL, LOG_LEVEL_INPUT, f"{dev}: features1: {feature_or_not}: {has_constraints}")
            if feature in FEATURE_CONSTRAINS:
                has_feature_constraints = has_feature_by_constraints(dev, FEATURE_CONSTRAINS, feature)
                log(LOG_LEVEL, LOG_LEVEL_INPUT, f"{dev}: features: feature: {feature_or_not}: {has_feature_constraints}")
                if has_feature_constraints[False]:
                    has_feature = False

            feature_or_not = ('' if has_feature else 'no_') + feature
            features.append(feature_or_not)
        log(LOG_LEVEL, LOG_LEVEL_OUTPUT, f"{dev}: features: all: {features}")

        add_multi_feature_dirs(dev, f'{conf_base_dir}features/', '', features)
        add_sets(dev, f'{conf_base_dir}features/', 'sets/', features)

        # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {features}")

        settings_dirs = []
        for feature_or_not in features:
            dir = has_directory(f'{conf_base_dir}features/{feature_or_not}/source')
            if dir != '' and feature_or_not != 'base': source_path_arr.append(dir)
            dir = has_directory(f'{conf_base_dir}features/{feature_or_not}/resources')
            if dir != '' and feature_or_not != 'base': resource_path_arr.append(dir)
            if feature_or_not != 'base' and MULTI_FEATURE_DIR_SEPARATOR not in feature_or_not:
                exclude_annotation = feature_or_not.replace('no_', '') if feature_or_not.startswith('no_') else f"no_{feature_or_not}"
                exclude_annotations_arr.append(exclude_annotation)
            for lang in MANIFEST_LANGS:
                dir = has_directory(f'{conf_base_dir}features/{feature_or_not}/lang-{lang}')
                # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {feature}: {lang}, {dir}")
                if dir != '':
                    if lang not in langs:
                        langs[lang] = []
                    langs[lang].append(dir)
            dir = has_directory(f'{conf_base_dir}features/{feature_or_not}/settings')
            if dir != '':
                settings_dirs.append(dir)

        # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: settings in: {settings_dirs}")
        settings_files = {}
        for settings_dir in settings_dirs:
            for file in os.listdir(settings_dir):
                if file in settings_files:
                    # sys.exit(f"{dev}: multiple settings file with the same name: {settings_files[file]}/{file} and {settings_dir}/{file}")
                    print_error(f"{dev}: multiple settings file with the same name: {settings_files[file]}/{file} and {settings_dir}/{file}")
                    sys.exit('')
                settings_files[file] = settings_dir
        sorted_settings_files = sorted(settings_files.keys())
        # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{sorted_settings_files}")
        for file in sorted_settings_files:
            resource_path_arr.append(f"{settings_files[file]}/{file}")

    result = [';'.join(source_path_arr), ';'.join(resource_path_arr), ';'.join(exclude_annotations_arr), langs]
    # log(LOG_LEVEL, LOG_LEVEL_BASIC, f"{dev}: {result}")
    return result
pre_register(features)

SHAPES = ['rectangle', 'round', 'semi-octagon', 'semi-round']
def shape(dev):
    if dev == 'base':
        return ['', '', '']
    device = DEVICES[dev]
    if 'display' not in device['simulator']:
        print_error(f"{dev}: no display shape")
        return ['', '', '']

    shape = device['simulator']['display']['shape']
    shape_str = shape.replace('-', '_')
    # annotations = ['no_rectangle' if shape == 'rectangle' else 'rectangle']
    annotations = []
    for s in SHAPES:
        annotations.append(('no_' if s == shape else '') + 'shape_' + s.replace('-', '_'))
    return ['', '', ';'.join(annotations)]
pre_register(shape)

def smart_datafield(dev):
    if dev == 'base':
        return ['', '', '']
    # sourceDirs = list(filter(None, [has_directory(f"{GENERATED_FEATURES_DIR}/datafield_layout"), has_directory(f"{GENERATED_DEVICES_DIR}/{dev}")]))
    return [has_directory(f"{GENERATED_FEATURES_DIR}/smart_datafield"), '', '']
pre_register(smart_datafield, 'smart_datafield', dependencies=['color', 'number_font', 'shape'])

def degrees_from_screen_center(x, y, screen_center_x, screen_center_y):
    # if x == screen_center_x:
    #     return 90 if y < screen_center_y else 270
    rad = math.atan2(x - screen_center_x, y - screen_center_y)
    deg = math.degrees(rad)
    # log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"degrees_from_screen_center: x: {x}, y: {y}, ox: {screen_center_x}, oy: {screen_center_y}, dx: {x - screen_center_x}, dy: {y - screen_center_y}, rad: {rad}, deg: {deg} => {deg - 90}")
    return deg - 90


def key_location(dev):
    if dev == 'base':
        return ['', '', '']

    conf_base_dir = get_base_dir()
    if not conf_base_dir:
        device = DEVICES[dev]
        display_loc = device['simulator']['display']['location']
        try:
            control_bar_height = device['simulator']['layouts'][0]['controlBar']['height']
        except:
            control_bar_height = 0
        device_dir = f"{GENERATED_DEVICES_DIR}/{dev}"
        device_file = f"{device_dir}/key_location.mc"
        os.makedirs(device_dir, 0o755, True)
        with open(device_file, 'w') as output:
            # output.write(f"// GENERATED for {dev} by {GENERATROR_SIGNATURE}\n\n");
            output.write(f"// GENERATED by {GENERATROR_SIGNATURE}\n\n")
            output.write("import Toybox.Lang;\n\n")

            if USE_MODULES:
                output.write("module Flocsy {\n")
                output.write("\tmodule KeyLocation {\n\n")

            is_round = 'round' in device['simulator']['display']['shape']
            is_rectangle = 'rectangle' in device['simulator']['display']['shape']
            has_key_hint_on_the_left = False
            has_key_hint_on_the_right = False
            has_key_hint_on_the_bottom = False
            output.write(f"(:key_location) const KEY_HINT_IS_ARC = {'true' if is_round else 'false'};\n")
            output.write(f"(:key_location) const KEY_HINT_IS_BAR = {'true' if is_rectangle else 'false'};\n\n")
            if 'keys' in device['simulator']:
                processed_keys = set()
                for key in device['simulator']['keys']:
                    # invalid values but need the constants so the monkey compiler is happy
                    deg = 0.0
                    x = 0
                    y = 0
                    w = 0
                    h = 0
                    if is_round:
                        key_x = key['location']['x'] + key['location']['width'] / 2 - display_loc['x']
                        key_y = key['location']['y'] + key['location']['height'] / 2 - display_loc['y']
                        deg = degrees_from_screen_center(key_x, key_y, display_loc['width'] / 2, display_loc['height'] / 2)
                        # output.write(f"(:key_location) const KEY_{key['id'].upper()}_ARC_DEGREE_START = {deg - 8};\n")
                        # output.write(f"(:key_location) const KEY_{key['id'].upper()}_ARC_DEGREE_END = {deg + 8};\n")
                        if 'semi' in device['simulator']['display']['shape']:
                            x = key['location']['x'] - display_loc['x']
                            y = key['location']['y'] - display_loc['y']
                            w = key['location']['width']
                            h = key['location']['height']
                            if w > h and y + h > display_loc['height']:
                                log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: semi-round key hint {key['id']}: x: {x}, y: {y}, w: {w}, h: {h}; y + h > display_height: {display_loc['height']}")
                                y = display_loc['height'] - control_bar_height
                                h = 1
                                has_key_hint_on_the_bottom = True
                                x += 4
                                w -= 8
                            else:
                                x = 0
                                y = 0
                                w = 0
                                h = 0
                        log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: key hint {key['id']}: deg: {deg}")
                    elif is_rectangle:
                        x = key['location']['x'] - display_loc['x']
                        y = key['location']['y'] - display_loc['y']
                        w = key['location']['width']
                        h = key['location']['height']
                        if w > h:
                            if y + h > display_loc['height']:
                                log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: key hint {key['id']}: x: {x}, y: {y}, w: {w}, h: {h}; y + h > display_height: {display_loc['height']}")
                                y = display_loc['height'] - control_bar_height
                                h = 1
                                has_key_hint_on_the_bottom = True
                                x += 4
                                w -= 8
                        elif h > w:
                            if x < 0:
                                log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: key hint {key['id']}: x: {x}, y: {y}, w: {w}, h: {h}; x < 0")
                                x = 0
                                w = 1
                                has_key_hint_on_the_left = True
                            elif x + w > display_loc['width']:
                                log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: key hint {key['id']}: x: {x}, y: {y}, w: {w}, h: {h}; x + w > display_width: {display_loc['width']}")
                                x = display_loc['width']
                                w = 1
                                has_key_hint_on_the_right = True
                        log(LOG_LEVEL, LOG_LEVEL_DEBUG, f"{dev}: key hint {key['id']}: x: {x}, y: {y}, w: {w}, h: {h}")
                    output.write(f"// id: {key['id']}{f', behavior: ' + key['behavior'] if 'behavior' in key else ''}\n")
                    for attr in ['id', 'behavior']:
                        if attr in key:
                            if key[attr].upper() not in processed_keys:
                                output.write(f"(:key_location) const KEY_{key[attr].upper()}_LOCATION_X = {key['location']['x'] - display_loc['x']};\n")
                                output.write(f"(:key_location) const KEY_{key[attr].upper()}_LOCATION_Y = {key['location']['y'] - display_loc['y']};\n")
                                output.write(f"(:key_location) const KEY_{key[attr].upper()}_LOCATION_WIDTH = {key['location']['width']};\n")
                                output.write(f"(:key_location) const KEY_{key[attr].upper()}_LOCATION_HEIGHT = {key['location']['height']};\n")

                                output.write(f"(:key_location) const KEY_{key[attr].upper()}_ARC_DEGREE = {deg};\n")
                                output.write(f"(:key_location) const KEY_{key[attr].upper()}_BAR_X = {x};\n")
                                output.write(f"(:key_location) const KEY_{key[attr].upper()}_BAR_Y = {y};\n")
                                output.write(f"(:key_location) const KEY_{key[attr].upper()}_BAR_WIDTH = {w};\n")
                                output.write(f"(:key_location) const KEY_{key[attr].upper()}_BAR_HEIGHT = {h};\n\n")
                                processed_keys.add(key[attr].upper())
                            else:
                                print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"key_location duplicate key {attr}: {dev}: {key[attr]}")
                output.write(f"(:key_location) const KEY_HINT_ON_THE_LEFT = {'true' if has_key_hint_on_the_left else 'false'};\n")
                output.write(f"(:key_location) const KEY_HINT_ON_THE_RIGHT = {'true' if has_key_hint_on_the_right else 'false'};\n")
                output.write(f"(:key_location) const KEY_HINT_ON_THE_BOTTOM = {'true' if has_key_hint_on_the_bottom else 'false'};\n")
            else:
                print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"key_location: {dev}: no keys")

            if USE_MODULES:
                output.write("\t}\n")
                output.write("}\n")
    sourceDirs = list(filter(None, [has_directory(f"{conf_base_dir}{GENERATED_FEATURES_DIR}/key_location"), has_directory(f"{conf_base_dir}{GENERATED_DEVICES_DIR}/{dev}")]))
    return [';'.join(sourceDirs), '', '']
pre_register(key_location, 'key_location')


def const_font(dev):
    if dev == 'base':
        return ['', '', '']

    conf_base_dir = get_base_dir()
    if not conf_base_dir:
        device = DEVICES[dev]
        device_dir = f"{GENERATED_DEVICES_DIR}/{dev}"
        device_file = f"{device_dir}/const_font.mc"
        os.makedirs(device_dir, 0o755, True)
        with open(device_file, 'w') as output:
            # output.write(f"// GENERATED for {dev} by {GENERATROR_SIGNATURE}\n\n");
            output.write(f"// GENERATED by {GENERATROR_SIGNATURE}\n\n")
            output.write("import Toybox.Graphics;\n\n")
            # output.write("import Toybox.Lang;\n\n")

            if USE_MODULES:
                output.write("module Flocsy {\n")
                output.write("\tmodule FontConstants {\n\n")

            for const_name, json_path_str in CONSTS['font'].items():
                font = get_value_by_json_path(dev, 'const_font', '', json_path_str)
                if font:
                    mc_font = font2mc_font(font, dev)
                    output.write(f"const {const_name} = {mc_font};\n")
                else:
                    print_error_log(LOG_LEVEL, LOG_LEVEL_ALWAYS, f"{dev}: const_font: font value in json")

            if USE_MODULES:
                output.write("\t}\n")
                output.write("}\n")
    # sourceDirs = list(filter(None, [has_directory(f"{conf_base_dir}{GENERATED_FEATURES_DIR}/key_location"), has_directory(f"{conf_base_dir}{GENERATED_DEVICES_DIR}/{dev}")]))
    # return [';'.join(sourceDirs), '', '']
    return [has_directory(f"{conf_base_dir}{GENERATED_DEVICES_DIR}/{dev}"), '', '']
# pre_register(const_font, 'const_font')
pre_register(const_font)


# def settings(dev):
#     if dev == 'base':
#         return ['', '', '']
#     device = DEVICES[dev]
#     return ['', '', '']
# pre_register(settings)


def resources(dev):
    conf_base_dir = get_base_dir()
    if dev == 'base':
        return ['', has_directory(f"{conf_base_dir}resources"), '']
    device = DEVICES[dev]
    deviceFamily = device['compiler']['deviceFamily']
    return ['', has_directory(f"{conf_base_dir}resources-{deviceFamily}"), '']
pre_register(resources)


def source(dev):
    conf_base_dir = get_base_dir()
    if dev == 'base':
        return [has_directory(f"{conf_base_dir}source"), '', '']
    device = DEVICES[dev]
    deviceFamily = device['compiler']['deviceFamily']
    return [has_directory(f"{conf_base_dir}source-{deviceFamily}"), '', '']
pre_register(source)


if __name__ == '__main__':
    main(sys.argv[1:])
