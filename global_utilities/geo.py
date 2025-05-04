from geopy.geocoders import Nominatim

def get_map_coors(address):
    if type(address) != "".__class__:
        raise TypeError("you have to give a string ")
    locator = Nominatim(user_agent="myGeocoder")
    print(address)
    location = locator.geocode(address)

    return location.latitude, location.longitude

def get_address_from_point(point):

    locator = Nominatim(user_agent="myGeocoder")
    coors = f'{p.x}, {p.y}'
    location = locator.reverse(coors)
    return location.address
