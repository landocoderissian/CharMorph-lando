import bpy
import requests
import zipfile
import io
import json
import os
from .lib import charlib


undo_modes = [("S", "Simple", "Don't show additional info in undo list")]
undo_default_mode = "S"
undo_update_hook = None

if "undo_push" in dir(bpy.ops.ed):
    undo_modes.append(("A", "Advanced", "Undo system with full info. Can cause problems on some systems."))
    undo_default_mode = "A"

class CHAR_MORPH_OT_download_character(bpy.types.Operator):
    bl_idname = "charmorph.download_character"
    bl_label = "Download Character"

    character_name: bpy.props.StringProperty() #type: ignore

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        char_data = next((char for char in prefs.character_list if char["name"] == self.character_name), None)
        
        if char_data:
            response = requests.get(char_data["repo"])
            if response.status_code == 200:
                release_data = response.json()
                asset_url = release_data["assets"][0]["browser_download_url"]
                
                response = requests.get(asset_url)
                if response.status_code == 200:
                    z = zipfile.ZipFile(io.BytesIO(response.content))
                    z.extractall(charlib.global_data_dir.dirpath)
                    
                    char_data["downloaded"] = True
                    self.report({'INFO'}, f"Character {self.character_name} downloaded and extracted successfully.")
                    return {'FINISHED'}
        
        self.report({'ERROR'}, f"Failed to download character {self.character_name}.")
        return {'CANCELLED'}

# Operator to select a directory and migrate data
class CHAR_MORPH_OT_select_directory(bpy.types.Operator):
    bl_idname = "charmorph.select_directory"
    bl_label = "Select Directory"

    directory: bpy.props.StringProperty(subtype="DIR_PATH")  # type: ignore

    def execute(self, context):
        if not self.directory:
            self.report({'ERROR'}, "No directory selected")
            return {'CANCELLED'}

        try:
            # Migrate the data to the new directory
            charlib.global_data_dir.migrate_data(self.directory)

            # Update the global library instance with the new directory
            library = charlib.Library(charlib.global_data_dir.dirpath)

            # Save the new directory path to a config file for persistence
            charlib.save_directory_path(charlib.global_data_dir.dirpath)

            self.report({'INFO'}, f"Data migrated to {self.directory} and library updated.")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to migrate data: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# Preferences Class
class CharMorphPrefs(bpy.types.AddonPreferences):
    bl_idname = "CharMorph-lando"

    undo_mode: bpy.props.EnumProperty( #type: ignore
        name="Undo mode",
        description="Undo mode",
        items=[
            ("S", "Simple", "Don't show additional info in undo list"),
            ("A", "Advanced", "Undo system with full info. Can cause problems on some systems.")
        ],
        default="S"
    )
    adult_mode: bpy.props.BoolProperty( # type: ignore
        name="Adult mode",
        description="No censors, enable adult assets (genitals, pubic hair)",
        default=False
    )
    
    character_list: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup) #type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(text="CharMorph Preferences", icon='PREFERENCES')
        layout.prop(self, "undo_mode")
        layout.prop(self, "adult_mode")
        layout.operator("charmorph.select_directory", text="Migrate Data")

        # Character download section
        layout.label(text="Available Characters:")
        for char in self.character_list:
            row = layout.row()
            row.label(text=char.name)
            row.label(text=char.license)
            if char.get("downloaded", False):
                row.label(text="Downloaded", icon='CHECKMARK')
            else:
                row.operator("charmorph.download_character", text="Download").character_name = char.name


def get_prefs():
    return bpy.context.preferences.addons.get(__package__)


def load_character_list():
    prefs = bpy.context.preferences.addons[__package__].preferences
    with open(os.path.join(os.path.dirname(__file__), "list.json"), "r") as f:
        data = json.load(f)
    prefs.character_list.clear()
    for char in data["assets"]:
        item = prefs.character_list.add()
        item.name = char["name"]
        item.license = char["license"]
        item["repo"] = char["repo"]
        item["downloaded"] = False

# Register and Unregister Classes
classes = [
    CharMorphPrefs,
    CHAR_MORPH_OT_select_directory,
    CHAR_MORPH_OT_download_character,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        load_character_list()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()