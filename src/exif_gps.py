import datetime

import gpxpy
import pandas as pd
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def read_gpx_dataframe(file_name, deltaMS):

    with open(file_name, "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    delta = datetime.timedelta(0, deltaMS)
    gpx.adjust_time(delta)

    points = []

    for track in gpx.tracks:
        for segment in track.segments:
            previous_point = None
            for point in segment.points:
                if previous_point is not None:
                    delta_time = point.time_difference(previous_point)
                    if delta_time == 0:
                        continue

                    ele = point.elevation
                    latitude = point.latitude
                    longitude = point.longitude

                    dateTime = point.time.strftime("%Y:%m:%d %H:%M:%S")
                    points.append((dateTime, latitude, longitude, ele, delta_time))

                previous_point = point

    df = pd.DataFrame(points)
    df.columns = ["dateTime", "latitude", "longitude", "elevation", "deltaTime"]

    return df


#Get the exif of a file
def get_exif(filename):
    image = Image.open(filename)
    image.verify()
    return image._getexif()


#Get the labeled exif of a raw _getexif() def
def get_labeled_exif(exif):
    labeled = {}
    for (key, val) in exif.items():
        labeled[TAGS.get(key)] = val

    return labeled

def get_geotagging(exif):
    if not exif:
        raise ValueError("No EXIF metadata found")

    geotagging = {}
    for (idx, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if idx not in exif:
                raise ValueError("No EXIF geotagging found")

            for (key, val) in GPSTAGS.items():
                if key in exif[idx]:
                    geotagging[val] = exif[idx][key]

    return geotagging

def get_geotagging(exif):
    if not exif:
        raise ValueError("No EXIF metadata found")

    geotagging = {}
    for (idx, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if idx not in exif:
                raise ValueError("No EXIF geotagging found")

            for (key, val) in GPSTAGS.items():
                if key in exif[idx]:
                    geotagging[val] = exif[idx][key]

    return geotagging



def get_Tag(exif, targetTag):
    ret = {}
    if not exif:
        raise ValueError("No EXIF metadata found")

    for (tag, value) in exif.items():
        decoded = TAGS.get(tag)
        ret[decoded] = value

    return ret[targetTag]


def increment_time(timeString, seconds):
    a = datetime.datetime.strptime(timeString, "%Y:%m:%d %H:%M:%S")
    b = a + datetime.timedelta(seconds=seconds)
    c = b.strftime("%Y:%m:%d %H:%M:%S")
    return c

def analyse_single_photo(path_single_photo, path_gpx_file, utc_offset_seconds):
    from pathlib import Path
    img = Path(path_single_photo)
    parsed_gpx = read_gpx_dataframe(path_gpx_file, utc_offset_seconds)
    analyse(img, parsed_gpx)


def analyse(img, parsed_gpx):


    exif = get_exif(img)
    dateOriginal = get_Tag(exif, 'DateTimeOriginal')
    #print(f"Analysing '{img.name}', taken at {dateOriginal}")

    if dateOriginal < parsed_gpx.iloc[0]['dateTime']:
        print(
            f"Picture taken before gpx track starts. first point => {parsed_gpx.iloc[0]['dateTime']}, pic.time => {dateOriginal}")

    if dateOriginal > parsed_gpx.iloc[-1]['dateTime']:
        print(
            f"Picture taken after gpx track ended. last point => {parsed_gpx.iloc[-1]['dateTime']}, pic.time => {dateOriginal}")

    previous_point = None
    for index, point in parsed_gpx.iterrows():

        if previous_point is not None:
            i = 0
            time_cursor = previous_point['dateTime']
            delta = point['deltaTime']
            if delta > 1:
                while i < delta:
                    time_cursor = increment_time(time_cursor, 1)
                    # print(f"[{i+1}/{delta}] cursor: {time_cursor}   point: {previous_point['dateTime']}     target: {dateOriginal}")
                    i += 1

                    if time_cursor == dateOriginal:
                        print(
                            f"Matching photo with trackpoint : {point['dateTime']} at lat:{point['latitude']} long: {point['longitude']} altitude:{point['elevation']}m")

        previous_point = point


def analyse_in_dir(path_photos_dir, path_gpx_file, utc_offset_seconds):

    parsed_gpx = read_gpx_dataframe(path_gpx_file, utc_offset_seconds)


    from pathlib import Path
    p = Path(path_photos_dir)

    for img in p.glob("*.jpg"):
        analyse(img, parsed_gpx)


analyse_single_photo("../data/sample/sampledata-1.jpg", "../data/sample/sampledata-1.gpx", 7200)
#analyse_in_dir("../data/sample", "../data/sample/sampledata-1.gpx", 7200)
