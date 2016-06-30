# blender-actrack-scripts
This is a collection of Blender addons I've found useful for track modding.
The original authors are still credited in the individual Python files; I've
made such modifications as I needed for my purposes:
 - added a family of import tools based on the original SRTM importer
 - Modified drop_to_ground to be able to better calculate a bottom center
   point.

In addition, there are some shell scripts that show how elevation data can be
downloaded and converted into a .grid file, which can then be imported into
Blender using the io_import_scene_array.py addon.
