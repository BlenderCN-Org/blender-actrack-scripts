# This is the release version of the plugin file io_import_scene_srtm_dev.py
# If you would like to make edits, make them in the file io_import_scene_srtm_dev.py and the other related modules
# To create the release version of io_import_scene_srtm_dev.py, executed:
# python plugin_builder.py io_import_scene_srtm_dev.py:
bl_info = {
        "name": "Import grid (.grid)",
        "author": "Vladimir Elistratov <vladimir.elistratov@gmail.com>",
        "version": (1, 0, 0),
        "blender": (2, 6, 9),
        "location": "File > Import > SRTM (.hgt)",
        "description" : "Import digital elevation model data from files in grid format (.grid)",
        "warning": "",
        "wiki_url": "https://github.com/vvoovv/blender-geo/wiki/Import-SRTM-(.hgt)",
        "tracker_url": "https://github.com/vvoovv/blender-geo/issues",
        "support": "COMMUNITY",
        "category": "Import-Export",
}

import bpy, mathutils
# ImportHelper is a helper class, defines filename and invoke() function which calls the file selector
from bpy_extras.io_utils import ImportHelper

import struct, math, os

import sys
import math

# see conversion formulas at
# http://en.wikipedia.org/wiki/Transverse_Mercator_projection
# and
# http://mathworld.wolfram.com/MercatorProjection.html
class TransverseMercator:
        radius = 6378137

        def __init__(self, **kwargs):
                # setting default values
                self.lat = 0 # in degrees
                self.lon = 0 # in degrees
                self.k = 1 # scale factor
                
                for attr in kwargs:
                        setattr(self, attr, kwargs[attr])
                self.latInRadians = math.radians(self.lat)

        def fromGeographic(self, lat, lon):
                lat = math.radians(lat)
                lon = math.radians(lon-self.lon)
                B = math.sin(lon) * math.cos(lat)
                x = 0.5 * self.k * self.radius * math.log((1+B)/(1-B))
                y = self.k * self.radius * ( math.atan(math.tan(lat)/math.cos(lon)) - self.latInRadians )
                return (x,y)

        def toGeographic(self, x, y):
                x = x/(self.k * self.radius)
                y = y/(self.k * self.radius)
                D = y + self.latInRadians
                lon = math.atan(math.sinh(x)/math.cos(D))
                lat = math.asin(math.sin(D)/math.cosh(x))

                lon = self.lon + math.degrees(lon)
                lat = math.degrees(lat)
                return (lat, lon)

def getPtArrayIntervals(x1, x2):
        """
        Split (x1, x2) into SRTM intervals. Examples:
        (31.2, 32.7) => [ (31.2, 32), (32, 32.7) ]
        (31.2, 32) => [ (31.2, 32) ]
        """
        _x1 = x1
        intervals = []
        while True:
                _x2 = math.floor(_x1 + 1)
                if (_x2>=x2):
                        intervals.append((_x1, x2))
                        break
                else:
                        intervals.append((_x1, _x2))
                        _x1 = _x2
        return intervals

def getSelectionBoundingBox(context):
        # perform context.scene.update(), otherwise o.matrix_world or o.bound_box are incorrect
        context.scene.update()
        if len(context.selected_objects)==0:
                return None
        xmin = float("inf")
        ymin = float("inf")
        xmax = float("-inf")
        ymax = float("-inf")
        for o in context.selected_objects:
                for v in o.bound_box:
                        (x,y,z) = o.matrix_world * mathutils.Vector(v)
                        if x<xmin: xmin = x
                        elif x>xmax: xmax = x
                        if y<ymin: ymin = y
                        elif y>ymax: ymax = y
        return {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}


