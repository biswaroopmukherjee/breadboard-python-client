## Imports
import numpy as np
import re
import sqlite3
import datetime

### Useful for datetime
epoch = datetime.datetime.utcfromtimestamp(0)
def unix_time(dt):
    return (dt - epoch).total_seconds()

def timestr_to_datetime(time_string):
    time_string = re.sub(' ','0',time_string)
    return datetime.datetime.strptime(time_string,'%m-%d-%Y_%H_%M_%S')

###-----------------------------------
### Functions to read snippet files
###-----------------------------------

## Make a dictionary from an arbitrary line in the file
def generate_dictionary(line):

	# Split line into name and params, and clean
    current_line = re.split('\t',line)  # Split line into image name and params
    current_line = [re.sub('\n','',line) for line in current_line] # Remove newlines

    # Get snippet_time, date and time
    snippet_time = current_line[0]
    [img_mm, img_dd, img_yy, img_hh, img_mi, img_ss] = re.split('-|_',snippet_time)
    img_date = img_yy+'-'+img_mm+'-'+img_dd
    img_time = img_hh+':'+img_mi+':'+img_ss
    extra_params = ['snippet_time',snippet_time] + ['Date', img_date] + ['Time', img_time] +  ['year', int(img_yy)] + ['month', int(img_mm)] + ['day', int(img_dd)] + ['hour', int(img_hh)] + ['minute', int(img_mi)] + ['second', int(img_ss)] + ['unixtime',unix_time(timestr_to_datetime(snippet_time))]

    # Set up params as a list
    paramline = re.sub(' |=|\+','',current_line[1])
    paramline = re.split(';|,',paramline)[0:-1] # Split by ; or ,
    paramline[::2] = ['exp_'+re.sub('\.','',param) for param in paramline[::2]] # remove . from parameter name only
    paramline[1::2] = [float(param) for param in paramline[1::2]] # turn experimental parameters into floats
    params =  extra_params + paramline
    params[::2] = [str.strip(param).lower() for param in params[::2]] # Clean params

    # Turn it into a dictionary and return
    return dict(zip(params[0::2], params[1::2]))


## Convert files to dictionaries
def read_snippet_file(filename):

    if type(filename)!=str:
        print('Please enter a string for the filename!')
        return

    # Open file
    try:
        fo = open(filename,'r')
    except FileNotFoundError:
        print("Can't find that file!")

    # Read all lines
    lines = fo.readlines()
    database_dict = []

    # Parse into dictionary
    for k in range(len(lines)):
        current_dict = generate_dictionary(lines[k])
        database_dict = database_dict+[current_dict]

    # Close opened file
    fo.close()

    return database_dict

## Read a single snippet line
def read_snippet_line(filename, line_to_read):

    if type(filename)!=str:
        print('Please enter a string for the filename!')
        return

    # Open file
    try:
        fo = open(filename,'r')
    except FileNotFoundError:
        print("Can't find that file!")

    # Read the line
    for i, line in enumerate(fo):
        if i==line_to_read:
            line_dict = generate_dictionary(line)
        else:
            line_dict = []

    # Close opened file
    fo.close()

    return line_dict
