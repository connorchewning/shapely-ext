"""My Library has useful functionality"""

from .accessor import ShapelyExtension, _shapely_geo_accessor

# Patch the shapely objects
from shapely.geometry import Polygon, MultiPolygon
Polygon.geo = property(_shapely_geo_accessor)
MultiPolygon.geo = property(_shapely_geo_accessor)