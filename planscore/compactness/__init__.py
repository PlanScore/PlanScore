import math, itertools
from osgeo import ogr, osr
from . import smallestenclosingcircle

# Spherical mercator should work at typical district sizes
EPSG4326 = osr.SpatialReference(); EPSG4326.ImportFromEPSG(4326)
EPSG3857 = osr.SpatialReference(); EPSG3857.ImportFromEPSG(3857)
projection = osr.CoordinateTransformation(EPSG4326, EPSG3857)

def get_scores(geometry):
    ''' Return dictionary of compactness scores for a geographic area.
    '''
    scores = dict()
    
    try:
        scores['Reock'] = get_reock_score(geometry)
    except Exception:
        scores['Reock'] = None
    
    return scores

def get_reock_score(geometry):
    ''' Return area ratio of geometry to minimum bounding circle
        
        More on Reock score:
        https://github.com/cicero-data/compactness-stats/wiki#reock
    '''
    projected = geometry.Clone()
    projected.Transform(projection)
    boundary = projected.GetBoundary()
    geom_area = projected.GetArea()
    
    if boundary.GetGeometryType() in (ogr.wkbMultiLineString, ogr.wkbMultiLineString25D):
        geoms = [boundary.GetGeometryRef(i) for i in range(boundary.GetGeometryCount())]
        points = itertools.chain(*[[geom.GetPoint(i)[:2]
            for i in range(1, geom.GetPointCount())] for geom in geoms])
    else:
        points = [boundary.GetPoint(i)[:2] for i in range(1, boundary.GetPointCount())]

    _, _, radius = smallestenclosingcircle.make_circle(points)
    return geom_area / (math.pi * radius * radius)
