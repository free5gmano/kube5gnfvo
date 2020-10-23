# All Rights Reserved.
#
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import zipfile
import io
import shutil
import yaml
import urllib.request
from shutil import copy2
import hashlib


def walk_file(path, key):
    for root, dirs, files in os.walk(path):
        if key in root:
            return root, dirs, files


def copy_file(src_path, dst_path, key):
    root, dirs, files = walk_file(src_path, key)
    for file in files:
        copy2('{}/{}'.format(root, file), dst_path)


def create_update_file(path, input_data):
    target_path = os.path.split(path)
    if not os.path.isdir(target_path[0]):
        os.makedirs(target_path[0])
    with open(path, 'w') as target_file:
        target_file.write(input_data)


def create_dir(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass


def decompress_zip(zip_file, dir_path):
    with zipfile.ZipFile(zip_file, "r") as zf:
        for file in zf.namelist():
            zf.extract(file, dir_path)
        zf.close()
    return dir_path + zf.filename.split(".")[0] + '/' \
        if zf.filename in '/' else dir_path + os.path.basename(zf.filename).split('.')[0] + '/'


def read_yaml_file(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def read_manifest_file(file_path, key, deep):
    result = [] if deep > 1 else ''
    with open(file_path, "r") as file:
        data = file.read().splitlines()
    for index, element in enumerate(data):
        if key in element:
            if deep > 1:
                item_dict = {}
                for deep_count in range(0, deep):
                    item_dict[data[deep_count + index].split(':')[0].lstrip()] = \
                        data[deep_count + index].split(':')[1].lstrip()
                result.append(item_dict)
            else:
                result = data[index].split(':')[1].lstrip()
    return result


def compression_dir_zip(output_filename, source_dir):
    zip_filename = "%s.zip" % output_filename
    bytes_io = io.BytesIO()
    rel_root = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(bytes_io, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            zf.write(root, os.path.relpath(root, rel_root))
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename):
                    arc_name = os.path.join(os.path.relpath(root, rel_root), file)
                    zf.write(filename, arc_name)
    return bytes_io, zip_filename


def remove_file(path):
    shutil.rmtree(path, ignore_errors=True)


def sha256_hash(file_path):
    sha256_hash_value = hashlib.sha256()
    with open(file_path, "rb") as file:
        sha256_hash_value.update(file.read())
        return sha256_hash_value.hexdigest()


def download_file(url, file_name):
    with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
        return file_name


def mount_dir(nfs_server,nfs_path):
    if not os.path.isdir(setting.NFS_PATH):
        os.makedirs(setting.NFS_PATH)
    if not os.path.ismount(setting.NFS_PATH):
        process = Popen(['mount', '-t', 'nfs', '{}:{}'.format(nfs_server, nfs_path),
                         setting.NFS_PATH], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()