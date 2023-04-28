# -*- coding: utf-8 -*-
"""
Created on Thu Apr 27 17:06:04 2023

@author: rringuet
"""
from os.path import getsize, split
from datetime import datetime, timedelta
import urllib.request
import json
import kamodo_ccmc.flythrough.model_wrapper as MW
from kamodo_ccmc.readers.reader_utilities import read_timelist

# file_formats are the formats of the converted files, if relevant, 
# and the txt files Kamodo generates (e.g. model_list.txt and model_times.txt).
file_formats = {'ADELPHI': ['netcdf4','txt'],
                'AMGeO': ['hdf5', 'txt'],
                'CTIPe': ['netcdf3', 'netcdf4', 'txt'],
                'DTM': ['netcdf3', 'txt'],
                'GAMERA_GM': ['hdf5', 'txt'],  # under development
                'GITM': ['netcdf4', 'txt'],
                'IRI': ['netcdf3', 'txt'],
                'MARBLE': ['hdf5', 'txt'],  # under development
                'OpenGGCM_GM': ['netcdf4', 'txt'],
                'SuperDARN_uni': ['netcdf4', 'txt'],
                'SuperDARN_equ': ['netcdf4', 'txt'],
                'SWMF_IE': ['netcdf4', 'txt'],
                'SWMF_GM': ['binary', 'txt'],
                'TIEGCM': ['netcdf4', 'txt'],
                'WACCMX': ['netcdf3', 'txt'],
                'WAMIPE': ['netcdf3', 'txt'],
                'Weimer': ['netcdf3', 'txt']
                }


def bucket_name(file_dir):
    '''Given the complete path to a collection of files, determine the bucket
    name and return it. Expects file_dir to be of the form
    "s3://bucket_name/etc/etc/..../" with the trailing slash, where
    "s3://bucket_name/" is returned.
    '''
    tmp = split(file_dir[5:-1])  # cut of 's3://' and trailing slash
    while '/' in tmp[0] or '\\' in tmp[0]:
        tmp = split(tmp[0])
    return 's3://' + tmp[0] + '/'
    

def retrieve_modeljson(resourceURL=''):
    '''Return json from given resourceURL, or return current datetime in iso
    format as the 'runPublicationTime'.

    Parameters
    ----------
    resourceURL : string, optional
        String containing the online filepath to the json. Default is an empty
        string.

    Returns
    -------
    Dictionary either generated from the json retrieved or of format
    {'runPublicationTime': datetime.utcnow().isoformat}
    if the resourceURL is not provided.
    '''
    if resourceURL != '':
        with urllib.request.urlopen(resourceURL) as url:
            return json.load(url)
    else:
        return {'runPublicationTime': datetime.utcnow().isoformat()}


def modelcatalog_entry(model_name, run_name, file_dir, resourceURL='',
                       aboutURL='Not supplied', citation='Not supplied',
                       contact='Not supplied', contactID='ORCiD not supplied'):
    '''Creates catalog entry for a given model output.

    Parameters
    ----------
        - model_name: string of the model name as representing in Kamodo.
            See output from commands below to choose the right string.
            import kamodo_ccmc.flythrough.model_wrapper as MW
            MW.Choose_Model('')
        - run_name: string of the unique identifier for the model output. For
            outputs obtained from the CCMC, this should be the run name
            (e.g. Yihua_Zheng_040122_1). Otherwise, the user can create a
            unique name for the model run using any combination of letters,
            numbers, underscores, and dashes.
        - file_dir: string containing the complete file path to the location of
            the model outputs on the s3 bucket. File paths of the form
            's3://bucket_name/subbucket_name/etc.../' are expected.
        - resourceURL: a string indicating the website location of the json
            describing the model output. Could be on CCMC's website or on an
            online storage service (e.g. Google Drive) with universal read
            access.
            Example resourceURL =
            https://ccmc.gsfc.nasa.gov/results/api/run_metadata.php?runnumber=Yihua_Zheng_040122_1
            Example retrieved json located in the ExampleModelJSON.json file.
            The json must have an entry labeled 'runPublicationTime' indicating
            the model run publication time (e.g. time it is publicly available)
            or the current time (e.g. datetime.utcnow().isoformat()) in iso
            format.
            Default value is an empty string, resulting in the current time
            being used as the model run creation date.
        - aboutURL: a string containing the link to a website containing
            information about the model run.
            Example aboutURL:
            https://ccmc.gsfc.nasa.gov/results/viewrun.php?domain=GM&runnumber=Yihua_Zheng_040122_1
            Example contents located in ExampleModelaboutURL.pdf
            Default value is "Not supplied".
        - citation: How this model output should be cited, preferably a DOI
            for the dataset generated independently of any publications.
            Default value is "Not supplied".
        - contact: A string containing your first and last name and email
            address. By providing this information, you consent to it being
            made public and associated with this dataset.
            Default value is "Not supplied".
        - contactID: Your ORCiD. See https://www.orcid.org to find your ORCiD
            or to create one. The process is quick. By providing this
            information, you consent to it being made public and associated
            with this dataset.
            Default value is "ORCiD not supplied".

    Returns
    -------
        Dictionary entry for the model output to be entered in the catalog
            list of the bucket/catalog.json file.
    '''
    bucketname = bucket_name(file_dir)
    start_dt, stop_dt = MW.File_Times(model_name, file_dir, print_output=False)
    model_json = retrieve_modeljson(resourceURL)
    json_dict = {'id': model_name+'-'+run_name,
                 'loc': bucketname+'ModelOutputs/',
                 'title': model_name+' model, '+run_name+' run.',
                 'startDate': start_dt.isoformat()[:19]+'Z',
                 'stopDate': stop_dt.isoformat()[:19]+'Z',
                 'modificationDate': datetime.utcnow().isoformat()[:19]+'Z',
                 'indexFormat': 'csv',
                 'fileFormat': file_formats[model_name],
                 'description': model_json,
                 'resourceURL': resourceURL,
                 'creationDate': model_json['runPublicationTime'][:19]+'Z',
                 'citation': citation,
                 'contact': contact,
                 'contactID': contactID,
                 'aboutURL': aboutURL
                 }
    return json_dict


