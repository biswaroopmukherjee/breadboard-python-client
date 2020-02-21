'''
breadboard_python_watchdog.py
=============================
This lets you watch a folder for new single images and upload the metadata to Breadboard. 
Usage:

python3 breadboard_python_watchdog.py [WATCHFOLDER]

where [WATCHFOLDER] is the folder your camera program writes images to.

'''

# Imports 
import os
import time
import datetime
import shutil
import posixpath
import sys
from breadboard import BreadboardClient
import warnings
warnings.filterwarnings("ignore", "Your application has authenticated using end user credentials")
warnings.filterwarnings("ignore", "Could not find appropriate MS Visual C Runtime")

def getFileList(folder = 'Not Provided'):
    # Get a list of files in a folder
    if not os.path.exists(folder): raise ValueError("Folder '{}' doesn't exist".format(folder))
    # Folder contents
    filenames = [filename for filename in os.listdir(folder)]
    # Output
    paths = [os.path.join(folder,f) for f in filenames]
    return (filenames, paths)

def main():
    # Global settings 
    # bc = BreadboardClient(config_path='API_CONFIG.json') # enter your path to the API_config
    refresh_time = 0.5 # seconds
    watchfolder = sys.argv[1] # feed the program your watchfolder
    print("\n\n Watching this folder for changes: " + sys.argv[1] + "\n\n")

    names_old, paths_old = getFileList(watchfolder)

    # Main Loop 
    while True: 
        # Get a list of all the images in the folder 
        names, paths = getFileList(watchfolder)
        names = sorted(names)
        paths = sorted(paths)
        # check if a new image has come in
        if len(names)>len(names_old):
            output_filename = names[-1]
            print('New file: ' + output_filename)
            output_filepath = paths[-1]
            dt = datetime.datetime.fromtimestamp(os.path.getctime(output_filepath))
        
            # Write to Breadboard
            try:
                resp = bc.post_images(
                            image_names = os.path.splitext(output_filename)[0],
                            filepath = output_filepath,
                            image_times = [dt], 
                            auto_time = False # Add more information here
                            )
                if resp.status_code!=200:
                    print(resp.text)
            except: pass
            names_old = names

        # Wait before checking again 
        time.sleep(refresh_time)

if __name__ == '__main__':
    main()