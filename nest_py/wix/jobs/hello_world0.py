"""
Example of a Wix job that just uses the framework's basic 
functions to:
    log messages that will be sent to both the console and
        saved in a log-file in the run's data directory (each 
        run of the job has it's own log file that 
        won't be overwritten on the next run)
    load the parameters of a config file. The default config
        file is in nest/data/wix/hello_world.0/hello_world.0.cfg
    write a data file to the run-specific data directory. No
        other run of the hello_world0 job will be able to overwrite 
        this file (this is how you would save results)
    download a file from box and save it in a data directory
        *shared* by runs of hello_world0 so that the file
        doesn't have to be re-downloaded each time
    create 'checkpoint' log messages that append the number of
        seconds since the last checkpoint. Provides a very light
        weight way to time individual chunks of code.

"""
import os
import nest_py.core.jobs.file_utils as file_utils
import nest_py.core.jobs.box_downloads as box_downloads

import nest_py.hello_world.data_types.simplest_dto as simplest_dto
from nest_py.hello_world.data_types.simplest_dto import SimplestDTO
import nest_py.core.db.nest_db as nest_db
import nest_py.hello_world.db.hw_db as hw_db
import nest_py.core.jobs.jobs_auth as jobs_auth
import nest_py.wix.wix_db as wix_db

def run(jcx):
    """
    jcx (JobContext) Contains the Wix framework resources
        made available to this job run. Logging, 
        disk file management, etc. should be handled
        through the jcx. 
    """

    #this will log the message with the time elapsed since
    #the job was triggered, and also the time since 'checkpoint'
    #was last called.
    jcx.checkpoint('hello_world0 job beginning')

    read_the_config_file(jcx)
    
    write_and_read_a_csv_file(jcx)

    download_file_from_box(jcx)
     
    write_and_read_a_db_entry(jcx)

    #one last checkpoint to tell us how long the whole thing took
    jcx.checkpoint('hello_world0 job run complete')

    jcx.declare_success()#you can also declare_failure()
    return 

def read_the_config_file(jcx):
    #this job's config file is JSON format. 
    #JSON supports any combination and nesting
    #of hashmaps, lists, numbers, and strings. The top level is normally
    #a hashmap that you access as below
    config = jcx.get_config_jdata()

    example_param_0 = config['example_param_0'] 
    jcx.log("The value 'example_param_0' in the hello_world0.cfg " +
        "config file = '" + str(example_param_0) + "'")
    return

def write_and_read_a_db_entry(jcx):
    init_db_client_registry(jcx)

    #the name of the table we want to work with
    table_name = simplest_dto.COLLECTION_NAME
    client = jcx.runtime()['db_clients'][table_name]

    entry = SimplestDTO(message='hi')
    saved_entry = client.create_entry(entry)
    jcx.log('created an entry in postgres table: ' + table_name)
    jcx.log('the entry with the id that postgres assigned is: ' +
        str(saved_entry) + ', id = ' + str(saved_entry.id))

    nest_id = saved_entry.get_nest_id()

    read_entry = client.read_entry(nest_id)
    jcx.log('the entry if we read it back out by id should be the same: ' +
        str(read_entry))
    return

def init_db_client_registry(jcx):
    """
    create a dict of database clients for hello_world project's datatypes.
    put the dictionary in the jcx 'runtime' so that they are accessible as:
    jcx.runtime()['db_clients'][<datatype>]
    """
    #get the 'maker' objects for database tables and clients in
    #the hello_world project
    hw_sqla_makers = hw_db.get_sqla_makers()
    wix_db.init_db_clients(jcx, hw_sqla_makers)
    return

def write_and_read_a_csv_file(jcx):

    #when reading/writing csvs in python, the table is treated as a list of
    #rows, and every row is a dict of key-value pairs, where the key is a
    #column name and the value is the value of the table's cell. The columns
    #are unordered until you actually write the table to a file with 
    #a specified column ordered.
    #Here, I am making a table with 2 columns named 'id' and 'color' 
    #that looks like:
    #  
    # id,color  
    # 0,red 
    # 1,blue
    # 2,green

    list_of_rows = list()
    #make the rows with just an 'id' column
    for row_idx in range(0, 3):
        data_row = dict()
        data_row['id'] = row_idx
        list_of_rows.append(data_row)
    #add another 'column' called 'color' to the three rows
    list_of_rows[0]['color'] = 'red'
    list_of_rows[1]['color'] = 'blue'
    list_of_rows[2]['color'] = 'green'

    #make a filename for our csv
    tmp_relative_fn = 'color_table.csv' 

    #wix provides access to two data directories through the JobContext:
    # - 'get_run_file_space()' manage's a directory that only this run of the job
    #     can access. It's intended for results files.
    data_dir = jcx.get_run_file_space().get_dirpath()

    #the file goes in the working directory that wix gave us
    tmp_absolute_fn = os.path.join(data_dir, tmp_relative_fn)

    #the order we want the columns to be in the csv file
    column_names = ['id', 'color']

    #use our file_utils to write the csv file
    #unfortunately, you really need to use my file_utils or things can go
    #wrong involving docker and file permissions
    jcx_user = jcx.get_container_user()
    file_utils.dump_csv(tmp_absolute_fn, column_names, list_of_rows,
        file_owner=jcx_user, ensure_dir=True)

    #now read it back in, completing the roundtrip. this method actually
    #returns a dict where the key is the 'id' row, and the value should be
    #identical to the row we wrote out
    roundtrip_rows = file_utils.csv_file_to_nested_dict(tmp_absolute_fn, 'id')

    #note that everything comes back as strings when you read them back in,
    #which is why the 'id' that is read back in is not an int
    jcx.log("The color of row '1' before and after roundtrip: " +
        list_of_rows[1]['color'] + ", " + roundtrip_rows['1']['color'])

    return
    
def download_file_from_box(jcx):

    #note that the file must be shared as "anyone with the link"
    #and the url is the "direct" url in the advanced settings of 
    #the file on Box.com
    #the hello world data can be seen in a browser  here: 
    #https://uofi.app.box.com/files/0/f/8053049869/hello_world
    
    #the filename we will save the file as
    box_test_relative_fn = 'box_test_0.txt'

    #when downloading from box, we can use the data_dir that is
    #shared across job runs so we don't have to download it every time
    #the box downloader won't download if the file is already there
    data_dir = jcx.get_job_file_space().get_job_global_data_dir()

    box_test_fn = os.path.join(data_dir, box_test_relative_fn)

    jcx_user = jcx.get_container_user()

    box_url = 'https://uofi.box.com/shared/static/y8a7qmgskm73rpovf16j96yr3st7ea96.txt'
    #let's also log a checkpoint before and after to see
    #how long it takes
    jcx.checkpoint('Beginning download of : ' + box_url)
    box_downloads.download_from_box_no_auth(box_url, box_test_fn,
        file_owner=jcx_user, force=False)
    jcx.checkpoint('Download complete')

    #now we can read the file like a normal file:
    jcx.log('Printing contents of file: ' + box_test_fn)
    with open(box_test_fn, 'r') as filestream:
        for line in filestream:
            jcx.log(line)

    return 

