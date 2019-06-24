# subsonic_migrate
A collection of simple scripts to export (.dsv) existing Subsonic ratings, starred entries and playlists, and to import them into a new installation.

## Prerequisites
This procedures assumes the source (migrated-from) and destination (migrated-to) have the same media folders' organisation and content, because the files are matched by their absolute path.

* HSQLDB sqltool command line should be available on your system (on Ubuntu: apt-get install hsqldb-utils). **IMPORTANT**: Version 1.8 is required, it won't work with version 2. In v 1.8, the utilities are a class in the main `hsqldb` jar
 * Configure it to get access to your subsonic db (under Linux, the path is /var/subsonic/db/subsonic), creating a sqltool.rc file
 ```
 # A personal, local, persistent database.
 urlid subsonic
 url jdbc:hsqldb:file:$PATH_TO_DB;shutdown=true
 username SA
 password
 # When connecting directly to a file database like this, you should
 # use the shutdown connection property like this to shut down the DB
 # properly when you exit the JVM.
 ```
 * Test access to it: ```sudo -u $SUBSONIC_USER hsqldb-sqltool --rcFile sqltool.rc subsonic```
 
## Usage
### Export
1. Stop the ***migrated-from*** Subsonic
2. Dump the table as dsv by running export.sql from this repository (on Linux: ```sudo -u $SUBSONIC_USER hsqldb-sqltool --rcFile sqltool.rc subsonic export.sql```)
3. Move the generated files under data/source


### Import
1. Stop the ***migrated-to*** Subsonic
2. Dump the table as dsv by running export.sql from this repository (on Linux: ```sudo -u $SUBSONIC_USER hsqldb-sqltool --rcFile sqltool.rc subsonic export.sql```)
3. Move the generated files under data/destination
4. Run ```main.py```, which will generate import SQL scripts in the output/ folder.
5. Import the data from the scripts. Note that it will first delete any existing ratings, playlists, and stars. (on Linux: ```sudo -u $SUBSONIC_USER hsqldb-sqltool --rcFile sqltool.rc subsonic delete_then_import.sql```)
