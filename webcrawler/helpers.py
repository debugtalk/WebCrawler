import os
import yaml
import json
import hashlib
import logging
from termcolor import colored

try:
    # Python3
    import urllib.parse as urlparse
    from urllib.parse import urlencode
except ImportError:
    # Python2
    import urlparse
    from urllib import urlencode

urlparsed_object_mapping = {}

def get_parsed_object_from_url(url, referer_url=None):
    if url in urlparsed_object_mapping:
        return urlparsed_object_mapping[url]

    parsed_object = get_parsed_object_from_url_without_extra_info(url)
    if referer_url:
        parsed_object = _make_url_by_referer(parsed_object, referer_url)

    urlparsed_object_mapping[url] = parsed_object
    return parsed_object

def get_parsed_object_from_url_without_extra_info(url):
    parsed_object = urlparse.urlparse(url)

    # remove unwanted query items
    query_dict = urlparse.parse_qs(parsed_object.query)
    for key in ['from', 'nonamp']:
        query_dict.pop(key, None)

    new_query = urlencode(query_dict)
    parsed_object = parsed_object._replace(query=new_query)

    # remove url fragment
    parsed_object = parsed_object._replace(fragment='')

    return parsed_object

def _make_url_by_referer(origin_parsed_obj, referer_url):
    """
    @params
        referer_url: e.g. https://store.debugtalk.com/product/osmo
        origin_parsed_obj.path e.g.:
            (1) complete urls: http(s)://store.debugtalk.com/product/phantom-4-pro
            (2) cdn asset files: //asset1.xcdn.com/assets/xxx.png
            (3) relative links type1: /category/phantom
            (4) relative links type2: mavic-pro
            (5) relative links type3: ../compare-phantom-3
    @return
        corresponding result url:
            (1) http(s)://store.debugtalk.com/product/phantom-4-pro
            (2) http://asset1.xcdn.com/assets/xxx.png
            (3) https://store.debugtalk.com/category/phantom
            (4) https://store.debugtalk.com/product/mavic-pro
            (5) https://store.debugtalk.com/compare-phantom-3
    """
    if origin_parsed_obj.scheme != "":
        # complete urls, e.g. http(s)://store.debugtalk.com/product/phantom-4-pro
        return origin_parsed_obj

    elif origin_parsed_obj.netloc != "":
        # cdn asset files, e.g. //asset1.xcdn.com/assets/xxx.png
        origin_parsed_obj = origin_parsed_obj._replace(scheme='http')
        return origin_parsed_obj

    elif origin_parsed_obj.path.startswith('/'):
        # relative links, e.g. /category/phantom
        referer_url_parsed_object = get_parsed_object_from_url(referer_url)
        origin_parsed_obj = origin_parsed_obj._replace(
            scheme=referer_url_parsed_object.scheme,
            netloc=referer_url_parsed_object.netloc
        )
        return origin_parsed_obj
    else:
        referer_url_parsed_object = get_parsed_object_from_url(referer_url)
        path_list = referer_url_parsed_object.path.split('/')

        if origin_parsed_obj.path.startswith('../'):
            # relative links, e.g. ../compare-phantom-3
            path_list.pop()
            path_list[-1] = origin_parsed_obj.path.lstrip('../')
        else:
            # relative links, e.g. mavic-pro
            path_list[-1] = origin_parsed_obj.path

        new_path = '/'.join(path_list)
        origin_parsed_obj = origin_parsed_obj._replace(path=new_path)

        origin_parsed_obj = origin_parsed_obj._replace(
            scheme=referer_url_parsed_object.scheme,
            netloc=referer_url_parsed_object.netloc
        )
        return origin_parsed_obj

def color_logging(text, log_level='info', color=None):
    log_level = log_level.upper()
    if log_level == 'DEBUG':
        color = color or 'blue'
        logging.info(colored(text, color))
    elif log_level == 'INFO':
        color = color or 'green'
        logging.info(colored(text, color, attrs=['bold']))
    elif log_level == 'WARNING':
        color = color or 'yellow'
        logging.info(colored(text, color, attrs=['bold']))
    elif log_level == 'ERROR':
        color = color or 'red'
        logging.info(colored(text, color, attrs=['bold']))

def load_json_file(json_file):
    with open(json_file, 'r+') as f:
        return f.read()

def load_yaml_file(yaml_file):
    with open(yaml_file, 'r+') as stream:
        return yaml.load(stream)

def get_md5(content):
    return hashlib.md5(content).hexdigest()

def load_file(file_path, file_suffix='.json'):
    file_suffix = file_suffix.lower()
    if file_suffix == '.json':
        content = load_json_file(file_path)
        return {
            'md5': get_md5(content),
            'json': json.loads(content)
        }
    elif file_suffix in ['.yaml', '.yml']:
        content = load_yaml_file(file_path)
        return {
            'md5': get_md5(json.dumps(content)),
            'json': content
        }

def save_to_yaml(data, filepath):
    file_dir = os.path.dirname(filepath)
    try:
        os.makedirs(file_dir)
    except OSError:
        pass
    with open(filepath, 'w+') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

def load_foler_files(folder_path):
    """ load folder path, return all files in set format.
    """
    file_list = []

    for dirpath, dirnames, filenames in os.walk(folder_path):
        if dirnames:
            continue

        for filename in filenames:
            basename = os.path.basename(dirpath)
            file_relative_path = os.path.join(basename, filename)
            file_list.append(file_relative_path)

    return set(file_list)
