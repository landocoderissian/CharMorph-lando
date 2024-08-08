import bpy

def append_color_ramp_from_external():
    # Define the path to the external blend file and the material
    blend_file_path = "./lib/shader.blend/Material/"
    material_name = "Rody_Body"

    # Append the material from the external file
    with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
        if material_name in data_from.materials:
            data_to.materials = [material_name]

    # The material is now appended and accessible
    appended_material = bpy.data.materials.get(material_name)
    
    if not appended_material:
        print("Material not found in the appended file.")
        return None

    # Look for the ColorRamp node in the appended material's node tree
    color_ramp_node = None
    if appended_material.use_nodes:
        for node in appended_material.node_tree.nodes:
            if node.type == 'VALTORGB':  # ColorRamp node type
                color_ramp_node = node
                break

    if color_ramp_node:
        return color_ramp_node
    else:
        print("ColorRamp node not found in the material.")
        return None

def toonify_material(material):
    # Ensure the material uses nodes
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Find existing image texture node, if any
    image_texture = None
    for node in nodes:
        if node.type == 'TEX_IMAGE':
            image_texture = node
            break
    
    if not image_texture:
        return  # No image texture, skip this material

    # Clear existing nodes except the image texture
    for node in nodes:
        if node != image_texture:
            nodes.remove(node)

    # Add Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (-300, 300)

    # Add Shader to RGB
    shader_to_rgb = nodes.new(type='ShaderNodeShaderToRGB')
    shader_to_rgb.location = (-100, 300)

    # Append the ColorRamp from the external file
    color_ramp = append_color_ramp_from_external()
    if color_ramp:
        color_ramp = nodes.new(type='ShaderNodeValToRGB')
        color_ramp.location = (100, 300)
        # Copy the values from the appended ColorRamp
        for i, element in enumerate(color_ramp.color_ramp.elements):
            color_ramp.color_ramp.elements[i].position = element.position
            color_ramp.color_ramp.elements[i].color = element.color
    else:
        return  # Skip this material if ColorRamp wasn't found or loaded

    # Add Emission nodes
    emission1 = nodes.new(type='ShaderNodeEmission')
    emission1.location = (300, 400)
    
    emission2 = nodes.new(type='ShaderNodeEmission')
    emission2.location = (300, 200)
    
    # Add Mix Shader
    mix_shader = nodes.new(type='ShaderNodeMixShader')
    mix_shader.location = (500, 300)
    
    # Add Material Output
    material_output = nodes.new(type='ShaderNodeOutputMaterial')
    material_output.location = (700, 300)

    # Add Hue/Saturation Value
    hsv = nodes.new(type='ShaderNodeHueSaturation')
    hsv.location = (-300, 0)
    
    # Link nodes
    links.new(image_texture.outputs['Color'], hsv.inputs['Color'])
    links.new(image_texture.outputs['Color'], emission1.inputs['Color'])
    links.new(hsv.outputs['Color'], emission2.inputs['Color'])
    links.new(principled.outputs['BSDF'], shader_to_rgb.inputs['Shader'])
    links.new(shader_to_rgb.outputs['Color'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], mix_shader.inputs['Fac'])
    links.new(mix_shader.outputs['Shader'], material_output.inputs['Surface'])
    links.new(emission1.outputs['Emission'], mix_shader.inputs[1])
    links.new(emission2.outputs['Emission'], mix_shader.inputs[2])
    
    # Set default values
    hsv.inputs['Saturation'].default_value = 1.0
    hsv.inputs['Value'].default_value = 0.2
    emission2.inputs['Strength'].default_value = 1.0

def apply_toonify():
    obj = bpy.context.active_object
    
    if obj is not None:
        for material_slot in obj.material_slots:
            material = material_slot.material
            if material:
                toonify_material(material)
    else:
        print("No active object selected.")

class ToonifyOperator(bpy.types.Operator):
    bl_idname = "object.toonify_operator"
    bl_label = "Toonify"
    
    def execute(self, context):
        apply_toonify()
        return {'FINISHED'}

class ToonifyPanel(bpy.types.Panel):
    bl_label = "Toonify"
    bl_idname = "OBJECT_PT_toonify"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Toonify'
    
    def draw(self, context):
        layout = self.layout
        layout.operator("object.toonify_operator")

def register():
    bpy.utils.register_class(ToonifyOperator)
    bpy.utils.register_class(ToonifyPanel)

def unregister():
    bpy.utils.unregister_class(ToonifyOperator)
    bpy.utils.unregister_class(ToonifyPanel)

if __name__ == "__main__":
    register()
