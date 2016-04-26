#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections, os

def get_media_mapping(input_filename):
    """ Should receive the MEDIA_FILE.dsv export of the source (migrated-from) installation """
    """ in order to generate two dictionaries mapping (for each line) the "media file" path (resp. ID) """
    """ to a NamedTuple containing all the fields of the line. """
    name_mapping = {}
    id_mapping = {}
    with open(input_filename, "r") as f:
        LineTuple = collections.namedtuple("LineTuple", f.readline().strip().split("|"))
        for line in f.readlines():
            fields = LineTuple(*line.strip().split("|"))
            name_mapping[fields.PATH] = (fields)
            id_mapping[fields.ID] = (fields)
 
    return name_mapping, id_mapping

def get_content(input_filename, dict_keys=[]):
    values = []

    dictionaries = []
    for key in dict_keys:
        dictionaries.append({})

    with open(input_filename, "r") as f:
        TupleType = collections.namedtuple("{base}_Tuple".format(base=os.path.splitext(os.path.basename(input_filename))[0]),
                                           f.readline().strip().split("|"))
        for line in f.readlines():
            data = TupleType(*line.strip().split("|"))
            values.append(data)

            for index, key in enumerate(dict_keys):
                dictionaries[index][getattr(data, key)] = data

    if dict_keys:
        return values, dictionaries
    else:
        return values


#gUSR_RATING = "INSERT INTO USER_RATING VALUES('adn','/var/subsonic/Music/Albums/65daysofstatic/[2007] The Destruction of Small Ideas',2.0E0)"
gUSR_RATING = "INSERT INTO USER_RATING VALUES('{username}','{filename}',{rating}E0)"
#gSTARRED    = "INSERT INTO STARRED_MEDIA_FILE VALUES(0,45070,'adn','2016-04-24 20:28:40.719000000')"
gSTARRED    = "INSERT INTO STARRED_MEDIA_FILE VALUES({pk},{media_file_id},'{username}','{created}')"
#gPLAYLIST       = "INSERT INTO PLAYLIST VALUES(1,'adn',TRUE,'playlist_julie','commentatort!',1,222,'2016-04-24 20:28:49.366000000','2016-04-24 20:29:37.984000000',NULL)"
gPLAYLIST       = "INSERT INTO PLAYLIST VALUES({id},'{username}',{is_public},'{name}','{comment}',{file_count},{duration_seconds},'{created}','{changed}',{imported_from})"
gPLAYLIST_FILE  = "INSERT INTO PLAYLIST_FILE VALUES({id},{playlist_id},{media_file_id})"

username_map = {
    "admin": "adn",
    "AdN": "adn",
    "pegazuss": "adn",
    "pibi": "FranzP",
}

def translate(dico, value):
    return dico.get(value, value)

def translate_id(source_id, source_id_map, dest_name_map):
   path = source_id_map[source_id].PATH
   destination_media_file = dest_name_map.get(path)
   return destination_media_file.ID if destination_media_file else None

def write_file(filename, statements):
    with open(filename, "w") as out:
        map(lambda x: out.write(x+";\n"), statements)

def fix_name(name):
    if name == "[null]": # internal token used by HSQLDB to represent null value, creates internal errors if inserted
        return ""
    return name.replace("'", "''")

