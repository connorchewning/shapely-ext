import shapely
from shapely.geometry import Polygon, MultiPolygon

import tools

class ShapelyExtension:
    """Extension methods for Shapely geometries."""

    def __init__(self, geom):
        if not isinstance(geom, (Polygon, MultiPolygon)):
            raise TypeError("ShapelyExtension only works with Polygon or MultiPolygon.")
        self._geom = geom

    @property
    def crosses_antimeridian(self):
        """Check if the polygon crosses the antimeridian (-180° to 180°)."""
        return any(x < -180 or x > 180 for x, _ in self._geom.exterior.coords)

    @property
    def intersects_antimeridian(geom):
        """Assume that if the polygon spans more than 350 degress it likely is off"""
        intersects = False
        for poly in tools.convert_to_poly_list(geom):
            if (max(poly.exterior.coords)[0] - min(poly.exterior.coords)[0]) > 180:
                intersects = True

        return intersects



    # Split the geometry at 180 degrees
    def split_at_antimeridian(self):
        """Split the polygon into multiple parts if it crosses the antimeridian."""

        # check if we need to split
        if not self.crosses_antimeridian:
            return self._geom  # No split needed

        # Otherwise run the splitting routine
        new_polys = list()
        for poly in tools.convert_to_poly_list(self._geom):

            poly = tools.shift_polygon(poly)
            antimeridian = shapely.LineString([(180, 91), (180, -91)])
            multipoly = MultiPolygon(shapely.ops.split(geom, antimeridian))
            multipoly = tools.unshift_multipolygon(multipoly)
            multipoly = tools.post_process_multipolygon(multipoly)
            
            for new_poly in tools.convert_to_poly_list(multipoly):
                new_polys.append(new_poly)

        if len(new_polys) > 1:
            return MultiPolygon(new_polys)

        else:
            return new_polys[0]

         


def _shapely_ext_accessor(self):
    """Returns the extension object for additional methods."""
    return ShapelyExtension(self)


# Attach the extension property to Shapely geometries
Polygon.ext = property(_shapely_ext_accessor)
MultiPolygon.ext = property(_shapely_ext_accessor)