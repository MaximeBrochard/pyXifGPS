import datetime
import fractions

import gpxpy
import pandas as pd
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
from GPSPhoto import gpsphoto
import exifread


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

def to_deg(value, loc):
    """convert decimal coordinates into degrees, munutes and seconds tuple
    Keyword arguments: value is float gps-value, loc is direction list ["S", "N"] or ["W", "E"]
    return: tuple like (25, 13, 48.343 ,'N')
    """
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg =  int(abs_value)
    t1 = (abs_value-deg)*60
    min = int(t1)
    sec = round((t1 - min)* 60, 5)
    return (deg, min, sec, loc_value)


def change_to_rational(number):
    """convert a number to rantional
    Keyword arguments: number
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = fractions.Fraction(str(number))
    return (f.numerator, f.denominator)


def add_gps_infos(file_name, lat, lng, altitude):
    """Adds GPS position as EXIF metadata
    Keyword arguments:
    file_name -- image file
    lat -- latitude (as float)
    lng -- longitude (as float)
    altitude -- altitude (as float)
    """
    lat_deg = to_deg(lat, ["S", "N"])
    lng_deg = to_deg(lng, ["W", "E"])

    exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
    exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))

    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
        piexif.GPSIFD.GPSAltitudeRef: 1,
        piexif.GPSIFD.GPSAltitude: change_to_rational(round(altitude)),
        piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
        piexif.GPSIFD.GPSLatitude: exiv_lat,
        piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
        piexif.GPSIFD.GPSLongitude: exiv_lng,
    }

    gps_exif = {"GPS": gps_ifd}

    # get original exif data first!
    exif_data = piexif.load(file_name)

    # update original exif data to include GPS tag
    exif_data.update(gps_exif)
    exif_bytes = piexif.dump(exif_data)

    piexif.insert(exif_bytes, file_name)

def analyse_single_photo(path_single_photo, path_gpx_file, utc_offset_seconds):
    from pathlib import Path
    img = Path(path_single_photo)
    parsed_gpx = read_gpx_dataframe(path_gpx_file, utc_offset_seconds)
    analyse(img, parsed_gpx)


def analyse(img, parsed_gpx):
    my_path = img.as_posix()

    exif = get_exif(img)
    dateOriginal = get_Tag(exif, 'DateTimeOriginal')
    #print(f"Analysing '{img.name}', taken at {dateOriginal}")

    if dateOriginal < parsed_gpx.iloc[0]['dateTime']:
        print(
            f"[{img.name}]  Picture taken before gpx track starts. lat: {parsed_gpx.iloc[0]['latitude']}, long: {parsed_gpx.iloc[0]['longitude']}, altitude: {parsed_gpx.iloc[-1]['elevation']}")
        add_gps_infos(my_path, parsed_gpx.iloc[0]['latitude'], parsed_gpx.iloc[0]['longitude'], int(parsed_gpx.iloc[0]['elevation']))

    if dateOriginal > parsed_gpx.iloc[-1]['dateTime']:
        print(
            f"[{img.name}]  Picture taken after gpx track ended. lat: {parsed_gpx.iloc[-1]['latitude']}, long: {parsed_gpx.iloc[-1]['longitude']}, altitude: {parsed_gpx.iloc[-1]['elevation']}")
        add_gps_infos(my_path, parsed_gpx.iloc[-1]['latitude'], parsed_gpx.iloc[-1]['longitude'], int(parsed_gpx.iloc[-1]['elevation']))


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
                            f"[{img.name}]  Matching trackpoint at {point['dateTime']} : lat:{point['latitude']} long: {point['longitude']} altitude:{point['elevation']}m")
                        add_gps_infos(my_path, point['latitude'], point['longitude'], int(point['elevation']))
        previous_point = point


def analyse_in_dir(path_photos_dir, path_gpx_file, utc_offset_seconds):

    parsed_gpx = read_gpx_dataframe(path_gpx_file, utc_offset_seconds)


    from pathlib import Path
    p = Path(path_photos_dir)

    for img in p.glob("*.jpg"):
        analyse(img, parsed_gpx)


#analyse_single_photo("../data/sample-2-lite/sampledata-3.jpg", "../data/sample-2-lite/sampledata-2.gpx", 7200)
analyse_in_dir("../data/sample-2-lite", "../data/sample-2-lite/sampledata-2.gpx", 7200)
