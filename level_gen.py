import sys
import struct

import numpy as np

VERBOSE = True # True if you want to see Exception errors & messages
HUMAN_READABLE = True # output 2 txt files when done

class Course():
    def __init__(self, course_name: str):
        self.course = self._read_decrypted(course_name) # raw course bytes
        self.file_info = self._init_data()

    def _read_decrypted(self, course_name: str) -> bytes:
        # load course data into memory
        with open(course_name, "rb") as f:
            course = f.read()

        return course

    def _init_data(self) -> list:
        # here we initialize some data structures for later
        file_info = list()
        obj_info = dict() # dict with mappings from object flags to object type e.g, {63: "Goomba"}

        with open("object_info.dat") as f:
            for line in f:
                line = line.split()
                obj_info[line[0]] = line[1]

        file_info.append(obj_info)
   
        """
        get level height/width (this doesn't seem very well documented)
        
        so there are a few ways this can be calculated (i think):
            1. take the max coords of all found objects/tiles
            2. get level goal (x, y) pos located in header
            3. https://github.com/switchjs/smm2data/blob/master/index.js#L22
                unsure why that works...
            4. https://github.com/RedDuckss/smm2-level-viewer/blob/master/app/assets/js/scene.js#L243
            5. assumption: _start/goal y_ pos are located at 0x0, 0x1 and are 0x1 in size.
                there is no mention of _start x pos_, BUT, _goal x pos_ is located at 0x2.
                for some reason the docs say its 0x2 size, which seems weird. so one can TRY
                and assume that 0x3 is _start x pos_

                this hasn't been true 100% of the time, but has worked in some cases...
        """
        #level_height = 27
        #level_width = int(((self.course[0x2] | self.course[0x3] << 8) + 95) / 10)
        #file_info.append(level_width)
        #file_info.append(level_height)

        # this doesn't always work... i think doors & subworlds fuck it
        goal_y_pos = self.course[0x1]
        goal_x_pos = self.course[0x2]

        file_info.append(goal_x_pos)
        file_info.append(goal_y_pos)

        course_header = self.course[:0x200]

        level_style = _decode(course_header[0xF1:0xF1 + 0x3])
        if level_style != "MW":
            raise Exception("game style needs to be Super Mario World!")
            exit()

        level_title = _decode(course_header[0xF4:0xF4 + 0x42])
        print(f"getting level data from... '{level_title}'")

        return file_info

def _decode(data: bytes):
    """
    helper function to decode some shit
    """
    return data.replace(b"\x00", b"").decode()

def _get_object_data(object_data: bytes, obj_count: int) -> dict:
    """
    returns a dictionary containing object information
        object_data: bytes from object_data section of file
        obj_count: total objects in level
        -------
        objects_info: {}
    """
    objects_info = dict()

    # each section is 0x20 bytes
    for i in range(obj_count):
        section_data = object_data[i * 0x20:(i * 0x20) + 0x20]

        # get tile postions which are from the block center in a 160x160 grid
        x_pos = struct.unpack("<I", section_data[:0x4])
        x_pos = int((x_pos[0] - 80) / 160)
        y_pos = struct.unpack("<I", section_data[0x4:0x8])
        y_pos = int((y_pos[0] - 80) / 160)

        # get tile width & height (for stuff like clouds & lifts)
        width = section_data[0xA]
        height = section_data[0xB]

        # raw object flags
        raw_flags = struct.unpack("<I", section_data[0xC:0x10])[0]
        wings = True if (raw_flags >> 1) & 1 else False
        parachute = True if (raw_flags >> 15) & 1 else False

        # get tile type
        object_type = section_data[0x18:0x1A].hex()[:2]

        objects_info[i] = {"x": x_pos, "y": y_pos, "width": width, "height": height,
            "raw_flags": raw_flags, "item_properties": (wings, parachute), "obj_type": object_type}

    return objects_info

def _get_tile_data(tile_data: bytes, tile_count: int) -> dict:
    """
    returns a dictionary containing tile information
        tile_data: bytes from tile_data section of file
        tile_count: total objects in level
        -------
        tile_info: {}
    """
    tile_info = dict()

    # range(tile_count) can also be replaced with range(4000)
    for i in range(4000):
        x_pos = tile_data[0x247A4 + (0x4 * i)]
        y_pos = tile_data[0x247A4 + (0x4 * i + 1)]

        tile_info[i] = {"x": x_pos, "y": y_pos}

    return tile_info

