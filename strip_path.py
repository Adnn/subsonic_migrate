#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections, os

def path_elements(path):
    head, tail = os.path.split(path)
    if head and head != "/":
        return path_elements(head) + [tail] 
    else:
        return [tail]

def trim_path_elements(path):
    return os.path.join("/", *[element.strip() for element in path_elements(path)])

def fixup_file(input_filename):
    values = []

    with open(input_filename, "r") as f:
        firstline = f.readline()
        TupleType = collections.namedtuple("{base}_Tuple".format(base=os.path.splitext(os.path.basename(input_filename))[0]),
                                           firstline.strip().split("|"))
        if hasattr(TupleType, "PATH"):
            print "fixing path for file '{file}'".format(file=input_filename)
            with open(input_filename+"_fix", "w") as w:
                w.write(firstline)
                for line in f.readlines():
                    data = TupleType(*line.strip().split("|"))
                    modifiable = data._asdict()
                    modifiable["PATH"] = trim_path_elements(data.PATH)
                    w.write("|".join(TupleType(**modifiable))+"\n")


fixup_file("src_cpy/MEDIA_FILE.dsv")
fixup_file("src_cpy/USER_RATING.dsv")
