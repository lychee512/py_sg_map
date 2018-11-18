from fastkml import kml
import pandas as pd
import numpy as np
import shapely.geometry
import re

from matplotlib.collections import LineCollection


class GeoDataSg():
    """Object which holds a DataFrame with each row obtained from a placemark feature in the a KML file.
        Each GeoDataSg.df has a column named 'POLYGON' which is a shapely geometry object."""

    df = pd.DataFrame()
    LONGITUDE_ORIGIN = (103 + 50 / 60) / 180 * np.pi
    LATITUDE_ORIGIN = (1 + 22 / 60) / 180 * np.pi
    ASPECT_RATIO = 1 / np.cos(LATITUDE_ORIGIN)
    LONGITUDE_LIMITS = [103.6, 104.1]
    LATITUDE_LIMITS = [1.18, 1.48]

    def __init__(self, path_to_file):
        """Initialize and populate self.df with data from *.kml file at string path_to_file"""
        with open(path_to_file, 'rt', encoding="utf-8") as kmlfile:
            doc = kmlfile.read()
        k = kml.KML()
        pattern = re.compile(r'xsd:')
        doc2 = re.sub(pattern, '', doc)
        k.from_string(doc2.encode('utf-8'))

        document = list(k.features())[0]
        folder = list(document.features())[0]
        placemarks = list(folder.features())

        # warning: placemarks.geometry can be of type shapely.geometry.polygon.Polygon
        #  or MultiPolygon or others!

        df = pd.DataFrame()
        for i, placemark in enumerate(placemarks):
            try:
                data = placemark.extended_data.elements[0].data
                # build a dict from the name/value pairs in data
                # note that we encapsulated the values as a 1-element list
                data_dict = dict([(_dict['name'], [_dict['value']]) for _dict in data])

                # remove these fields from the dict
                data_dict.pop('FMEL_UPD_D', None)
                data_dict.pop('INC_CRC', None)

            except AttributeError:  # catch when extended_data is none
                data_dict = dict()

            # add a polygon field to the dict
            data_dict['POLYGON'] = [placemark.geometry]

            # build a dataframe and append it
            _df = pd.DataFrame(data_dict, index=[i])
            df = df.append(_df)
        # df.set_index('SUBZONE_N',verify_integrity=True,inplace =True)
        self.df = df.apply(pd.to_numeric, errors='ignore')

    def add_lines_to_plot(self, ax, *args, **kwargs):
        """add a line collection defined from geometry objects in self.df
        to a matplotlib.axes instance ax"""
        ax.set_xlim(GeoDataSg.LONGITUDE_LIMITS)
        ax.set_ylim(GeoDataSg.LATITUDE_LIMITS)
        ax.set_aspect(GeoDataSg.ASPECT_RATIO)
        # This is the more accurate and correct way, if we want to use cartopy
        # ax = plt.axes(projection = cartopy.crs.PlateCarree())
        # ax.set_extent([103.6, 104.1, 1.18, 1.48],crs = cartopy.crs.PlateCarree())
        line_list = []
        for i, polygon in enumerate(self.df['POLYGON']):
            if isinstance(polygon, shapely.geometry.polygon.Polygon):
                line_list.append(np.asarray(polygon.exterior.xy).transpose())
            elif isinstance(polygon, shapely.geometry.LineString):
                line_list.append(np.asarray(polygon.coords.xy).transpose())
            elif isinstance(polygon, shapely.geometry.multilinestring.MultiLineString):
                for sub_line in polygon.geoms:
                    line_list.append(np.asarray(sub_line.xy).transpose())
            else:
                # this should be a multipolygon
                # print(df.iloc[i]['SUBZONE_N']+', part of '+df.iloc[i]['PLN_AREA_N'])
                for sub_polygon in polygon.geoms:
                    line_list.append(np.asarray(sub_polygon.exterior.xy).transpose())
        ax.add_collection(LineCollection(line_list, *args, **kwargs))


if __name__ == '__main__':
    print('imports done')
