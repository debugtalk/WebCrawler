import os
import yaml
import json
import hashlib
import logging
from termcolor import colored


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
