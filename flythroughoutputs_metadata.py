# -*- coding: utf-8 -*-
"""
Created on Thu Apr 27 17:06:04 2023

@author: rringuet
"""
from os.path import getsize, split
from datetime import datetime, timedelta
import json
import kamodo_ccmc.flythrough.model_wrapper as MW
import kamodo_ccmc.SF_output as O


# Better to have a DOI for the packages than the citations below.
kamodo_ccmc_citation = 'Ringuette, R., D. De Zeeuw, L. Rastaetter, and ' +\
    "A. Pembroke. 2022. Kamodo's Model-Agnostic Satellite Flythrough: " +\
        "Lowering the Utilization Barrier for Heliophysics Model Outputs. " +\
            'Frontiers in Astronomy and Space Sciences, vol 9. ' +\
                'http://dx.doi.org/10.3389/fspas.2022.1005977'
pyspedas_citation = 'pySPEDAS. 2022. pySPEDAS. GitHub. Accessed April ' +\
    '2023. https://github.com/spedas/pyspedas'
magnetopause_project_citation = ''  # get from OSF


def magnetopause_flythrough(model_name, run_name, sat_name,
                            contact='Not supplied',
                            contactID='ORCiD not supplied'):
    '''
    Retrieve the desired trajectory through pySPEDAS, interpolate as done in
    Polson et al. (2022) (https://doi.org/10.3389/fspas.2022.977781), then
    fly that trajectory through the chosen dataset. Generates the typical
    files from the flythrough, and also the metadata files required on
    HelioCloud. This code assumes the dataset is already registered with and
    uploaded to HelioCloud. (?)
    A 16 GB or 32 GB instance is recommended for running this program,
    depending on the size of the dataset.

    Parameters
    ----------
    model_name : string
        DESCRIPTION.
    run_name : string
        DESCRIPTION.
    sat_name : string
        DESCRIPTION.
    contact : string, optional
        DESCRIPTION. The default is 'Not supplied'.
    contactID : string, optional
        DESCRIPTION. The default is 'ORCiD not supplied'.

    Returns
    -------
    None.

    '''
    # retrieve MMS trajectory as done in Polson et al. 2022.
    # interpolate to time grid
    # fly trajectory through model output
    # generate metadata entries and add to respective files
    return


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


# call this from a wrapper over SF.ModelFlythrough + pyspedas calls to auto-
# generate this based on the inputs
def flythroughcatalog_entry(model_name, run_name, file_dir, sat_name,
                            contact='Not supplied',
                            contactID='ORCiD not supplied'):
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
        - sat_name: string indicating the name of the satellite trajectory
            retrieved with pySPEDAS.
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
        Dictionary entry for the flythrough output to be entered in the catalog
            list of the bucket/catalog.json file.
    '''
    bucketname = bucket_name(file_dir)
    start_dt, stop_dt = MW.File_Times(model_name, file_dir, print_output=False)
    citation = kamodo_ccmc_citation + ', ' + pyspedas_citation + ', ' +\
        magnetopause_project_citation
    time_now = datetime.utcnow().isoformat()
    json_dict = {'id': model_name+'-'+run_name+'-Flythrough',
                 'loc': bucketname+'FlythroughResults/',
                 'title': 'Flythrough results from the '+model_name+'-'+\
                     run_name+' run.',
                 'startDate': start_dt.isoformat()[:19]+'Z',
                 'stopDate': stop_dt.isoformat()[:19]+'Z',
                 'modificationDate': time_now[:19]+'Z',
                 'indexFormat': 'csv',
                 'fileFormat': 'netcdf4',  # netcdf4 or csv ?????????????????????????????????????????
                 'description': 'Created using kamodo-ccmc from '+model_name+\
                     '-'+run_name+' dataset using the '+sat_name+\
                         ' trajectory obtained with pySPEDAS',
                 'creationDate': time_now[:10]+'Z',
                 'citation': citation,  # can we mint DOIs for these?
                 'contact': contact,
                 'contactID': contactID,
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
    newcsv_filename = model_name + '-' + run_name + '-Flythrough_' +\
        str(year) + '.csv'
    write_file = open(newcsv_filename, 'w')
    write_file.write('# startDate, key, filesize, stopDate, model, ' +
                     'runname, coordinate_system, coordinate1, coordinate2, ' +
                     'coordinate3, variable_list')
    return write_file


# CHANGE THIS TO WORK FOR FLYTHROUGH OUTPUTS
def flythroughregistry(model_name, run_name, file_dir):
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
                 'parameters': [
                     {
                         'name': 'stopDate',
                         'type': 'string',
                         'description': 'ISO date of end of file'
                         },
                     {
                         'name': 'model',
                         'type': 'string',
                         'description': 'Name of model.'
                         },
                     {
                         'name': 'runname',
                         'type': 'string',
                         'description': 'Name of run.'
                         },
                     {
                         'name': 'coordinate_system',
                         'type': 'string',
                         'description': 'Name of coordinate system from ....'  # MORE HERE
                         },
                     {
                         'name': 'coordinate1',
                         'type': 'string',
                         'description': 'X in R_E or longitude in degrees.'
                         },
                     {
                         'name': 'coordinate2',
                         'type': 'string',
                         'description': 'Y in R_E or latitude in degrees.'
                         },
                     {
                         'name': 'coordinate3',
                         'type': 'string',
                         'description': 'Z in R_E or height in km.'
                         },
                     {
                         'name': 'variable_list',
                         'type': 'string',
                         'description': 'Comma-separated list of variable ' +\
                             'names in the flythrough output.'
                         }
                     ]
                 }
    json_filename = model_name + '-' + run_name + '-Flythrough_info.json'
    with open(json_filename, 'w') as write_file:
        json.dump(info_json, write_file)

    # create csv file(s) for flythrough outputs  MORE DEVELOPMENT NEEDED HERE-------------------
    # How to deal with multiple files from the same model output, the same satellite, but different 
    # variable lists?
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

