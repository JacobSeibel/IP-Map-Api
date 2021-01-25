# IP Mapping API

An API that returns the count of IPs at a subset of coordinates on the globe.

## Endpoints

### `GET` /ipCounts
#### Parameters
* bounds: [Optional] Provide a list of four coordinates representing the NW, NE, SE, SW bounds (in any order) of a bounding box. The coordinates must be formatted like so: `[[aLat, aLng], [bLat, bLng], [cLat, cLng], [dLat, dLng]]` This endpoint assumes rectangular dimensions, and will provide unexpected results if the coordinates do not represent a rectangle.

#### Returns
* A JSON object containing a "results" attribute which contains a list of JSON objects containing "longitude", "latitude", and "count" attributes. The list of objects in "results" represent either all coordinates in the world (if 'bounds' was not provided) or all the coordinates inside the bounding box specified by the 'bounds' parameter.
