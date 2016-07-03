# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
bl_info = {
    'name': 'Displace mesh',
    'author': 'Unnikrishnan(kodemax), Florian Meyer(testscreenings)',
    'version': (1,2),
    "blender": (2, 63, 0),
    'location': '3D View -> Tool Shelf -> Object Tools Panel (at the bottom)',
    'description': 'Drop selected objects on active object',
    'warning': '',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Object/Drop_to_ground',
    "tracker_url": "http://projects.blender.org/tracker/?func=detail&atid=25349",
    'category': 'Object'}
#################################################################
import bpy, bmesh
from mathutils import *
from bpy.types import Operator
from bpy.props import *
#################################################################

def transform_ground_to_world(sc, ground):
    tmpMesh = ground.to_mesh(sc, True, 'PREVIEW')
    tmpMesh.transform(ground.matrix_world)
    tmp_ground = bpy.data.objects.new('tmpGround', tmpMesh)
    sc.objects.link(tmp_ground)
    sc.update()
    return tmp_ground

def modify_mesh(ob, ground, down, mat_parent=None):
    bme = bmesh.new()
    bme.from_mesh(ob.data)
    mat_to_world = ob.matrix_world.copy()
    if mat_parent:
        mat_to_world = mat_parent * mat_to_world
    #bme.verts.index_update() #probably not needed
    lowest_co = 0
    count = 0
    for v in bme.verts:
        v_world_co = mat_to_world * v.co
        hit_loc, hit_normal, hit_index = ground.ray_cast (v_world_co, v_world_co + down)
        # cheating, assumes object coords == world coords
        disp = hit_loc.z
        # print (v.co.z, disp)
        v.co.z += disp
    bme.to_mesh (ob.data)
    bme.free()

def displace_objects(self, context):
    ground = context.object
    obs = context.selected_objects
    obs.remove(ground)
    tmp_ground = transform_ground_to_world(context.scene, ground)
    down = Vector((0, 0, -10000))

    for ob in obs:
        modify_mesh (ob, tmp_ground, down)

    #cleanup
    bpy.ops.object.select_all(action='DESELECT')
    tmp_ground.select = True
    bpy.ops.object.delete('EXEC_DEFAULT')
    for ob in obs:
        ob.select = True
    ground.select = True

#################################################################
class OBJECT_OT_displace_mesh(Operator):
    """Displace points in selected objects by z of active object"""
    bl_idname = "object.displace_by_active"
    bl_label = "Displace mesh"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Displace points in selected objects by z of active object"

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) >= 2

    ##### EXECUTE #####
    def execute(self, context):
        print('\nDropping Objects')
        displace_objects(self, context)
        return {'FINISHED'}

#################################################################
def displace_mesh_button(self, context):
    self.layout.operator(OBJECT_OT_displace_mesh.bl_idname,
                         text="Displace mesh")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_PT_tools_add_object.append(displace_mesh_button)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_PT_tools_add_object.remove(displace_mesh_button)

if __name__ == '__main__':
    register()
