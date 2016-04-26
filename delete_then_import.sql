delete from USER_RATING;
delete from STARRED_MEDIA_FILE;
delete from PLAYLIST_FILE; delete from PLAYLIST;

\i output/import_ratings.sql
\i output/import_starreds.sql
\i output/import_playlists.sql

\=
