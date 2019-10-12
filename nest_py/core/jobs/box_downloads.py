import os

import requests
import urllib3

import nest_py.core.jobs.file_utils as file_utils

#disable expected ssl warnings
#TODO: is there a global place this could go?
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecurePlatformWarning)


def download_from_box_no_auth(box_shared_link, absolute_filename, \
    file_owner=None, force=False):
    """
    Downloads a file over http and saves it to a destination filename.
    Theoretically works for any url, but specifically tested on
    box.com downloads. NOTE: you must set the sharing permissions on the file
    to 'anyone with the link' in the file's share settings on Box before
    this will work (Box defaults to 'anyone with access to this folder' or
    similar).

    box_shared_link (string of url) must be the 'direct download' link at
        the bottom of the 'Advanced Settings' menu of the file's share
        settings on box.

    absolute_filename (string): where to put the file, including full path.
        box downloads get the name of the sha like:
            y8a7qmgskm73rpovf16j96yr3st7ea96.txt
        so we will rename to this filename

    file_owner (ContainerUser) the downloaded file will have it's owner
    user and group changed to this ContainerUser's. If not set, no
    permissions will be modified and the file will keep the owner of
    the current process.

    force (bool): if False, will check if the file already exists on disk and do
        nothing if it's there. If True, will always perform the download and
        overwrite an existing file.
    """
    if not force:
        if os.path.isfile(absolute_filename):
            return

    file_utils.ensure_directory_of_file(absolute_filename, file_owner=file_owner)

    #http://stackoverflow.com/questions/14114729/save-a-large-file-using-the-python-requests-library
    with open(absolute_filename, 'wb') as handle:
        response = requests.get(box_shared_link, stream=True)
        if not response.ok:
            raise Exception("Failed to download file from \'" + \
                box_shared_link + '\' to \'' + absolute_filename)
        for block in response.iter_content(1024):
            handle.write(block)
    if not file_owner is None:
        file_utils.set_file_owner(file_owner, absolute_filename)
    return