def get_level_data(course: bytes) -> tuple:
    """
    gets level data needed to build the course
        -------
    returns tuple() containing both object & tile info
    """
    course_data = course[0x200:0x2DEE0] # main course area after the HEADER

    obj_count = course_data[0x1C:0x1C + 0x4]
    obj_count = struct.unpack("<I", obj_count)[0] # little endian
    tile_count = course_data[0x3C:0x3C + 0x4]
    tile_count = struct.unpack("<I", tile_count)[0]

    # get course object data
    object_data = course_data[0x48:0x20 * 2600]
    objects = _get_object_data(object_data, obj_count)

    # get course tile data
    #tile_data = course[0x249A4:0x249A4 + (0x4 * tile_count)] # the format docs actually say 0x247A4 but w/e...
    tiles = _get_tile_data(course_data, tile_count)

    print("done!")

    return {"objects": objects, "tiles": tiles}

def build_ascii_course(level_data: dict, file_info: list):
    """
    builds ASCII course of level!
    """
    print("building ascii course!")

    objects_info = level_data["objects"]
    tile_info = level_data["tiles"]

    #level_mat = np.full((file_info[3] + 1, file_info[4] + 1), "-", dtype = str) # horizontal view
    level_mat = np.full((file_info[4] + 1, file_info[3] + 1), "-", dtype = str) # veritcal view
    print(f"level is {file_info[4]} by {file_info[3]}")

    for k, v in objects_info.items():
        object_type = file_info[0][v["obj_type"]][0]

        # pipes
        if object_type == "P":
            h = v["height"]

            # this was fucking mind-bending
            if not v["y"] - h < 0:
                level_mat[v["y"], v["x"] - 1] = "P"
                level_mat[h + 1:v["y"], v["x"]] = "P"
                level_mat[h + 1:v["y"], v["x"] - 1] = "P"

                #level_mat[v["y"] - h, v["x"]] = ">"
            else:
                level_mat[v["y"], v["x"] + 1] = "P"
                # @TODO

        # belts
        if object_type == "B":
            w = v["width"]

            level_mat[v["y"], v["x"]:v["x"] + w] = "B"
        try:
            #level_mat[v["x"], v["y"]] = object_type # horizontal
            level_mat[v["y"], v["x"]] = object_type # vertical
        except:
            if VERBOSE:
                print(f"can't place object at {v['x'], v['y']}")
            else:
                pass

    for k, v in tile_info.items():
        try:
            #level_mat[v["x"], v["y"]] = "X" # horizontal
            level_mat[v["y"], v["x"]] = "X" # vertical
        except:
            if VERBOSE:
                print(f"can't place tile at {v['x'], v['y']}")
            else:
                pass

    """
    assumption: all levels ive generated have tile blocks cut out from idx[0:8].
        i believe this is because nintendo FORCES these tiles as the starting tiles of the level
        and are therefore default, and for some reason not included in the tile data
        
        so, here, those tiles get automatically filled in so that they match up with the first tile
        data at idx[0, 8]~
    """
    level_mat = level_mat.T
    level_mat[:7, 0] = "X"
    if level_mat[7, 1] == "X":
        level_mat[:7, 1] = "X"

    # place goal if it hasn't already been placed...
    #level_mat[file_info[2], file_info[1]] = "W"

    return level_mat

def _(level: list) -> list:
    new_level = list(zip(*level))[::-1]
    ["".join(new_level[i]) for i in range(len(new_level))]
    return new_level

if __name__ == "__main__":
    course_name = sys.argv[1]

    course = Course(course_name)
    course_data = course.course

    level_data = get_level_data(course_data)

    # need to figure out how to get exact/accurate level dimensions... refer to _init_data()
    _obj_width = max(x["x"] for x in level_data["objects"].values())
    _tile_width = max(x["x"] for x in level_data["tiles"].values())
    level_width = max(_obj_width, _tile_width)
    del _obj_width, _tile_width

    level_height = max([y["y"] for y in level_data["objects"].values()])
    level_height = level_height if level_height > 27 else 27 # ugly lol

    course.file_info.append(level_width)
    course.file_info.append(level_height)

    level_mat = build_ascii_course(level_data, course.file_info)
    _ = course_name.split("bcd")[-2].split("/")[-1]
    np.savetxt(f"{_}txt", level_mat, fmt = "%s", delimiter = "")

    if HUMAN_READABLE:
        np.savetxt(f"HR_{_}txt", np.flipud(level_mat.T), fmt = "%s", delimiter = "")
