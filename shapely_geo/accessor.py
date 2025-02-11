import shapely
from shapely.geometry import Polygon, MultiPolygon
from shapely_geo import geo_tools
import numpy as np

from pyproj import CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from pyproj import Transformer

class ShapelyExtension:
    """Extension methods for Shapely geometries."""

    def __init__(self, geom):
        if not isinstance(geom, (Polygon, MultiPolygon)):
            raise TypeError("ShapelyExtension only works with Polygon or MultiPolygon.")
        self._geom = geom
        self._type = geom.geom_type

    @property
    def intersects_antimeridian(self):
        """Assume that if the polygon spans more than 350 degress it likely is off"""
        intersects = False
        for poly in geo_tools.convert_to_poly_list(self._geom):
            if (max(poly.exterior.coords)[0] - min(poly.exterior.coords)[0]) > 180:
                intersects = True

        return intersects


    # Split the geometry at 180 degrees
    def split_at_antimeridian(self):
        """Split the polygon into multiple parts if it crosses the antimeridian."""

        # check if we need to split
        if not self.intersects_antimeridian:
            return self._geom  # No split needed

        # Otherwise run the splitting routine
        new_polys = list()
        for poly in geo_tools.convert_to_poly_list(self._geom):

            poly = geo_tools.shift_polygon(poly)
            antimeridian = shapely.LineString([(180, 91), (180, -91)])
            multipoly = MultiPolygon(shapely.ops.split(poly, antimeridian))
            multipoly = geo_tools.unshift_multipolygon(multipoly)
            multipoly = geo_tools.post_process_multipolygon(multipoly)
            
            for new_poly in geo_tools.convert_to_poly_list(multipoly):
                new_polys.append(new_poly)

        if len(new_polys) > 1:
            return MultiPolygon(new_polys)

        else:
            return new_polys[0]


    # Inspired / follow geopandas syntax and implementation for estiamting the local crs
    def estimate_utm_crs(self, crs='EPSG:4326', datum_name="WGS 84"):

        minx, miny, maxx, maxy = shapely.bounds(self._geom)
        crs_input = CRS.from_user_input(crs)
        if crs_input.is_geographic:
            x_center = np.mean([minx, maxx])
            y_center = np.mean([miny, maxy])
        # ensure using geographic coordinates
        else:
            # transformer = TransformerFromCRS(crs_input, "EPSG:4326", always_xy=True)
            transformer = Transformer.from_crs(crs_input, "EPSG:4326", always_xy=True)
            minx, miny, maxx, maxy = transformer.transform_bounds(
                minx, miny, maxx, maxy
            )
            y_center = np.mean([miny, maxy])
            # crossed the antimeridian          # TODO: perhaps a good implementation here for checking the antimeridian
            if minx > maxx:
                # shift maxx from [-180,180] to [0,360]
                # so both numbers are positive for center calculation
                # Example: -175 to 185
                maxx += 360
                x_center = np.mean([minx, maxx])
                # shift back to [-180,180]
                x_center = ((x_center + 180) % 360) - 180
            else:
                x_center = np.mean([minx, maxx])

        utm_crs_list = query_utm_crs_info(
            datum_name=datum_name,
            area_of_interest=AreaOfInterest(
                west_lon_degree=x_center,
                south_lat_degree=y_center,
                east_lon_degree=x_center,
                north_lat_degree=y_center,
            ),
        )
        try:
            return CRS.from_epsg(utm_crs_list[0].code)
        except IndexError:
            raise RuntimeError("Unable to determine UTM CRS")



    def to_crs(self, src_crs=None, src_epsg=None, crs=None, epsg=None):

        # Check the crs for the source geometry is provided
        if src_crs is not None:
            src_crs = CRS.from_user_input(src_crs)
        elif src_epsg is not None:
            src_crs = CRS.from_epsg(src_epsg)
        else:
            raise ValueError(
                "Cannot transform naive geometries. "
                "Please provide a crs for the object first."
            )

        # check the dst crs is provided
        if crs is not None:
            crs = CRS.from_user_input(crs)
        elif epsg is not None:
            crs = CRS.from_epsg(epsg)
        else:
            raise ValueError("Must pass either crs or epsg for transformation.")

        # skip if the input CRS and output CRS are the exact same
        if src_crs.is_exact_same(crs):
            return self._geom

        transformer = Transformer.from_crs(src_crs, crs, always_xy=True)
        # transformer = TransformerFromCRS(crs_input, crs, always_xy=True)

        new_shape = shapely.ops.transform(transformer.transform, self._geom)
        return new_shape
         


def _shapely_geo_accessor(self):
    """Returns the extension object for additional methods."""
    return ShapelyExtension(self)


# Attach the extension property to Shapely geometries
Polygon.geo = property(_shapely_geo_accessor)
MultiPolygon.geo = property(_shapely_geo_accessor)