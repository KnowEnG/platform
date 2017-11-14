"""
utilities for working with files, particularly inside docker containers that
need to use ContainerUsers to get permissions right.
"""

import os
import csv
import json
from nest_py.ops.command_runner import CommandRunnerLocal

import nest_py.core.jobs.jobs_logger as logger

def set_file_owner(container_user, filename):
    """
    container_user(ContainerUser)
    filename(string)
    """
    uid = container_user.get_uid()
    gid = container_user.get_gid()
    os.chown(filename, uid, gid)
    return

def set_directory_owner(container_user, dirname, recurse=False):
    """
    container_user(ContainerUser)
    dirname(string)
    recurse: if true, chown all files and subdirectories 
    """
    if recurse:
        uid = container_user.get_uid()
        gid = container_user.get_gid()
        #http://stackoverflow.com/a/2853934
        for root, dirs, files in os.walk(dirname):  
            for momo in dirs:  
                os.chown(os.path.join(root, momo), uid, gid)
            for momo in files:
                os.chown(os.path.join(root, momo), uid, gid)
    else:
        set_file_owner(container_user, dirname)
    return


def dump_csv(filename, column_names, row_blobs, file_owner=None, ensure_dir=True):
    """
    filename(string)
    column_names(list of strings)
    row_blobs(list of dicts): every dict has an entry for each column name 
    file_owner(ContainerUser)
    ensure_dir(bool): make directory of file if it doesn't exist
    """
    #print("writing " + str(len(row_blobs)) + ' rows to file: ' + filename)

    if ensure_dir:
        ensure_directory_of_file(filename, file_owner=file_owner)

    with open(filename, 'wb') as csvfile:
        writer = csv.DictWriter(csvfile, 
            fieldnames=column_names,
            delimiter=',', 
            lineterminator=os.linesep)
        writer.writeheader()
        for row in row_blobs:
            writer.writerow(row)
            
    if not file_owner is None:
        set_file_owner(file_owner, filename)
    return

def csv_file_to_nested_dict(filename, primary_key_col):
    """
    assumes the first line of the csv is column names. loads each line
    into a dict of kvps where key is column name and value is the value 
    in the cell.

    Puts all of these kvp dicts into one top level dict, where the key
    is the value of the 'primary_key_col' and the value is the kvp dict.
    """
    nested_dict = dict()
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row_dict in reader:
            primary_key = row_dict[primary_key_col]
            nested_dict[primary_key] = row_dict
    #logger.log('loaded csv file to nested dict: ' + filename)
    #logger.pretty_print_jdata(nested_dict)
    return nested_dict

def csv_file_column_names(filename):
    """
    returns the column names (first row values) of a csv file
    as a list of strings
    """
    with open(filename, 'r') as csv_file:
        d_reader = csv.DictReader(csv_file)
        column_names = list(d_reader.fieldnames)
    return column_names

def ensure_directory(dirname, file_owner=None):
    if not os.path.exists(dirname):
        if file_owner is None:
            os.makedirs(dirname)
        else:
            #use a bash command and commandrunner so the ownership propagates
            cr = CommandRunnerLocal(file_owner)
            cmd = 'mkdir -p ' + dirname
            res = cr.run(cmd)
            if not res.succeeded():
                raise Exception('Failed to make directory: \n' + str(res))
    return

def make_symlink(existing_path, target_path, file_owner=None):
    """
    makes a symlink on the file system so that target_path points
    to existing_path.
    """
    cr = CommandRunnerLocal(file_owner)
    cmd = 'ln -s ' + existing_path + ' ' + target_path 
    res = cr.run(cmd)
    if not res.succeeded():
        raise Exception('Failed to make symlink: \n' + str(res))
    if not file_owner is None:
        set_file_owner(file_owner, target_path)
    return

def ensure_directory_of_file(filename, file_owner=None):
    """
    given a file name (which may or may not exist), checks
    if it's directory exists and creates it if not
    """    
    dirname = os.path.dirname(filename)
    ensure_directory(dirname, file_owner=file_owner)
    return

def load_json_file(filename):
    with open(filename) as data_file:    
        data = json.load(data_file)
    return data

def dump_json_file(filename, jdata, file_owner=None):
    """
    writes the contents of a jdata object (lists, dicts, primitives)
        as a pretty printed (multiline) json string to the
        filename
    """
    json_str = json.dumps(jdata, indent=4)
    with open(filename, 'wb') as json_file:
        json_file.write(json_str)
    if not file_owner is None:
        set_file_owner(file_owner, filename)
    return

