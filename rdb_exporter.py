from prometheus_client import start_http_server, Gauge
from subprocess import Popen, PIPE
import configparser
import os
import fdb
from itertools import islice
from datetime import date
import re

def readConfig(config_path='./rdb_exporter_config.cfg'):
    '''
    returns config file
    '''
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
    except Exception:
        print(f'Check your {config_path} config file!')
        return None
    else:
        return config     

def gstat_scrape(gstat_path, database_path):
    with Popen(
        [gstat_path, '-h', database_path], 
        stdout=PIPE, 
        bufsize=1, 
        universal_newlines=True
    ) as gstat:
        gstat_stdout = gstat.stdout.read().split('\n')
        OIT = gstat_stdout[11].split('\t')[-1]
        OAT = gstat_stdout[12].split('\t')[-1]
        NT  = gstat_stdout[14].split('\t')[-1]
        OIT, OAT, NT = list(map(int, [OIT, OAT, NT]))
            
        gauge_OAT_OIT_difference.set(OAT - OIT)
        gauge_NT_OIT_difference.set(NT - OIT)


def db_size_scrape(database_path):
    if os.path.exists(database_path):
        db_size_mb = os.path.getsize(database_path) * 1.0

        gauge_database_size.set(db_size_mb/1024/1024)

def attachments_scrape(hostname, database_path, user_name, password, fb_library_name):
    try:
        con = fdb.connect(
            host=hostname,
            database=database_path, 
            user=user_name,
            password=password,
            charset='UTF8',
            fb_library_name=fb_library_name
        )
        cur = con.cursor()
        cur.execute('select count(*) from MON$ATTACHMENTS')

        gauge_database_attachments.set(cur.fetchall()[0][0])
    except:
        print('Database connection is not established')    


def replication_scrape(database_path):
    pass

def PID_scrape(database_path):
    pass

def find_date(line):
    if (m := re.search(
        pattern=r'(Jan)*(Feb)*(Mar)*(Apr)*(May)*(Jun)*(Jul)*(Aug)*(Sep)*(Oct)*(Nov)*(Dec)*\s[0-9]{1,2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}\s[0-9]{4}',
        string=line
    )) is not None:
        return m[0]
    else:
        return None  

def log_errors_scrape(firebird_log_path, index):
    today = date.today()
    day = today.strftime('%d')
    mon = today.strftime('%B')[:3]
    year =today.strftime('%Y')
    file = open(firebird_log_path, 'r')
    lines = islice(file, index, None)
    check = False
    text = ''
    for line in lines:
        if check:
            text += line
        elif (s := find_date(line)) is not None:
            spl = s.split(' ')
            if day == spl[1] and mon == spl[0] and year == spl[-1]:
                check = True
        index += 1
    Fcc = text.count('Firebird consistency check')
    Err_read = text.count('Error while trying to read from file')
    Err_write = text.count('Error while trying to write to file')
    gauge_Err_consistency.set(Fcc)
    gauge_Err_read.set(Err_read)
    gauge_Err_write.set(Err_write)
    return index
    

def process_request(config) -> None:
    '''
    1.Run gstat in a loop and update stats per line
    2.Check size of database file
    3.Get amount of attachments to database
    4.fbreplmgr replication check
    5.PID check rdb_lock_print
    6.Firebird log error scraping (0 in 0:00:00 every day)
    '''
    index = 0
    up.set(1)
    gstat_scrape(config['PATHS']['gstat'], config['PATHS']['database'])
    db_size_scrape(config['PATHS']['database'])
    attachments_scrape(
        config['DATABASE']['host'],
        config['PATHS']['database'],
        config['DATABASE']['username'],
        config['DATABASE']['password'],
        config['PATHS']['fb_library_name']
    )
    # replication_scrape(config['PATHS']['database'])
    # PID_scrape(config['PATHS']['database'])
    index = log_errors_scrape(config['PATHS']['firebird_log'], index)


up = Gauge(
    'up', 
    'The value of this Gauge is always 1 when the exporter is up'
)

gauge_OAT_OIT_difference = Gauge(
    'gstat_OAT_OIT_difference',
    'The difference between oldest active transaction and oldest transaction',
)
gauge_NT_OIT_difference = Gauge(
    'gstat_NT_OIT_difference',
    'The difference between next transaction and oldest transaction',
)
gauge_database_size = Gauge(
    'database_size',
    'The database size',
)
gauge_database_attachments = Gauge(
    'database_attachments',
    'The count of attachments to the database',
)
gauge_Err_consistency = Gauge(
    'Firebird_Err_consistency',
    'The amount of consistency error in firebird log file today',
)
gauge_Err_read = Gauge(
    'Firebird_Err_read',
    'The amount of reading error in firebird log file today',
)
gauge_Err_write = Gauge(
    'Firebird_Err_write',
    'The amount of writing error in firebird log file today',
)

config = readConfig()
if config is not None:
    start_http_server(int(config['EXPORTER']['port']))
    while True:
        process_request(config)
    else:
        up.set(0)    