def initialize_csvfile(model_name, run_name, year, write_file=None):
    '''Initializes the next csv File Registry file. Closes the one current open
    if given.

    Parameters
    ----------
    model_name : string of the model name as representing in Kamodo.
        See output from commands below to choose the right string.
        import kamodo_ccmc.flythrough.model_wrapper as MW
        MW.Choose_Model('')
    run_name : string of the unique identifier for the model output. For
        outputs obtained from the CCMC, this should be the run name
        (e.g. Yihua_Zheng_040122_1). Otherwise, the user can create a
        unique name for the model run using any combination of letters,
        numbers, underscores, and dashes.
    year : integer of the four digit year of the current timestamp of the data.
    write_file : file object, optional
        file object of the currently open csv. If there isn't one open, then
        the default should be used. The default is None.

    Returns
    -------
    write_file : file object
        file object for new csv file named with the current year.
    '''
    if write_file is not None:
        write_file.close()
    newcsv_filename = model_name + '-' + run_name + '_' + str(year) + '.csv'
    write_file = open(newcsv_filename, 'w')
    write_file.write('# startDate, key, filesize, stopDate')
    return write_file


def modelregistry(model_name, run_name, file_dir):
    '''Creates the csv (or multiple csvs) containing the file registry for the
    model output. If the model output contains data for multiple years, then
    one csv will be generated per year. The csv follows the formatting required
    by the HelioCloudRegistry software. A json file is also produced in line
    with the registry requirements.

    Parameters
    ----------
        - model_name : string of the model name as representing in Kamodo.
            See output from commands below to choose the right string.
            import kamodo_ccmc.flythrough.model_wrapper as MW
            MW.Choose_Model('')
        - run_name : string of the unique identifier for the model output. For
            outputs obtained from the CCMC, this should be the run name
            (e.g. Yihua_Zheng_040122_1). Otherwise, the user can create a
            unique name for the model run using any combination of letters,
            numbers, underscores, and dashes.
        - file_dir : string containing the complete file path to the location of
            the model outputs on the s3 bucket. File paths of the form
            's3://bucket_name/subbucket_name/etc.../' are expected.
    Returns
    -------
    None
    '''
    # create id_info.json file for dataset
    start_dt, stop_dt = MW.File_Times(model_name, file_dir, print_output=False)
    info_json = {'CloudMe': '0.2',
                 'parameters': [{
                     'name': 'stopDate',
                     'type': 'string',
                     'description': 'ISO date of end of file'
                     }]
                 }
    json_filename = model_name + '-' + run_name + '_info.json'
    with open(json_filename, 'w') as write_file:
        json.dump(info_json, write_file)

    # create csv file(s) for dataset
    time_file = file_dir + model_name + '_times.txt'
    list_file = file_dir + model_name + '_lists3.txt'  # generated by data_prep
    times, pattern_files, filedate, filename = read_timelist(time_file,
                                                             list_file)
    year = start_dt.year  # initialize year for filenames, integer (YYYY)
    write_file = initialize_csvfile(model_name, run_name, year)
    for p, files in pattern_files.items():
        for i, f in enumerate(files):
            startDate = filedate + timedelta(hours=times[p]['start'][i])
            stopDate = filedate + timedelta(hours=times[p]['end'][i])
            filesize = getsize(f)
            if startDate.year != year:
                write_file = initialize_csvfile(model_name, run_name, year,
                                                write_file=write_file)
            write_file.write(f"'{startDate}','{f}','{filesize}','{stopDate}'")       
    write_file.close()
    return None

