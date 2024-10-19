import bpy
import requests
import zipfile
import io
import json
import os
import shutil
from .lib import charlib
from .lib.charlib import DataDir
from bpy.props import StringProperty, BoolProperty, CollectionProperty, EnumProperty
from bpy.types import PropertyGroup, AddonPreferences, Operator
from bpy_extras.io_utils import ImportHelper


undo_modes = [("S", "Simple", "Don't show additional info in undo list")]
undo_default_mode = "S"
undo_update_hook = None

def load_character_list():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.realpath(os.path.join(script_dir, "..", "data"))
    json_file = os.path.join(data_dir, "lists.json")
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data.get("characters", [])
    except Exception as e:
        print(f"Error loading lists.json: {e}")
        return []

class CharacterItem(PropertyGroup):
    name: StringProperty(name="Character Name")
    license: StringProperty(name="License")
    downloaded: BoolProperty(name="Downloaded", default=False)

if "undo_push" in dir(bpy.ops.ed):
    undo_modes.append(("A", "Advanced", "Undo system with full info. Can cause problems on some systems."))
    undo_default_mode = "A"

class CharMorphPrefs(AddonPreferences):
    bl_idname = __package__

    undo_mode: EnumProperty(
        name="Undo mode",
        description="Undo mode",
        items=[
            ("S", "Simple", "Don't show additional info in undo list"),
            ("A", "Advanced", "Undo system with full info. Can cause problems on some systems.")
        ],
        default="S"
    )
    adult_mode: BoolProperty(
        name="Adult mode",
        description="No censors, enable adult assets (genitals, pubic hair)",
        default=False
    )
    
    character_list: CollectionProperty(type=CharacterItem)

    data_path: StringProperty(
        name="Data Path",
        description="Path to CharMorph data",
        default="",
        subtype='DIR_PATH'
    )

    def __init__(self):
        super().__init__()
        self.load_characters()

    def load_characters(self):
        self.character_list.clear()
        characters = load_character_list()
        for char in characters:
            item = self.character_list.add()
            item.name = char.get("name", "")
            item.license = char.get("license", "")
            item.downloaded = char.get("downloaded", False)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "undo_mode")
        layout.prop(self, "adult_mode")
        
        row = layout.row()
        row.prop(self, "data_path")
        row.operator("charmorph.select_directory", text="Migrate Data")

        layout.label(text="Available Characters:")
        for char in self.character_list:
            row = layout.row()
            row.label(text=char.name)
            row.label(text=char.license)
            if char.downloaded:
                row.operator("charmorph.delete_character", text="Delete", icon='TRASH').character_name = char.name
            else:
                row.operator("charmorph.download_character", text="Download", icon='IMPORT').character_name = char.name

class CHARMORPH_OT_select_directory(Operator, ImportHelper):
    bl_idname = "charmorph.select_directory"
    bl_label = "Select Directory for Data Migration"
    
    filename_ext = ""
    use_filter_folder = True
    
    directory: StringProperty(
        name="Destination Folder",
        description="Select the destination folder for data migration",
        subtype='DIR_PATH'
    )
    
    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        source_dir = charlib.DataDir.dirpath
        
        if not os.path.exists(source_dir):
            self.report({'ERROR'}, f"Source directory not found: {source_dir}")
            return {'CANCELLED'}
        
        try:
            # Copy data from source to destination
            shutil.copytree(source_dir, self.directory, dirs_exist_ok=True)
            prefs.data_path = self.directory
            self.report({'INFO'}, f"Data migrated successfully to: {self.directory}")
        except Exception as e:
            self.report({'ERROR'}, f"Error during data migration: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class CHARMORPH_OT_download_character(Operator):
    bl_idname = "charmorph.download_character"
    bl_label = "Download Character"
    character_name: StringProperty()
    
    def execute(self, context):
        # Implement character download logic here
        return {'FINISHED'}

class CHARMORPH_OT_delete_character(Operator):
    bl_idname = "charmorph.delete_character"
    bl_label = "Delete Character"
    character_name: StringProperty()
    
    def execute(self, context):
        # Implement character deletion logic here
        return {'FINISHED'}

classes = (
    CharacterItem,
    CharMorphPrefs,
    CHARMORPH_OT_select_directory,
    CHARMORPH_OT_download_character,
    CHARMORPH_OT_delete_character,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
