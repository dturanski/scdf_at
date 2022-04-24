__copyright__ = '''
Copyright 2022 the original author or authors.
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
      http://www.apache.org/licenses/LICENSE-2.0
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
'''

__author__ = 'David Turanski'


import os
import psycopg2
import time
import cx_Oracle
import traceback
import logging

from cloudfoundry.platform.config.db import DatasourceConfig

logger = logging.getLogger(__name__)


def get_traceback(e):
    lines = traceback.format_exception(type(e), e, e.__traceback__)
    return ''.join(lines)


def db_name(prefix, db_config, binder):
    if db_config.provider == 'oracle':
        return 'xe'
    db_index = db_config.index
    return "%s_pro_1_5_0_%s_%s" % (prefix, binder, db_index)


def init_postgres_db(db_config, dbname):
    logger.info("initializing postgresql DB %s..." % (dbname))
    conn = None
    try:
        # Connect to the postgres (admin) database to drop/create target database
        conn = psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            dbname='postgres',
            connect_timeout=5)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = %s;", (dbname,))
            live_connections = cur.fetchone()[0]
            logger.debug("DB %s has %d live connections" % (dbname, live_connections))
            while live_connections > 0:
                # Terminate any existing connections to the database
                cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s;", (dbname,))
                time.sleep(1.0)
                cur.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = %s;", (dbname,))
                live_connections = cur.fetchone()[0]
                logger.debug("DB %s has %d live connections" % (dbname, live_connections))

            cur.execute("DROP DATABASE IF EXISTS %s;" % dbname)
            cur.execute("CREATE DATABASE %s;" % dbname)
            logger.info("completed initialization of postgresql DB %s" % (dbname))
    except (psycopg2.DatabaseError, psycopg2.OperationalError) as e:
        # If we fail, continue anyway
        logger.error(f'Error {e}')
    finally:
        if conn:
            conn.close()


def init_oracle_db(db_config, dbname):
    logger.info("initializing Oracle DB %s..." % (dbname))
    conn = None
    try:
        CONN_INFO = {
            'host': db_config.host,
            'port': db_config.port,
            'user': 'SYSTEM',
            'psw': db_config.password,
            'service': 'xe',
        }
        conn_str = '{user}/{psw}@{host}:{port}/{service}'.format(**CONN_INFO)
        conn = cx_Oracle.connect(conn_str)
        # todo: set connect_timeout
        with conn.cursor() as cur:
            try:
                cur.execute('ALTER SESSION SET "_ORACLE_SCRIPT"=TRUE')
                cur.execute("SELECT sid,serial# FROM v$session where username='%s'" % (db_config.username.upper()))
                for row in cur.fetchall():
                    logger.debug("killing session " + str(row))
                    cur.execute("ALTER SYSTEM kill session '%s,%s' immediate" % row)
                cur.execute("DROP USER %s CASCADE" % db_config.username)
            except cx_Oracle.DatabaseError as e:
                logger.error(get_traceback(e))
            finally:
                cur.execute("CREATE USER %s IDENTIFIED BY %s" % (db_config.username, db_config.password))
                cur.execute("GRANT ALL PRIVILEGES TO %s" % db_config.username)
                logger.info("completed initialization of DB %s" % dbname)

    except cx_Oracle.DatabaseError as e:
        # If we fail, continue anyway
        logger.error(get_traceback(e))
    finally:
        if conn:
            conn.close()


def init_db(config):
    db = config.db_config
    if not (db and db.provider):
        logging.info("'database provider' is not defined. Skipping external DB initialization.")
        return

    binder = config.test_config.binder
    if db.provider in ['postgresql', 'postgres']:
        init_postgres_db(db, db_name('skipper', db,binder))
        init_postgres_db(db, db_name('dataflow', db, binder))
        skipper_url = "jdbc:postgresql://%s:%d/%s?user=%s&password=%s" % (db.host, int(db.port),
                                                                     db_name('skipper', db, binder),
                                                                     db.username,
                                                                     db.password)
        dataflow_url = "jdbc:postgresql://%s:%d/%s?user=%s&password=%s" % (db.host, int(db.port),
                                                                      db_name('dataflow', db, binder),
                                                                      db.username,
                                                                      db.password)
        driver_class_name = 'org.postgresql.Driver'
    elif db.provider == 'oracle':
        lib_dir = os.getenv('LD_LIBRARY_PATH')
        if lib_dir:
            logger.debug("Initializing oracle client in %s" % lib_dir)
        else:
            raise ValueError("Error initializing Oracle. 'LD_LIBRARY_PATH' is not defined. \n" +
                             "Should be where the oracle client libs are installed")
        cx_Oracle.init_oracle_client(lib_dir=lib_dir)
        '''Oracle would need to create different user for each. Using shared DB here'''
        init_oracle_db(db, 'xe')
        skipper_url = dataflow_url = "jdbc:oracle:thin:%s:%d:xe" % (db.host, int(db.port))
        driver_class_name = 'oracle.jdbc.OracleDriver'
    else:
        raise ValueError("Sorry, SQL provider %s is invalid or unsupported." % db.provider)

    datasource_configs = {
        "dataflow": DatasourceConfig(url=dataflow_url,
                                     username=db.username,
                                     password=db.password,
                                     driver_class_name=driver_class_name),
        "skipper": DatasourceConfig(url=skipper_url,
                                    username=db.username,
                                    password=db.password,
                                    driver_class_name=driver_class_name),
    }
    return datasource_configs
