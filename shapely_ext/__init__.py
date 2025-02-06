"""My Library has useful functionality"""

from .accessor import ShapelyExtension, _shapely_ext_accessor

# Patch the shapely objects
from shapely.geometry import Polygon, MultiPolygon
Polygon.ext = property(_shapely_ext_accessor)
MultiPolygon.ext = property(_shapely_ext_accessor)