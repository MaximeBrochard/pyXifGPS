# pyXifGPS
A command line tool to add GPS data from .gpx track to JPEG images.

## What is it?
pyXifGPS is basic Python tool that helps you insert GPS data into JPEG's [exif](https://en.wikipedia.org/wiki/Exif)(**Exchangeable image file format**). By scanning *DateTImeOriginal* data in **JPEG's** files,  and GPS *Trackpoints* in **gpx** file, **pyXifGPS** can find the emplacement of a given picture.      

## Main Features
What it does well:
* Process a single JPEG file or a whole directory with following flags : `--singlefile` `--directory`
* Handle offset between **.gpx** timezone (typcally GMT) and images, set offset with `--offset` flag
* Check if image is out of **.gpx** track bounds, auto-assign first or last point informations
* Check if the file already contains GPS infos, inform user distance between original and computed GPS coordinates

## Dependencies
[Piexif](https://github.com/hMatoba/Piexif), [Pillow](https://github.com/python-pillow/Pillow), [gpxpy](https://github.com/tkrajina/gpxpy), [pandas](https://github.com/pandas-dev/pandas/)

## Usage
It implies to have all the dependencies above previoulsy install on your environment 

After making `exif_gps.py` executable (basically with a `chmod +x src/exif_gps.py`), you are able to run :

```
python exif_gps.py path/to/gpx/file --directory path/to/images/directory --offset **int_value**
``` 

**Description**:
* paths are relative to `exif_gps.py`
* `path/to/gpx/file` path to the gpx file you want to make match with your image(s)
* `path/to/images/directory` path to the directory of images you want to make match with the **.gpx** track.
    * use `--directory` flag before directory path to batch a directory
    * use `--singlefile` flag before image path to process only one image
* `--offset` use this flag to adjust offset (in seconds) between **.gpx** track and image(s)

### Example
The following example describe how to run **pyXifGPS** in this example data provided with the repo at `example_data/sample1`. 
```
python exif_gps.py ../example_data/sample1/sample_gpx_gmt_plus2.gpx --directory ../example_data/sample1 --offset 7200
```

`--offset 7200` is used in this example because **sample_gpx_gmt_plus2.gpx** stores a UTC timeformat and is recorded in a **GMT+2** timezone, while images time informations are in-built timezoned by the user/manufacturer.
  