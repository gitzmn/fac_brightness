bl_info = {
    "name": "Compositor Fac Animator",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "Compositor > Sidebar > Fac Animator",
    "description": "Links .txt brightness data to the 'Factor' input of compositor nodes",
    "category": "Compositing",
}

import bpy
import os
import json
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, FloatProperty

handler_added = False

# List of common Factor input names
FACTOR_INPUT_NAMES = ['Fac', 'factor', 'use_alpha']

# ---------------------- Core Logic ----------------------
def update_fac(scene):
    props = scene.fac_animator_props
    if not props.target_node_name or not props.brightness_data:
        return

    # Get the compositor node tree from the current scene
    node_tree = scene.node_tree
    if not node_tree:
        return

    target_node = node_tree.nodes.get(props.target_node_name)
    if not target_node:
        return

    # Find the Factor input dynamically
    factor_input = None
    for input_name in FACTOR_INPUT_NAMES:
        if input_name in target_node.inputs:
            factor_input = target_node.inputs[input_name]
            break

    if not factor_input:
        return

    try:
        brightness_data = json.loads(props.brightness_data)
        current_frame = scene.frame_current - 1
        if 0 <= current_frame < len(brightness_data):
            factor_input.default_value = brightness_data[current_frame] * props.scale_factor
    except:
        pass

# ---------------------- Operator ----------------------
class FAC_OT_LinkBrightness(Operator):
    bl_idname = "fac.link_brightness"
    bl_label = "Link Brightness to Factor"
    bl_description = "Link .txt brightness data to the node's Factor input"

    def execute(self, context):
        global handler_added
        scene = context.scene
        props = scene.fac_animator_props

        if not props.target_node_name:
            self.report({'ERROR'}, "Select a compositor node first!")
            return {'CANCELLED'}

        # Get the compositor node tree from the current scene
        node_tree = scene.node_tree
        if not node_tree:
            self.report({'ERROR'}, "No compositor node tree found!")
            return {'CANCELLED'}

        target_node = node_tree.nodes.get(props.target_node_name)
        if not target_node:
            self.report({'ERROR'}, "Selected node not found!")
            return {'CANCELLED'}

        # Debug: Print all inputs of the selected node
        print(f"Available inputs for node '{props.target_node_name}':")
        for input in target_node.inputs:
            print(f"- {input.name} (identifier: {input.identifier})")

        # Find the Factor input dynamically
        factor_input = None
        for input_name in FACTOR_INPUT_NAMES:
            if input_name in target_node.inputs:
                factor_input = target_node.inputs[input_name]
                break

        if not factor_input:
            self.report({'ERROR'}, f"Selected node has no Factor input! Available inputs: {[input.name for input in target_node.inputs]}")
            return {'CANCELLED'}

        filepath = bpy.path.abspath(props.brightness_file)
        if not os.path.isfile(filepath):
            self.report({'ERROR'}, f"File not found: {filepath}")
            return {'CANCELLED'}

        try:
            with open(filepath, 'r') as f:
                props.brightness_data = json.dumps([float(line.strip()) for line in f])
        except Exception as e:
            self.report({'ERROR'}, f"File error: {str(e)}")
            return {'CANCELLED'}

        if not handler_added:
            bpy.app.handlers.frame_change_pre.append(update_fac)
            handler_added = True

        return {'FINISHED'}

# ---------------------- UI Panel ----------------------
class FAC_PT_ControlPanel(Panel):
    bl_label = "Fac Animator"
    bl_idname = "NODE_PT_fac_animator"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Fac Animator"

    def draw(self, context):
        layout = self.layout
        props = context.scene.fac_animator_props
        
        layout.prop_search(
            props, "target_node_name", 
            context.scene.node_tree, "nodes",
            text="Target Node"
        )
        layout.prop(props, "brightness_file")
        layout.prop(props, "scale_factor")
        layout.operator("fac.link_brightness")

# ---------------------- Properties ----------------------
class FacAnimatorProperties(PropertyGroup):
    brightness_file: StringProperty(
        name="Brightness File",
        subtype='FILE_PATH',
        description="Path to .txt file with 0-1 values"
    )
    
    target_node_name: StringProperty(
        name="Target Node",
        description="Name of the node with 'Factor' input"
    )
    
    scale_factor: FloatProperty(
        name="Scale Factor",
        default=1.0,
        min=0.01,
        max=1000.0
    )
    
    brightness_data: StringProperty(
        name="Brightness Data",
        default="[]"
    )

# ---------------------- Registration ----------------------
classes = (
    FAC_OT_LinkBrightness,
    FAC_PT_ControlPanel,
    FacAnimatorProperties,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.fac_animator_props = bpy.props.PointerProperty(type=FacAnimatorProperties)

def unregister():
    global handler_added
    if handler_added:
        bpy.app.handlers.frame_change_pre.remove(update_fac)
        handler_added = False
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.fac_animator_props

if __name__ == "__main__":
    register()