if __name__ == "__main__":
    source_name_mapping, source_id_mapping = get_media_mapping("data/source/MEDIA_FILE.dsv")
    destination_name_mapping, destination_id_mapping = get_media_mapping("data/destination/MEDIA_FILE.dsv")
    users, (username_mapping,) = get_content("data/destination/USER.dsv", ["USERNAME",] )


    #
    # RATINGS
    #
    ratings = get_content("data/source/USER_RATING.dsv")
    usernames = set()
    rating_statements = []
    #user_to_files_to_ratings = {} ## In case the translation tables make the same target user have several ratings for the same media...
    not_founds = {}
    for rating in ratings:
        usernames.add(rating.USERNAME)
        source = source_name_mapping.get(rating.PATH)
        destination = destination_name_mapping.get(rating.PATH)
        translated_user = translate(username_map, rating.USERNAME)
        if not source:
            not_founds.setdefault(translated_user, []).append(("SOURCE", rating,))
        elif not destination:
            not_founds.setdefault(translated_user, []).append(("DESTINATION", rating,))
        elif translated_user not in username_mapping:
            print("[WARN] The entry '{path}' with rating {rating} by {user} does not have a matching user in the DESTINATION: not importing it.".format(path=rating.PATH, rating=rating.RATING, user=rating.USERNAME))
        else:
            if source.TYPE != "ALBUM":   
                print("[INFO] The entry {path} has type {type}.".format(path=rating.PATH, type=source.TYPE))
            rating_statements.append(gUSR_RATING.format(username=translated_user, filename=fix_name(rating.PATH), rating=rating.RATING))
            #user_to_files_to_ratings.get(translated_user, {}).get(rating.PATH, []).append(rating.RATING)

    #print("UNIQUE users: {users}".format(users=usernames))
    for user, missings in not_founds.items():
        print("[WARN] The user {user} has ratings that cannot be matched: not importing them.".format(user=user))
        for side, rating in missings:
            print("\t* The entry '{path}' with rating {rating} was not found in the {side} media files.".format(path=rating.PATH, rating=rating.RATING, side=side))

    write_file("output/import_ratings.sql", rating_statements)


    #
    # STARREDS
    #
    starreds = get_content("data/source/STARRED_MEDIA_FILE.dsv")
    starred_statements = []
    for index, starred in enumerate(starreds):
        translated_user = translate(username_map, starred.USERNAME)
        if translated_user not in username_mapping:
            print("[WARN] The media file '{path}' was starred by {user}, which does not have a matching user in the DESTINATION: not importing it."
                    .format(path=source_id_mapping[starred.MEDIA_FILE_ID].PATH, user=translated_user))
            continue

        destination_id = translate_id(starred.MEDIA_FILE_ID, source_id_mapping, destination_name_mapping)
        if destination_id is None:
            print("[WARN] The media file '{path}' starred by {user} does not exist in the DESTINATION: not importing it."
                    .format(path=source_id_mapping[starred.MEDIA_FILE_ID].PATH, user=translated_user))
            continue

        starred_statements.append(gSTARRED.format(pk=index, media_file_id=destination_id, username=translated_user, created=starred.CREATED))

    write_file("output/import_starreds.sql", starred_statements)
        
    #
    # PLAYLISTS
    #
    playlists = get_content("data/source/PLAYLIST.dsv")
    playlist_files = get_content("data/source/PLAYLIST_FILE.dsv")

    def make_playlistid_to_playlistfiles(values):
        result = {}
        for line in values:
            filelist = result.setdefault(line.PLAYLIST_ID, [])
            filelist.append(line)
        return result

    playlistid_to_playlistfiles = make_playlistid_to_playlistfiles(playlist_files)

    playlist_statements = []
    playlist_file_statements = []
    for index, playlist in enumerate(playlists):
        translated_user = translate(username_map, playlist.USERNAME)
        if translated_user not in username_mapping:
            print("[WARN] The playlist '{playlist}' by {user} does not have a matching user in the DESTINATION: not importing it.".format(playlist=playlist.NAME, user=playlist.USERNAME))
        else:
            playlist_statements.append(gPLAYLIST.format(id=index, username=translated_user, is_public="TRUE", name=fix_name(playlist.NAME), comment=fix_name(playlist.COMMENT),
                                                        file_count=playlist.FILE_COUNT, duration_seconds=playlist.DURATION_SECONDS, created=playlist.CREATED, changed=playlist.CHANGED,
                                                        imported_from="NULL"))
            filelist = playlistid_to_playlistfiles.get(playlist.ID, [])
            if not filelist:
                print("The playlist '{playlist}' by {user} is empty: not importing it.".format(playlist=playlist.NAME, user=playlist.USERNAME))
                playlist_statements.pop()
            for pl_file in filelist:
                destination_id = translate_id(pl_file.MEDIA_FILE_ID, source_id_mapping, destination_name_mapping)
                if destination_id is None:
                    print("[WARN] The media file '{path}' in playlist '{playlist}' does not exist in the DESTINATION: not importing it."
                            .format(path=source_id_mapping[pl_file.MEDIA_FILE_ID].PATH, playlist=playlist.NAME))
                    continue
                playlist_file_statements.append(gPLAYLIST_FILE.format(id=pl_file.ID, playlist_id=index, media_file_id=destination_id))

    write_file("output/import_playlists.sql", playlist_statements + playlist_file_statements)
