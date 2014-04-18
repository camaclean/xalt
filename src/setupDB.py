#!/usr/bin/env python
# -*- python -*-
from __future__ import print_function
import os, sys, re, base64
import MySQLdb, ConfigParser, getpass, time
import warnings
warnings.filterwarnings("ignore", "Unknown table.*")

ConfigBaseNm = "xalt_db"
ConfigFn     = ConfigBaseNm + ".conf"

def readFromUser():
  global HOST,USER,PASSWD,DB
  HOST=raw_input("Database host:")
  USER=raw_input("Database user:")
  PASSWD=getpass.getpass("Database pass:")
  DB=raw_input("Database name:")

def writeConfig():
  config=ConfigParser.ConfigParser()
  config.add_section("MYSQL")
  config.set("MYSQL","HOST",HOST)
  config.set("MYSQL","USER",USER)
  config.set("MYSQL","PASSWD",base64.b64encode(PASSWD))
  config.set("MYSQL","DB",DB)

  t=time.strftime("%m%d%H%M%Y")
  f=open(ConfigBaseNm+t,'w')
  config.write(f)
  f.close()
  os.chmod(ConfigBaseNm+t,0640)
  if (os.path.exists(ConfigFn)):
    os.remove(ConfigFn)
  os.symlink(ConfigBaseNm+t,ConfigFn)

def readConfig():
  try:
    global HOST,USER,PASSWD,DB
    config=ConfigParser.ConfigParser()
    config.read(ConfigFn)
    HOST=config.get("MYSQL","HOST")
    USER=config.get("MYSQL","USER")
    PASSWD=base64.b64decode(config.get("MYSQL","PASSWD"))
    DB=config.get("MYSQL","DB")
  except ConfigParser.NoOptionError, err:
    sys.stderr.write("\nCannot parse the config file\n")
    sys.stderr.write("Switch to user input mode...\n\n")
    readFromUser()



def main():
  if(os.path.exists('xalt_db.conf')):
    print ("XALT database configuration file exists!")
    q=raw_input("Do you want to use the file to fill database information?[y/n]")
    if(q.lower() == "y"):
      readConfig()
    else:
      readFromUser()
  else:
    readFromUser()

  # connect to the MySQL server
  try:
    conn = MySQLdb.connect (HOST,USER,PASSWD)
  except MySQLdb.Error, e:
    print ("Error %d: %s" % (e.args[0], e.args[1]))
    sys.exit (1)

  #writeConfig()
  # create database and related tables
  try:
    cursor = conn.cursor()

    # If MySQL version < 4.1, comment out the line below
    cursor.execute("SET SQL_MODE=\"NO_AUTO_VALUE_ON_ZERO\"")
    # If the database does not exist, create it, otherwise, switch to the database.
    cursor.execute("CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci" % DB)
    cursor.execute("USE "+DB)

    idx = 1


    print("start")

    # 1
    cursor.execute("""
        CREATE TABLE `xalt_link` (
          `link_id`       int(11)        NOT NULL auto_increment,
          `uuid`          char(36)       NOT NULL,
          `hash_id`       char(40)       NOT NULL,
          `build_user`    varchar(64)    NOT NULL,
          `build_host`    varchar(64)    NOT NULL,
          `build_epoch`   double         NOT NULL,
          `exit_code`     tinyint(4)     NOT NULL,
          `exec_path`     varchar(1024)  NOT NULL,
          PRIMARY KEY  (`link_id`),
          UNIQUE  KEY  `uuid` (`uuid`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1
        """)
    print("(%d) create xalt_link table" % idx); idx += 1

    # 2
    cursor.execute("""
        CREATE TABLE `xalt_library` (
          `lib_id`        int(11)         NOT NULL auto_increment,
          `library_path`  varchar(1024)   NOT NULL,
          `uuid`          char(36)                ,
          `hash_id`       char(40)        NOT NULL,
          `lib_type`      char(2)         NOT NULL,
          PRIMARY KEY  (`lib_id`),
          INDEX  `index_uuid`    (`uuid`),
          INDEX  `index_hash_id` (`hash_id`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1
        """)
    print("(%d) create xalt_library table" % idx ); idx += 1;


    # 3
    cursor.execute("""
        CREATE TABLE `join_link_library` (
          `join_id`       int            NOT NULL auto_increment,
          `lib_id`        int(11)        NOT NULL,
          `link_id`       int(11)        NOT NULL,

          PRIMARY KEY (`join_id`),
          FOREIGN KEY (`link_id`) REFERENCES `xalt_link`(`link_id`),
          FOREIGN KEY (`lib_id`)  REFERENCES `xalt_library`(`lib_id`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1
        """)
    print("(%d) create join_link_library table" % idx); idx += 1

    # 4
    cursor.execute("""
        CREATE TABLE `xalt_job` (
          `run_id`        int(11)        NOT NULL auto_increment,
          `job_id`        int(11)        NOT NULL,
          `host`          varchar(64)    NOT NULL,
          `uuid`          char(36)               ,
          `hash_id`       char(40)       NOT NULL,
          `account`       char(11)       NOT NULL,
          `exec_type`     char(7)        NOT NULL,
          `build_user`    varchar(64)    NOT NULL,
          `start_time`    double         NOT NULL,
          `end_time`      double         NOT NULL,
          `run_time`      double         NOT NULL,
          `num_cores`     int(11)        NOT NULL,
          `num_nodes`     int(11)        NOT NULL,
          `num_threads`   tinyint(4)     NOT NULL,
          `queue`         varchar(32)    NOT NULL,
          `user`          varchar(32)    NOT NULL,
          `exec_path`     varchar(1024)  NOT NULL,
          PRIMARY KEY            (`run_id`),
          INDEX  `index_uuid`    (`uuid`),
          INDEX  `index_hash_id` (`hash_id`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1
        """)
    print("(%d) create xalt_job table" % idx)
    idx += 1

    # 5
    cursor.execute("""
        CREATE TABLE `join_job_library` (
          `join_id`       int            NOT NULL auto_increment,
          `lib_id`        int(11)        NOT NULL,
          `run_id`        int(11)        NOT NULL,

          PRIMARY KEY (`join_id`),
          FOREIGN KEY (`run_id`)  REFERENCES `xalt_job`(`run_id`),
          FOREIGN KEY (`lib_id`)  REFERENCES `xalt_library`(`lib_id`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1
        """)
    print("(%d) create join_job_library table" % idx); idx += 1


    # 6
    cursor.execute("""
        CREATE TABLE `xalt_env_name` (
          `env_id`        int           NOT NULL auto_increment,
          `env_name`      varchar(64)   NOT NULL,
          PRIMARY KEY  (`env_id`),
          UNIQUE  KEY  `env_name` (`env_name`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1
        """)
    print("(%d) create xalt_env_name table" % idx); idx += 1

    # 7
    cursor.execute("""
        CREATE TABLE `join_job_env` (
          `join_id`       int            NOT NULL auto_increment,
          `env_id`        int            NOT NULL,
          `run_id`        int(11)        NOT NULL,
          `env_value`     varchar(512)   NOT NULL,
          PRIMARY KEY (`join_id`),
          FOREIGN KEY (`env_id`)  REFERENCES `xalt_env_name`(`env_id`),
          FOREIGN KEY (`run_id`)  REFERENCES `xalt_job`(`job_id`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1
        """)
    print("(%d) create join_job_env table" % idx); idx += 1


    cursor.close()
  except  MySQLdb.Error, e:
    print ("Error %d: %s" % (e.args[0], e.args[1]))
    sys.exit (1)

if ( __name__ == '__main__'): main()