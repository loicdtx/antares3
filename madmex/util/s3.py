import os
import re
from rasterio.io import MemoryFile
import numpy as np
try:
    import boto3
except ImportError:
    _has_boto3 = False
else:
    _has_boto3 = True


def list_folders(bucket, path, pattern=None):
    """List 'sub-folders' of a s3 bucket 'folder'

    Args:
        bucket (str): Name of an existing s3 bucket
        path (str): Path of the folder containing the sub-folders to be listed
        pattern (str): Optional regex like pattern to filter the returned directories

    Examples:
        >>> from madmex.util import s3
        >>> # List all Landsat 8 scenes of conabio-s3-oregon bucket
        >>> s3.list_folders('conabio-s3-oregon', 'linea_base/L8/')
        >>> # Filter 039/037 path/row
        >>> s3.list_folders('conabio-s3-oregon', 'linea_base/L8/', pattern=r'.*LC08039037.*')

    Returns:
        list: List of subfolder names
    """
    if not _has_boto3:
        raise ImportError('boto3 is required for working with s3 buckets')
    # Add trailing slash to path if not already there and remove leading slash
    path = os.path.join(path.strip('/'), '')
    # Connect to bucket
    client = boto3.client('s3')
    paginator = client.get_paginator('list_objects')
    params = {'Bucket': bucket, 'Prefix': path, 'Delimiter': '/'}
    page_iterator = paginator.paginate(**params)
    out_list = []
    for page in page_iterator:
        common_prefixes = page.get('CommonPrefixes')
        if common_prefixes is not None:
            out_list += [x.get('Prefix') for x in common_prefixes]
    if pattern is not None:
        pattern = re.compile(pattern)
        out_list = [x for x in out_list if pattern.search(x)]
    return out_list


def list_files(bucket, path, pattern=None):
    """List objects within a 'path' in an s3 bucket

    Note that objects are listed recursively

    Args:
        bucket (str): Name of an existing s3 bucket
        path (str): Path of the folder containing the objects to be listed
        pattern (str): Optional regex like pattern to filter the returned objects

    Examples:
        >>> from madmex.util import s3
        >>> # List all files of a Landsat directory
        >>> s3.list_files(bucket='conabio-s3-oregon', path='linea_base/L8/LC080190482017022301T1-SC20180611232224')
        >>> # Filter metadata file
        >>> s3.list_files(bucket='conabio-s3-oregon', path='linea_base/L8/LC080190482017022301T1-SC20180611232224',
        ...               pattern=r'.*.xml$')

    Return:
        list: List of s3 keys (objects)
    """
    if not _has_boto3:
        raise ImportError('boto3 is required for working with s3 buckets')
    # Strip leading and trailing slash
    path = path.strip('/')
    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(bucket)
    obj_list = my_bucket.objects.filter(Prefix=path)
    out = [x.key for x in obj_list]
    if pattern is not None:
        pattern = re.compile(pattern)
        out = [x for x in out if pattern.search(x)]
    return out


def build_rasterio_path(bucket, path):
    """Build rasterio compliant s3 path to object

    Args:
        bucket (str): Name of bucket containing the data
        path (str): Path to append to bucket name (often to a geospatial raster
            object, but not always)

    Return:
        str: Rasterio compliant s3 object path
    """
    path = path.strip('/')
    return os.path.join('s3://', bucket, path)


def read_file(bucket, path):
    """Read a text file as string

    Args:
        bucket (str): Name of an existing s3 bucket
        path (str): Path to the text object

    Return:
        str: The content of the object read as a string
    """
    if not _has_boto3:
        raise ImportError('boto3 is required for working with s3 buckets')
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket, path)
    return obj.get()["Body"].read()


def write_raster(bucket, path, arr, **kwargs):
    """Write a numpy array as a geospatial raster to a s3 bucket

    This function uses rasterio to write the array to an in-memory file object
    that is later copied to the desired s3 location

    Args:
        bucket (str): Name of an existing s3 bucket
        path (str): Full path of the object to create with the s3 bucket
        arr (np.ndarray): The numpy array to write to a raster file. Can be 2D
            or 3D. If 3D (multiband raster), bands must correspond to the first
            array dimension
        **kwargs: Additional arguments to pass to ``rasterio.open``, typically
            the raster dataset meta characteristics (``crs``, ``height``, ...)

    Example:
        >>> from madmex.util import s3
        >>> import numpy as np
        >>> arr = np.arange(100).reshape((10, 10)).astype(np.uint8)
        >>> meta = {'height': 10, 'width': 10, 'dtype': np.uint8, 'count': 1,
        ...         'driver': 'GTiff', 'crs': '+proj=longlat'}
        >>> s3.write_raster('conabio-s3-oregon', 'rasterio/test_raster.tif',
        ...                 arr, **meta)
        >>> print(s3.list_files('conabio-s3-oregon', 'rasterio'))
    """
    if not _has_boto3:
        raise ImportError('boto3 is required for working with s3 buckets')
    s3 = boto3.client('s3')
    path = path.strip('/')
    if arr.ndim == 2:
        arr = np.expand_dims(arr, 0)
    with MemoryFile() as memfile:
        with memfile.open(**kwargs) as dst:
            for band_id, band in enumerate(arr, start=1):
                dst.write(band, band_id)
        s3.upload_fileobj(memfile, bucket, path)

