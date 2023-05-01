# -*- coding: utf-8 -*-
"""
Created on Thu Apr 27 17:06:04 2023

@author: rringuet
"""
from os.path import getsize, split
from datetime import datetime, timezone, timedelta
import json
from numpy import array, arctan2, sqrt, where, cos, diff, sign, unique
import kamodo_ccmc.flythrough.model_wrapper as MW
from kamodo_ccmc.flythrough import SatelliteFlythrough as S
from kamodo_ccmc.readers.reader_utilities import glob, _isfile
import pyspedas
import spacepy
from pytplot import get_data
from pyspedas import tinterpol


# Better to have a DOI for the packages than the citations below.
kamodo_ccmc_citation = 'Ringuette, R., D. De Zeeuw, L. Rastaetter, and ' +\
    "A. Pembroke. 2022. Kamodo's Model-Agnostic Satellite Flythrough: " +\
        "Lowering the Utilization Barrier for Heliophysics Model Outputs. " +\
            'Frontiers in Astronomy and Space Sciences, vol 9. ' +\
                'http://dx.doi.org/10.3389/fspas.2022.1005977'
pyspedas_citation = 'pySPEDAS. 2022. pySPEDAS. GitHub. Accessed April ' +\
    '2023. https://github.com/spedas/pyspedas'
magnetopause_project_citation = ''  # get from OSF


# trange = ['2015-10-16/11:30', '2015-10-16/17:00']


def load_mms_data(time_range):
    """Loads MMS MEC, FGM, and FPI data."""
    mec_vars = pyspedas.mms.mec(trange=time_range, time_clip=True, probe=1,
                                level='l2', data_rate='srvy',
                                varformat='*_r_gsm')  # Cartesian GSM coords
    fgm_vars = pyspedas.mms.fgm(trange=time_range, time_clip=True, probe=1,
                                level='l2', data_rate='srvy')
    ion_vars = pyspedas.mms.fpi(trange=time_range,
                                datatype=['dis-moms', 'des-moms'], level='l2',
                                data_rate='fast', time_clip=True,
                                center_measurement=True)

    return mec_vars, fgm_vars, ion_vars


def spacecraft_magnetopause_calculations(mms_mec_vars):
    """Returns epoch, 
               pos,
               distance between spacecraft and magnetopause, 
               magnetopause's distance from Earth, 
               spacecraft's distance from Earth, 
               and solar zenith angle.
    """
    data = get_data(mms_mec_vars[0])
    pos_gsm = data.y
    ticks = spacepy.time.Ticktock(data.times, dtype='UNX')
    epoch = ticks.UTC
    c = spacepy.coordinates.Coords(pos_gsm, 'GSM', 'car', units='km',
                                   ticks=ticks)
    pos = c.convert('GSE', 'car').data

    # Get the Shue coefficients
    alpha = []  # Shue flaring angle
    # Shue subsolar standoff
    standoff = spacepy.empiricals.getMPstandoff(ticks, alpha=alpha)
    alpha = array(alpha)

    # Solar zenith angle of s/c position (angle with GSE +x)
    sza = arctan2(pos[:, 0], sqrt((pos[:, :2] ** 2).sum(axis=1)))
    # Radial distance to MP along Earth-SC line (application of Shue coeffs)
    mp_dist = standoff * (2. / (1 + cos(sza))) ** alpha
    # Radial distance to SC
    sc_dist = sqrt((pos ** 2).sum(axis=1)) / 6378
    # How far is SC outside of MP?
    sc_to_mp = sc_dist - mp_dist

    return epoch, pos, sc_to_mp, mp_dist, sc_dist, sza


def find_magnetopause_crossings(sc_to_mp):
    """Returns the indices of elements before which zero crossings occur."""
    return where(diff(sign(sc_to_mp)))[0]


