import os
from sys import platform as _platform

def pathmake(main_folder, sub_folder):

    if _platform == 'darwin':
        # Mac OS X
        madepath = '/Volumes/'+main_folder+'/'+sub_folder
    elif _platform == 'win32' or _platform == 'cygwin':
        # Windows
        madepath = '\\\\18.62.1.253\\'+main_folder+'\\'+sub_folder
    else:
        # Unknown platform
        madepath = None

    ## Check if server is connected
    if os.path.exists(madepath) is False:
        raise FileNotFoundError('Server NOT connected! and file was not found at {}'.format(imagepath_backup))

    return madepath