class ImportPtArray(bpy.types.Operator, ImportHelper):
        """Import digital elevation model data from files in grid format (.grid)"""
        bl_idname = "import_scene.grid"  # important since its how bpy.ops.import_scene.srtm is constructed
        bl_label = "Import grid"
        bl_options = {"UNDO","PRESET"}

        # ImportHelper mixin class uses this
        filename_ext = ".grid"

        filter_glob = bpy.props.StringProperty(
                default="*.grid",
                options={"HIDDEN"},
        )

        ignoreGeoreferencing = bpy.props.BoolProperty(
                name="Ignore existing georeferencing",
                description="Ignore existing georeferencing and make a new one",
                default=False,
        )
        
        primitiveType = bpy.props.EnumProperty(
                name="Mesh primitive type: quad or triangle",
                items=(("quad","quad","quad"),("triangle","triangle","triangle")),
                description="Primitive type used for the terrain mesh: quad or triangle",
                default="quad",
        )
        
        useSpecificExtent = bpy.props.BoolProperty(
                name="Use manually set extent",
                description="Use specific extent by setting min lat, max lat, min lon, max lon",
                default=False,
        )
        
        minLat = bpy.props.FloatProperty(
                name="min lat",
                description="Minimum latitude of the imported extent",
                default=0,
        )

        maxLat = bpy.props.FloatProperty(
                name="max lat",
                description="Maximum latitude of the imported extent",
                default=0,
        )

        minLon = bpy.props.FloatProperty(
                name="min lon",
                description="Minimum longitude of the imported extent",
                default=0,
        )

        maxLon = bpy.props.FloatProperty(
                name="max lon",
                description="Maximum longitude of the imported extent",
                default=0,
        )

        def execute(self, context):
                scene = context.scene
                projection = None
                if "latitude" in scene and "longitude" in scene:
                        projection = TransverseMercator(lat=scene["latitude"], lon=scene["longitude"])

                # remember if we have georeferencing
                _projection = projection
                with open (self.filepath) as f:
                        line = f.readline ()
                        (snx, sny, sincx, sincy, sminlon, sminlat) = line.split(" ");
                        nx = int (snx);
                        ny = int (sny);
                        incx = float (sincx);
                        incy = float (sincy);
                        minlon = float (sminlon);
                        minlat = float (sminlat);
                        maxlon = minlon + incx * nx;
                        maxlat = minlat + incy * ny;
                        if not projection:
                                projection = TransverseMercator(lat=(minlat+maxlat)/2, lon=(minlon+maxlon)/2)
                        srtm = PtArray(
                                nx=nx, ny=ny,
                                projection=projection,
                                f=f,
                                primitiveType = self.primitiveType)
                        verts = []
                        indices = []
                        srtm.build(verts, indices)

                        # create a mesh object in Blender
                        mesh = bpy.data.meshes.new("PtArry")
                        mesh.from_pydata(verts, [], indices)
                        mesh.update()
                        obj = bpy.data.objects.new("PtArray", mesh)
                        bpy.context.scene.objects.link(obj)
                # set custom parameter "latitude" and "longitude" to the active scene
                if not _projection:
                        scene["latitude"] = projection.lat
                        scene["longitude"] = projection.lon
                
                return {"FINISHED"}

        def draw(self, context):
                layout = self.layout

                layout.label("Mesh primitive type:")
                row = layout.row()
                row.prop(self, "primitiveType", expand=True)
        
                

class PtArray:

        # SRTM3 data are sampled at three arc-seconds and contain 1201 lines and 1201 samples
        size = 3600

        voidValue = -32768

        def __init__(self, **kwargs):
                self.srtmDir = "."
                self.voidSubstitution = 0
                
                for key in kwargs:
                        setattr(self, key, kwargs[key])
                
        def build(self, verts, indices):
                """
                The method fills verts and indices lists with values
                verts is a list of vertices
                indices is a list of tuples; each tuple is composed of 3 indices of verts that define a triangle
                """
                
                minHeight = 32767
                maxHeight = -32767
                maxLon = 0
                maxLat = 0
                
                vertsCounter = 0
                
                for y in range(0, self.ny):
                        for x in range(0, self.nx):
                                line = self.f.readline ()
                                (slat, slon, alt) = line.split (" ")
                                lat = float (slat)
                                lon = float (slon)
                                z = float (alt)
                                xy = self.projection.fromGeographic(lat, lon)
                                # print ("%d: %f %f height %f" % (vertsCounter, xy[0], xy[1], z))
                                # add a new vertex to the verts array
                                verts.append((xy[0], xy[1], z))
                                if x>0 and y>0:
                                        topNeighborIndex = vertsCounter-self.nx
                                        leftTopNeighborIndex = vertsCounter-self.nx-1
                                        if self.primitiveType == "quad":
                                                # print ("%d %d %d %d" % (vertsCounter, topNeighborIndex, leftTopNeighborIndex, vertsCounter-1))
                                                indices.append((vertsCounter, topNeighborIndex, leftTopNeighborIndex, vertsCounter-1))
                                        else: # self.primitiveType == "triangle"
                                                indices.append((vertsCounter-1, topNeighborIndex, leftTopNeighborIndex))
                                                indices.append((vertsCounter, topNeighborIndex, vertsCounter-1))
                                vertsCounter += 1


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
        self.layout.operator(ImportPtArray.bl_idname, text="Grid (.grid)")

def register():
        bpy.utils.register_class(ImportPtArray)
        bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
        bpy.utils.unregister_class(ImportPtArray)
        bpy.types.INFO_MT_file_import.remove(menu_func_import)
