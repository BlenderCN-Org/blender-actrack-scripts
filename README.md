# blender-actrack-scripts

This is a collection of Blender addons I've found useful for track modding.
The original authors are still credited in the individual Python/C files; I've
made such modifications as I needed for my purposes:
 - added a family of import tools based on the original SRTM importer
 - Modified drop_to_ground to be able to better calculate a bottom center
   point.
 - Added object_displace, based on drop_to_ground, for displacing one mesh
   by another

In addition, there are some shell scripts that show how elevation data can be
downloaded and converted into a .grid file, which can then be imported into
Blender using the io_import_scene_array.py addon.

The makegroove.c file is for making a small texture with two different
strengths of a groove overlay, with a smooth transition in the middle. It
produces a PAM file with an alpha channel.

The pam2png converter has the following copyright notice:
/*
 *  pam2png.c --- conversion from PBM/PGM/PPM-file to PNG-file
 *  copyright (C) 2011 by Willem van Schaik <willem@schaik.com>
 *
 *  version 1.0 - First version.
 *
 *  Permission to use, copy, modify, and distribute this software and
 *  its documentation for any purpose and without fee is hereby granted,
 *  provided that the above copyright notice appear in all copies and
 *  that both that copyright notice and this permission notice appear in
 *  supporting documentation. This software is provided "as is" without
 *  express or implied warranty.
 */
