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
    'name': 'Drop to Ground',
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
def get_align_matrix(location, normal):
    up = Vector((0,0,1))
    angle = normal.angle(up)
    axis = up.cross(normal)
    mat_rot = Matrix.Rotation(angle, 4, axis)
    mat_loc = Matrix.Translation(location)
    mat_align = mat_rot * mat_loc
    return mat_align

def transform_ground_to_world(sc, ground):
    tmpMesh = ground.to_mesh(sc, True, 'PREVIEW')
    tmpMesh.transform(ground.matrix_world)
    tmp_ground = bpy.data.objects.new('tmpGround', tmpMesh)
    sc.objects.link(tmp_ground)
    sc.update()
    return tmp_ground

def get_lowest_world_co_from_mesh(ob, mat_parent=None):
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
#        print ("Z: ", v.co.z, v_world_co.z, "(", ("null" if count == 0 else lowest_co), ")")
        if count == 0:
#            print ("Reset")
            lowest_co = v_world_co.z
            co_sum = v_world_co
            count = 1
        elif v_world_co.z == lowest_co:
#            print ("inc count")
            count = count + 1
            co_sum += v_world_co
        elif v_world_co.z < lowest_co:
#            print ("new low")
            lowest_co = v_world_co.z
            co_sum = v_world_co
            count = 1

    bme.free()
    center_lowest_co = co_sum / count
    print(count, " vertices at lowest", center_lowest_co.z)
    return center_lowest_co

def get_lowest_world_co(context, ob, mat_parent=None):
    if ob.type == 'MESH':
        return get_lowest_world_co_from_mesh(ob)

    elif ob.type == 'EMPTY' and ob.dupli_type == 'GROUP':
        if not ob.dupli_group:
            return None

        else:
            lowest_co = None
            for ob_l in ob.dupli_group.objects:
                if ob_l.type == 'MESH':
                    lowest_ob_l = get_lowest_world_co_from_mesh(ob_l, ob.matrix_world)
                    if not lowest_co:
                        lowest_co = lowest_ob_l
                    if lowest_ob_l.z < lowest_co.z:
                        lowest_co = lowest_ob_l

            return lowest_co

def drop_objects(self, context):
    ground = context.object
    obs = context.selected_objects
    obs.remove(ground)
    tmp_ground = transform_ground_to_world(context.scene, ground)
    down = Vector((0, 0, -10000))

    for ob in obs:
        if self.use_origin:
            lowest_world_co = ob.location
        else:
            lowest_world_co = get_lowest_world_co(context, ob)
        if not lowest_world_co:
            print(ob.type, 'is not supported. Failed to drop', ob.name)
            continue
        hit_location, hit_normal, hit_index = tmp_ground.ray_cast(lowest_world_co,
                                                                  lowest_world_co + down)
        if hit_index == -1:
            print(ob.name, 'didn\'t hit the ground')
            continue

        # simple drop down
        to_ground_vec =  hit_location - lowest_world_co
        ob.location += to_ground_vec

        # drop with align to hit normal
        if self.align:
            to_center_vec = ob.location - hit_location #vec: hit_loc to origin
            # rotate object to align with face normal
            mat_normal = get_align_matrix(hit_location, hit_normal)
            rot_euler = mat_normal.to_euler()
            mat_ob_tmp = ob.matrix_world.copy().to_3x3()
            mat_ob_tmp.rotate(rot_euler)
            mat_ob_tmp = mat_ob_tmp.to_4x4()
            ob.matrix_world = mat_ob_tmp
            # move_object to hit_location
            ob.location = hit_location
            # move object above surface again
            to_center_vec.rotate(rot_euler)
            ob.location += to_center_vec

    #cleanup
    bpy.ops.object.select_all(action='DESELECT')
    tmp_ground.select = True
    bpy.ops.object.delete('EXEC_DEFAULT')
    for ob in obs:
        ob.select = True
    ground.select = True

#################################################################
class OBJECT_OT_drop_to_ground(Operator):
    """Drop selected objects on active object"""
    bl_idname = "object.drop_on_active"
    bl_label = "Drop to Ground"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Drop selected objects on active object"

    align = BoolProperty(
            name="Align to ground",
            description="Aligns the object to the ground",
            default=True)
    use_origin = BoolProperty(
            name="Use Center",
            description="Drop to objects origins",
            default=False)

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) >= 2
    
    ##### EXECUTE #####
    def execute(self, context):
        print('\nDropping Objects')
        drop_objects(self, context)
        return {'FINISHED'}

#################################################################
def drop_to_ground_button(self, context):
    self.layout.operator(OBJECT_OT_drop_to_ground.bl_idname,
                         text="Drop to Ground")
    
def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_PT_tools_add_object.append(drop_to_ground_button)
    
def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_PT_tools_add_object.remove(drop_to_ground_button)

if __name__ == '__main__':
    register()