def magnetopause_flythrough(model_name, run_name, file_dir, sat_name, trange,
                            out_file, variable_list=['B_x', 'B_y', 'B_z'],
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
    mec_vars, fgm_vars, ion_vars = load_mms_data(trange)
    epoch, pos, sc_to_mp, mp_dist, sc_dist, sza = \
        spacecraft_magnetopause_calculations(mec_vars)
    
    # Convert epoch to UTC timestamps and pos to R_Es
    sat_time = [time.replace(tzinfo=timezone.utc).timestamp() for time in
                epoch]
    sat_x = pos[:, 0] / 6378.
    sat_y = pos[:, 1] / 6378.
    sat_z = pos[:, 2] / 6378.

    # fly trajectory through model output and functionalize
    results = S.ModelFlythrough(model_name, file_dir, variable_list, sat_time,
                                sat_x, sat_y, sat_z, "GSM-car",
                                output_name=out_file+'.nc', plot_coord='GSM')
    kamodo_object = S.O.Functionalize_SFResults(model_name, results)

    # generate metadata entries and add to respective files
    
    
    return kamodo_object


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
                 'catalogLoc': bucketname+'FlythroughResults/',
                 'title': 'Flythrough results from the '+model_name+'-'+\
                     run_name+' run.',
                 'startDate': start_dt.isoformat()[:19]+'Z',
                 'stopDate': stop_dt.isoformat()[:19]+'Z',
                 'modificationDate': time_now[:19]+'Z',
                 'indexFormat': 'csv',
                 'fileFormat': 'netcdf4',
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
def flythroughregistry(model_name, run_name, flythrough_dir):
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
        - flythrough_dir : string containing the complete file path to the
            location of the flythrough outputs on the s3 bucket. File paths of
            the form 's3://bucket_name/subbucket_name/etc.../' are expected.
    Returns
    -------
    None
    '''
    # create id_info.json file for dataset
    json_filename = flythrough_dir + model_name + '-' + run_name +\
        '-Flythrough_info.json'
    if not _isfile(json_filename):
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
                             'description': 'Name of coordinate system.'
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
                             'description': 'Z or Radius in R_E, or height ' +
                                 'in km.'
                             },
                         {
                             'name': 'variable_list',
                             'type': 'string',
                             'description': 'Comma-separated list of variable ' +\
                                 'names in the flythrough output.'
                             }
                         ]
                     }
        
        with open(json_filename, 'w') as write_file:
            json.dump(info_json, write_file)

    # figure out what file starts in what year by building a dictionary
    # key: [startDate, filename, filesize, stopDate, model, runname, coord_sys,
    #       coord1, coord2, coord3, var_list]
    files = glob(flythrough_dir+'*.nc')
    file_dict = {}
    for f in files:
        results = S.O.SF_read(f)
        filesize = getsize(f)
        startDate = datetime.utcfromtimestamp(results['utc_time']['data'][0][
            :19]).isoformat() + 'Z'
        stopDate = datetime.utcfromtimestamp(results['utc_time']['data'][-1][
            :19]).isoformat() + 'Z'
        model = results['metadata']['model_used']
        coord_sys = results['metadata']['coord_type'] + '-' + \
            results['metadata']['coord_grid']
        var_list = [key for key in results.keys() if key not in
                    ['utc_time', 'c1', 'c2', 'c3', 'net_idx', 'metadata']]
        units = [results[c]['units'] for c in ['c1', 'c2', 'c3']]
        if units == ['R_E', 'R_E', 'R_E']:
            coord1, coord2, coord3 = 'X', 'Y', 'Z'
        elif units == ['deg', 'deg', 'R_E']:
            coord1, coord2, coord3 = 'Longitude', 'Latitude', 'Radius'
        elif units == ['deg', 'deg', 'km']:
            coord1, coord2, coord3 = 'Longitude', 'Latitude', 'Height'
        file_dict[f] = [startDate, f, filesize, stopDate, model, run_name,
                        coord_sys, coord1, coord2, coord3, var_list]

    # create dictionary of years with a list of filenames starting in each year
    years = unique([value[0][:4] for key, value in file_dict.items()])
    year_dict = {y: [f for f, value in file_dict.keys() if value[0][:4] == y]
                 for y in years}

    # create csv file(s) for flythrough outputs
    for year in year_dict.keys():
        write_file = initialize_csvfile(model_name, run_name, year)
        for f in year_dict[year]:
            out_string = ''.join(["'"+item+"'," for item in file_dict[f]])[:-1]
            write_file.write(out_string)
        write_file.close()

    return None

