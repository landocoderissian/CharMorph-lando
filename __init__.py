# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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
#
# Copyright (C) 2020 Michael Vigovsky

import logging
import bpy  # pylint: disable=import-error
from bpy.types import Operator
from bpy.utils import register_class, unregister_class

from . import common, library, assets, hair, morphing, randomize, file_io, finalize, rig, rigify, pose, prefs, cmedit, toonify

from .lib import charlib, file_preperation, materials

logger = logging.getLogger(__name__)

bl_info = {
    "name": "CharMorph-lando",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > CharMorph",
    "description": "Character creation and morphing tool",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

VERSION_ANNEX = ""

owner = object()


class VIEW3D_PT_CharMorph(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_CharMorph"
    bl_label = "".join(("CharMorph ", ".".join(str(item) for item in bl_info["version"]), VERSION_ANNEX))
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CharMorph"
    bl_order = 1

    def draw(self, _):
        pass


def on_select():
    common.manager.on_select()


@bpy.app.handlers.persistent
def undoredo_post(_context, _scene):
    common.manager.on_select(undoredo=True)


def subscribe_select_obj():
    bpy.msgbus.clear_by_owner(owner)
    bpy.msgbus.subscribe_rna(
        owner=owner,
        key=(bpy.types.LayerObjects, "active"),
        args=(),
        options={"PERSISTENT"},
        notify=on_select)


@bpy.app.handlers.persistent
def load_handler(_):
    subscribe_select_obj()
    common.manager.del_charmorphs()
    on_select()


@bpy.app.handlers.persistent
def select_handler(_):
    on_select()


classes = [
    prefs.CharacterItem,
    prefs.CharMorphPrefs,
    prefs.CHARMORPH_OT_select_directory,
    prefs.CHARMORPH_OT_download_character,
    prefs.CHARMORPH_OT_delete_character,
    VIEW3D_PT_CharMorph
]
uiprops = [bpy.types.PropertyGroup]
operators: list[type] = []


CharMorphUIProps = type("CharMorphUIProps", tuple(uiprops), {})
classes[0] = CharMorphUIProps

_is_registered = False

def register():
    global _is_registered
    if not _is_registered:
        prefs.register()
        for cls in classes:
            try:
                bpy.utils.register_class(cls)
            except ValueError as e:
                print(f"Skipping registration of {cls.__name__}: {str(e)}")
        
        logger.debug("Charmorph register")
        charlib.library.load()
        common.register()
        morphing.register()
        finalize.register()
        assets.register()
        hair.register()
        cmedit.register()
        library.register()
        bpy.types.WindowManager.charmorph_ui = bpy.props.PointerProperty(type=CharMorphUIProps, options={"SKIP_SAVE"})
        subscribe_select_obj()

        bpy.app.handlers.load_post.append(load_handler)
        bpy.app.handlers.undo_post.append(undoredo_post)
        bpy.app.handlers.redo_post.append(undoredo_post)
        bpy.app.handlers.depsgraph_update_post.append(select_handler)
        _is_registered = True

def unregister():
    global _is_registered
    if _is_registered:
        prefs.unregister()
        for cls in reversed(classes):
            try:
                bpy.utils.unregister_class(cls)
            except RuntimeError:
                # Class is already unregistered, so we can skip it
                pass
        
        rigging.unregister()
        materials.unregister()
        library.unregister()
        cmedit.unregister()
        hair.unregister()
        assets.unregister()
        finalize.unregister()
        morphing.unregister()
        common.unregister()
        
        for hlist in bpy.app.handlers:
            if not isinstance(hlist, list):
                continue
            for handler in hlist:
                if handler in (load_handler, select_handler):
                    hlist.remove(handler)
                    break

        bpy.msgbus.clear_by_owner(owner)
        del bpy.types.WindowManager.charmorph_ui
        common.manager.del_charmorphs()
        _is_registered = False


if __name__ == "__main__":
    register()
