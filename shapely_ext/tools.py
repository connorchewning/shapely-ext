"""Helper tools to be used by accessor
"""
def convert_to_poly_list(shape):

    if shape.geom_type == 'MultiPolygon':
        shapes = list(shape.geoms)
    elif shape.geom_type == 'Polygon':
        shapes = [shape]
    else:
        raise Exception("Shape must be Polygon or MultiPolygon")

    return shapes

def convert_180_to_360(ring):

    _ring = copy.deepcopy(ring) # make sure we dont edit in place

    # shift all negative geometries to be 0-360 , then split at 180 degrees into two geometries then convert back
    coords = list(_ring.coords)
    for i, coord in enumerate(coords):
        x = coord[0]
        y = coord[1]
        if x < 0:
            x = 360+x
            coords[i] = (x, y)

    # update ring and return
    return shapely.LinearRing(coords)

def convert_360_to_180(ring):

    _ring = copy.deepcopy(ring) # make sure we dont edit in place

    # shift all negative geometries to be 0-360 , then split at 180 degrees into two geometries then convert back
    coords = list(_ring.coords)
    for i, coord in enumerate(coords):
        x = coord[0]
        y = coord[1]
        # if x == 180:
        #     x = 179.999
        if x > 180:
            x = x-360
            coords[i] = (x, y)

    # update ring and return
    return shapely.LinearRing(coords)

def realign_antimeridian_points(ring, sign):

    _ring = copy.deepcopy(ring) # make sure we dont edit in place

    # shift all negative geometries to be 0-360 , then split at 180 degrees into two geometries then convert back
    coords = list(_ring.coords)
    for i, coord in enumerate(coords):
        x = coord[0]
        y = coord[1]
        if x == 180:
            x = x * sign
            coords[i] = (x, y)

    # update ring and return
    return shapely.LinearRing(coords)


def shift_polygon(poly):

    _poly = copy.deepcopy(poly)

    exterior = convert_180_to_360(_poly.exterior)

    interiors = list()
    for interior in _poly.interiors:
        interiors.append(convert_180_to_360(interior))

    return shapely.Polygon(shell=exterior, holes=interiors)


def unshift_polygon(poly):

    _poly = copy.deepcopy(poly)

    exterior = convert_360_to_180(_poly.exterior)

    interiors = list()
    for interior in _poly.interiors:
        interiors.append(convert_360_to_180(interior))

    return shapely.Polygon(shell=exterior, holes=interiors)

def post_process_polygon(poly):

    _poly = copy.deepcopy(poly)

    # determine sign
    x, y =  zip(*_poly.exterior.coords)
    if np.sign(max(x)) == np.sign(min(x)):
            sign = 1
    else:
        sign = -1

    # realign points
    exterior = realign_antimeridian_points(_poly.exterior, sign)

    interiors = list()
    for interior in _poly.interiors:
        interiors.append(realign_antimeridian_points(interior, sign))

    return shapely.Polygon(shell=exterior, holes=interiors)    

# def shift_multipolygon(multipoly):

#     _multipoly = copy.deepcopy(multipoly)

#     polys = list()
#     for poly in tools.convert_to_poly_list(_multipoly):
#         polys.append(shift_polygon(poly))

#     return shapely.MultiPolygon(polys)

def unshift_multipolygon(multipoly):

    _multipoly = copy.deepcopy(multipoly)

    polys = list()
    for poly in tools.convert_to_poly_list(_multipoly):
        polys.append(unshift_polygon(poly))

    return shapely.MultiPolygon(polys)

def post_process_multipolygon(multipoly):

    _multipoly = copy.deepcopy(multipoly)

    polys = list()
    for poly in tools.convert_to_poly_list(_multipoly):
        polys.append(post_process_polygon(poly))

    return shapely.MultiPolygon(polys)
