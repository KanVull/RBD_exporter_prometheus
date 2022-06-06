# RDB_exporter_prometheus
## Scraping most of useful metrics of reddatabase
This exporter scrape metrics of your database:
- Database size in MBs
- Database attachments
- Gstat 
- - difference between Oldest active transaction and Oldest interesting transaction
- - difference between Next transaction and Oldest interesting transaction
- Firebird.log 
- - "Firebird consistency check" daily count
- - "Error while trying to read from file" daily count
- - "Error while trying to write to file" daily count

# Installing
## Prometheus enviroment
[Prometheus](https://prometheus.io/) to download the latest version

Configuring prometheus.yml file by additing metrics job
```
global:
  scrape_interval: 15s
  scrape_timeout: 10s
  evaluation_interval: 15s
scrape_configs:
- job_name: rdb_exporter
  honor_timestamps: true
  scrape_interval: 10s
  scrape_timeout: 10s
  metrics_path: /metrics
  scheme: http
  follow_redirects: true
  enable_http2: true
  static_configs:
  - targets:
    - localhost:9248
```
**Port in targets must be changed to your port (9248 by default)**
Prometheus will be scraping your database metrics with time interval equal scrape_interval variable in job area

## Grafana grafic enviroment
[Dowload Grafana](https://grafana.com/) to download the latest version

For running nicely dashboard view of your metrics you must import [Grafana DashBoard](Grafana_RDB_DashBoard.json) file into your grafana dashboads (by default it located in [localhost:3000](https://localhost:3000))

## RDB_Exporter
Python version 3.6+
Create virtualenv in project dir
```
virtualenv Env
```
Run creating enviroment
```
source Env/bin/activate
pip install -r requirements.txt
```

Configure project in rdb_exporter_config.cfg file
Example:
```
[EXPORTER]
port = 9248

[PATHS]
gstat = /opt/RedDatabase/bin/gstat
database = /var/rdb/tpcc.fdb
fb_library_name = /opt/RedDatabase/lib/libfbclient.so
firebird_log = /opt/RedDatabase/firebird.log

[DATABASE]
host = localhost
username = SYSDBA
password = masterkey
```

Run code easily by 
```
python3 rdb_exporter.py
```

After that you shall see [localhost:9248](https://localhost:9248) for your metrics
If this work, grafana will be scraping and show you your metrics in nicely humanize graffical format

**2022**