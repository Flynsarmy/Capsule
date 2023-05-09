
from gc import collect
from re import search
import bpy, bmesh, random, platform

from mathutils import Vector
from bpy.types import Operator
from bpy.props import IntProperty, BoolProperty, FloatProperty, EnumProperty, PointerProperty, StringProperty, CollectionProperty

from .tk_utils import search as search_utils
from .tk_utils import select as select_utils
from .tk_utils import object_ops
from .export_formats import CAP_ExportFormat
from . import export_presets

#///////////////// - LOCATION DEFAULTS - ///////////////////////////////////////////

class CAPSULE_OT_Add_Path(Operator):
    """Create a new location."""

    bl_idname = "scene.cap_addpath"
    bl_label = "Add"

    def execute(self, context):
        #print(self)

        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile

        newPath = cap_file.location_presets.add()
        newPath.name = "Location " + str(len(cap_file.location_presets))
        newPath.path = ""

        # Position the index to the current location of the
        #count = 0
        #for i, item in enumerate(scn.path_defaults, 1):
            #count += 1

        #oldIndex = scn.path_list_index

        #scn.path_defaults.move(count - 1, scn.path_list_index)
        #scn.path_list_index = oldIndex

        return {'FINISHED'}

class CAPSULE_OT_Delete_Path(Operator):
    """
    Delete the selected location from the list.  This will also set the Location Preset of all
    objects and collections that used this selected location to 'None'
    """

    bl_idname = "scene.cap_deletepath"
    bl_label = "Remove"

    def execute(self, context):
        #print(self)

        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile

        preset_index = cap_file.location_presets_listindex

        # Ensure that any objects with a matching preset are set to None.
        # The index needs increasing by one as it doesnt include 'None'
        objects = bpy.data.objects
        for obj in objects:
            cap_obj = obj.CAPObj
            if cap_obj.location_preset == str(preset_index + 1):
                cap_obj.location_preset = '0'

        collections = search_utils.GetSceneCollections(context.scene, False)
        for collection in collections:
            cap_col = collection.CAPCol
            if cap_col.location_preset == str(preset_index + 1):
                cap_col.location_preset = '0'
        
        # TODO: Ensure the selection interface is updated so it gets the new value!
        # TODO: Ensure this is as efficient as it can be for large scenes
        
        # Once everything has been set, remove it.
        cap_file.location_presets.remove(preset_index)

        # ensure the selected list index is within the list bounds
        if len(cap_file.location_presets) > 0:
            cap_file.location_presets_listindex -= 1
        

        return {'FINISHED'}

class CAPSULE_OT_Add_Location_Path_Tag(Operator):
    """Adds a new path tag to the currently selected path."""

    bl_idname = "scene.cap_add_location_path_tag"
    bl_label = "Add Path Tag"

    path_tags: EnumProperty(
        name = "Add Path Tag",
        description = "",
        items =  (
        ('export_name', 'Export Name', 'Adds a folder with the name of the Object or Collection being exported.'),
        # ('object_type', 'Object Type', 'Adds a folder with the object type.'),
        # ('collection', 'Collection Name', 'Adds a folder with the collection name.'),
        ('blend_file_name', 'Blend File Name', 'Adds a folder with the blend file name.'),
        # ('location_preset_name', 'Location Preset Name', 'Adds a folder with the Location Preset name used on export.'),
        ('export_preset_name', 'Export Preset Name', 'Adds a folder with the Export Preset name used on export.'),
        ('export_date_ymd', 'Export Date (Year-Month-Day)', 'Adds a folder with the date of the export.'),
        ('export_date_dmy', 'Export Date (Day-Month-Year)', 'Adds a folder with the date of the export.'),
        ('export_date_mdy', 'Export Date (Month-Year-Day)', 'Adds a folder with the date of the export.'),
        ('export_time_hm', 'Export Time (Hour-Minute)', 'Adds a folder with the time of the export.'),
        ('export_time_hms', 'Export Time (Hour-Minute-Second)', 'Adds a folder with the time of the export.'),
        ),
    )

    def execute(self, context):
        #print(self)

        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile
        
        # get the selected path
        path_index = cap_file.location_presets_listindex
        new_path = cap_file.location_presets[path_index].path
        end_path = ""

        # directory failsafe
        if platform.system() == 'Windows':
            if new_path.endswith("\\") == False and new_path.endswith("//") == False:
                new_path += "\\"
            end_path = "\\"
        else:
            if new_path.endswith("/") == False:
                new_path += "/"
            end_path = "\\"

        # insert the selected option into the currently selected path
        new_path += "^"
        new_path += self.path_tags
        new_path += "^" + end_path
        
        cap_file.location_presets[path_index].path = new_path

        return {'FINISHED'}

class CAPSULE_OT_Add_ExportPreset_Path_Tag(Operator):
    """Adds a new path tag to the current Export Preset."""

    bl_idname = "scene.cap_add_exportpreset_path_tag"
    bl_label = "Add Path Tag"

    path_tags: EnumProperty(
        name = "Add Path Tag",
        description = "",
        items =  (
        ('export_name', 'Export Name', 'Adds a folder with the name of the Object or Collection being exported.'),
        # ('object_type', 'Object Type', 'Adds a folder with the object type.'),
        # ('collection', 'Collection Name', 'Adds a folder with the collection name.'),
        ('blend_file_name', 'Blend File Name', 'Adds a folder with the blend file name.'),
        ('location_preset_name', 'Location Preset Name', 'Adds a folder with the Location Preset name used on export.'),
        # ('export_preset_name', 'Export Preset Name', 'Adds a folder with the Export Preset name used on export.'),
        ('export_date_ymd', 'Export Date (Year-Month-Day)', 'Adds a folder with the date of the export.'),
        ('export_date_dmy', 'Export Date (Day-Month-Year)', 'Adds a folder with the date of the export.'),
        ('export_date_mdy', 'Export Date (Month-Year-Day)', 'Adds a folder with the date of the export.'),
        ('export_time_hm', 'Export Time (Hour-Minute)', 'Adds a folder with the time of the export.'),
        ('export_time_hms', 'Export Time (Hour-Minute-Second)', 'Adds a folder with the time of the export.'),
        ),
    )

    def execute(self, context):
        #print(self)

        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile
        selected_export_preset = cap_file.export_presets[cap_file.export_presets_listindex]

        # get the selected path
        new_path = selected_export_preset.sub_directory
        end_path = ""

        # directory failsafe
        if platform.system() == 'Windows':
            if new_path.endswith("\\") == False and new_path.endswith("//") == False:
                new_path += "\\"
            end_path = "\\"
        else:
            if new_path.endswith("/") == False:
                new_path += "/"
            end_path = "\\"

        # insert the selected option into the currently selected path
        new_path += "^"
        new_path += self.path_tags
        new_path += "^" + end_path
        
        selected_export_preset.sub_directory = new_path

        return {'FINISHED'}

class CAPSULE_OT_Add_Export(Operator):
    """Create a new file preset."""

    bl_idname = "scene.cap_addexport"
    bl_label = "Add"

    def get_unique_id(self, context, cap_file):
        newID = random.randrange(0, 1000000)

        for preset in cap_file.export_presets:
            if preset.instance_id == newID:
                newID = self.get_unique_id(context, cap_file)

        return newID

    def execute(self, context):
        #print(self)

        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile


        # make the new file preset
        newDefault = cap_file.export_presets.add()
        newDefault.name = "Export " + str(len(cap_file.export_presets))
        newDefault.path = ""

        # Ensure the tag index keeps within a window
        cap_file.export_presets_listindex = len(cap_file.export_presets) - 1

        return {'FINISHED'}



class CAPSULE_OT_Delete_Export(Operator):
    """
    Delete the selected export preset from the list.  This will also set the Location Preset of all
    objects and collections that used this selected location to 'None'
    """

    bl_idname = "scene.cap_deleteexport"
    bl_label = "Delete Export Preset"

    #StringProperty(default = "Are you sure you wish to delete the selected preset?")

    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile

        if len(cap_file.export_presets) > 0:
            return True

        return False

    def execute(self, context):
        #print(self)

        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile

        preset_index = cap_file.export_presets_listindex

        # Ensure that any objects with a matching preset are set to None.
        # The index needs increasing by one as it doesnt include 'None'
        objects = bpy.data.objects
        for obj in objects:
            cap_obj = obj.CAPObj
            if cap_obj.export_preset == str(preset_index + 1):
                cap_obj.export_preset = '0'

        collections = search_utils.GetSceneCollections(context.scene, False)
        for collection in collections:
            cap_col = collection.CAPCol
            if cap_col.export_preset == str(preset_index + 1):
                cap_col.export_preset = '0'
        
        # TODO: Ensure the selection interface is updated so it gets the new value!
        # TODO: Ensure this is as efficient as it can be for large scenes
        
        # Once everything has been set, remove it.
        cap_file.export_presets.remove(preset_index)

        # ensure the selected list index is within the list bounds
        if cap_file.export_presets_listindex > 0:
            cap_file.export_presets_listindex -= 1

        return {'FINISHED'}


class CAPSULE_OT_Shift_Path_Up(Operator):
    """Move the current entry in the list up by one"""

    bl_idname = "scene.cap_shiftup"
    bl_label = "Add"

    def execute(self, context):
        #print(self)

        scn = context.scene.CAPScn
        obj = context.active_object.CAPObj

        scn.path_defaults.move(scn.path_list_index, scn.path_list_index - 1)
        scn.path_list_index -= 1

        return {'FINISHED'}

class CAPSULE_OT_Shift_Path_Down(Operator):
    """Move the current entry in the list down by one"""

    bl_idname = "scene.cap_shiftdown"
    bl_label = "Remove"

    def execute(self, context):
        #print(self)

        scn = context.scene.CAPScn
        obj = context.active_object.CAPObj

        scn.path_defaults.move(scn.path_list_index, scn.path_list_index + 1)
        scn.path_list_index += 1

        return {'FINISHED'}


class CAPSULE_OT_Clear_List(Operator):
    """Delete all objects from the export list, and un-mark them for export"""

    bl_idname = "scene.cap_clearlist"
    bl_label = "Delete All"

    def execute(self, context):
        #print(self)

        scn = context.scene.CAPScn
        objectTab = int(str(scn.list_switch))

        if objectTab == 1:
            for object in context.scene.objects:
                obj = object.CAPObj
                obj.enable_export = False
                obj.in_export_list = False
            scn.object_list.clear()

        elif objectTab == 2:
            for collection in search_utils.GetSceneCollections(context.scene, False):
                col = collection.CAPCol
                col.enable_export = False
                col.in_export_list = False
            scn.collection_list.clear()

        return {'FINISHED'}

class CAPSULE_OT_Refresh_List(Operator):
    """Rebuild the list based on available objects or collections in the scene."""

    bl_idname = "scene.cap_refreshlist"
    bl_label = "Refresh"

    def execute(self, context):
        #print(self)

        scn = context.scene.CAPScn
        objectTab = int(str(scn.list_switch))

        if objectTab == 1:
            scn.object_list.clear()
            for obj in context.scene.objects:
                if obj.CAPObj.in_export_list is True:
                    entry = scn.object_list.add()
                    entry.object = obj
                    entry.enable_export = obj.CAPObj.enable_export


        elif objectTab == 2:
            scn.collection_list.clear()
            for collection in search_utils.GetSceneCollections(context.scene, False):
                print(collection)
                if collection.CAPCol.in_export_list is True:
                        entry = scn.collection_list.add()
                        entry.collection = collection
                        entry.enable_export = collection.CAPCol.enable_export

        return {'FINISHED'}


class CAPSULE_OT_Reset_Properties(Operator):
    """Resets all assigned export properties to every Object and Collection in every scene, and clears Export Lists"""

    bl_idname = "scene.cap_resetsceneprops"
    bl_label = "Reset Scene"

    def execute(self, context):
        #print(self)

        #self.export_stats['object_export_count'] = 0

        # Keep a record of the selected and active objects to restore later
        active = None
        selected = []

        for collection in bpy.data.collections:
            col = collection.CAPCol
            col.enable_export = False
            col.origin_point = 'Object'
            col.location_preset = '0'
            col.export_preset = '0'
            col.pack_script = None

        for object in bpy.data.objects:
            obj = object.CAPObj
            obj.enable_export = False
            obj.origin_export = "Scene"
            obj.root_object = None
            obj.location_preset = '0'
            obj.export_preset = '0'
            col.pack_script = None
        
        scn = context.scene.CAPScn
        list_tab = str(scn.list_switch)

        scn.list_switch = '1'
        bpy.ops.scene.cap_clearlist()

        scn.list_switch = '2'
        bpy.ops.scene.cap_clearlist()

        scn.list_switch = list_tab

        return {'FINISHED'}


class CAPSULE_OT_UI_Group_Separate(Operator):
    """Toggle the drop-down menu for separate collection export options"""

    bl_idname = "scene.cap_grpseparate"
    bl_label = ""

    def execute(self, context):
        #print(self)

        scn = context.scene.CAPScn
        ui = context.scene.CAPUI

        if ui.group_separate_dropdown is True:
            ui.group_separate_dropdown = False
        else:
            ui.group_separate_dropdown = True

        return {'FINISHED'}

class CAPSULE_OT_UI_Group_Options(Operator):
    """Toggle the drop-down menu for separate collection export options"""

    bl_idname = "scene.cap_grpoptions"
    bl_label = ""

    def execute(self, context):
        #print(self)

        scn = context.scene.CAPScn
        ui = context.scene.CAPUI

        if ui.group_options_dropdown is True:
            ui.group_options_dropdown = False
        else:
            ui.group_options_dropdown = True

        return {'FINISHED'}


class CAPSULE_OT_Create_ExportData(Operator):
    """Create a new empty object for which Capsule data is stored, and where both Active Export Presets and other scene data is stored."""

    bl_idname = "cap.exportdata_create"
    bl_label = "Create Capsule Data"

    def execute(self, context):
        #print(self)

        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[__package__].preferences

        # Ensure we're in the right context before creating the datablock.
        override = object_ops.Find3DViewContext()
        prev_mode = context.mode
        prev_active_object = context.active_object
        prev_selected_objects = context.selected_objects

        with context.temp_override(
            screen = override['screen'],
            window = context.window_manager.windows[0], 
            area = override['area'], 
            region = override['region']
            ):

            print("honk")

            if prev_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  

            # Figure out if an object already exists, if yes do nothing
            for object in bpy.data.objects:
                #print(object)
                if object.name == addon_prefs.default_datablock:
                    self.report({'WARNING'}, "Capsule data for the blend file has been found, a new one will not be created.")
                    return {'CANCELLED'}

            # Otherwise create the object using the addon preference data
            bpy.ops.object.select_all(action ='DESELECT')
            bpy.ops.object.empty_add(type = 'CIRCLE') # apparently using plain axes causes a crash.

            defaultDatablock = bpy.context.view_layer.objects.active
            defaultDatablock.name = addon_prefs.default_datablock
            defaultDatablock.hide_viewport = True
            defaultDatablock.hide_render = True
            defaultDatablock.hide_select = True
            defaultDatablock.CAPFile.is_storage_object = True
            addon_prefs.data_missing = False

            context.view_layer.objects.active = prev_active_object
            for obj in prev_selected_objects:
                obj.select_set(state=True)

            # # Restore the context
            if prev_mode != 'OBJECT':

                # We need this because the context returns separate definitions.
                if prev_mode.find('EDIT') != -1:
                    prev_mode = 'EDIT'
                
                bpy.ops.object.mode_set(mode=prev_mode, toggle=False)

        self.report({'INFO'}, "Capsule data created.")
        return {'FINISHED'}


class CAPSULE_OT_Add_Stored_Presets(Operator):
    """Add the currently selected saved preset into the Active Export Presets list, enabling it's use for exports in this .blend file."""
    bl_idname = "cap.create_current_preset"
    bl_label = "Default Presets"

    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile

        if len(addon_prefs.saved_export_presets) > 0:
            return True

        else:
            return False

    def execute(self, context):

        # Get the current export data
        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile

        # Obtain the selected preset
        new_preset = cap_file.export_presets.add()
        export_presets.CopyPreset(addon_prefs.saved_export_presets[addon_prefs.saved_export_presets_index], new_preset)

        return {'FINISHED'}

class CAPSULE_OT_Delete_Presets(Operator):
    """Delete the currently selected saved preset."""
    bl_idname = "cap.delete_global_preset"
    bl_label = "Store Preset"

    # Removed Default Export Presets in 1.33, any preset can now be deleted.
    # @classmethod
    # def poll(cls, context):
    #     preferences = context.preferences
    #     addon_prefs = preferences.addons[__package__].preferences

    #     if len(addon_prefs.saved_export_presets) > 0:
    #         export = addon_prefs.saved_export_presets[addon_prefs.saved_export_presets_index]
            
    #         if export.x_global_user_deletable is True:
    #             return True

    #     return False

    def execute(self, context):

        # Get the current export data
        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile

        # Obtain the selected preset
        addon_prefs.saved_export_presets.remove(addon_prefs.saved_export_presets_index)

        # Decrement the list selection
        if addon_prefs.saved_export_presets_index > 0:
            addon_prefs.saved_export_presets_index -= 1

        return {'FINISHED'}

class CAPSULE_OT_Store_Presets(Operator):
    """Store the currently selected export preset as a saved preset, to enable it's use in across .blend files."""
    bl_idname = "cap.add_global_preset"
    bl_label = "Store Preset"

    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile

        if len(cap_file.export_presets) > 0:
            return True

        else:
            return False


    def execute(self, context):

        # Get the current export data
        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile

        # Obtain the selected preset
        new_preset = addon_prefs.saved_export_presets.add()
        export_presets.CopyPreset(cap_file.export_presets[cap_file.export_presets_listindex], new_preset)

        return {'FINISHED'}

class CAPSULE_OT_Show_Preferences(Operator):
    """Opens a window to the Capsule Addon Preferences menu"""
    bl_idname = "scene.cap_show_preferences"
    bl_label = "Show Addon Preferences"

    def execute(self, context):

        # Get the current export data
        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile

        bpy.ops.screen.userpref_show()
        context.preferences.active_section = 'ADDONS'
        bpy.data.window_managers["WinMan"].addon_search = "Capsule"


        return {'FINISHED'}

class CAPSULE_OT_Tutorial_StoredPresets(Operator):
    """Opens a message describing how Stored Export Presets work"""
    bl_idname = "scene.cap_tut_storedpresets"
    bl_label = ""

    def execute(self, context):

        def tutorial_layout(self, context):
            self.layout.label(text = "Stored Export Presets are export settings you want to use to store")
            self.layout.label(text = "and use in different .blend files.")
            self.layout.label(text = "If Auto-Save Preferences is enabled the presets you store will be")
            self.layout.label(text = "saved when you close the Blender Preferences window.")

        # Get the current export data
        bpy.context.window_manager.popup_menu(tutorial_layout, title="Stored Export Presets", icon='HELP')


        return {'FINISHED'}

class CAPSULE_OT_Tutorial_ActivePresets(Operator):
    """Opens a message describing how Active Export Presets work"""
    bl_idname = "scene.cap_tut_activepresets"
    bl_label = ""

    def execute(self, context):

        def tutorial_layout(self, context):
            self.layout.label(text = "Active Export Presets are export settings that can be assigned to")
            self.layout.label(text = "different Objects and Collections in the current Blend file.")
            self.layout.label(text = "They are saved with your .blend file in a special hidden object.")
            self.layout.label(text = "(The object is called '>Capsule Blend File Data<', don't delete it!).")

        # Get the current export data
        bpy.context.window_manager.popup_menu(tutorial_layout, title="Active Export Presets", icon='HELP')


        return {'FINISHED'}


class CAPSULE_OT_TestPackScript(Operator):
    """Executes a Pack Script for the active Object or Collection and places all collected export targets into a new collection called, "Capsule Pack Test".  NOTE - This can only be used on one Object or Collection at a time"""
    bl_idname = "cap.test_pack_script_selection"
    bl_label = "Test Pack Script"

    # Defines the method that a target should be tested by.  UI elements should
    # be using this depending on the context.

    set_mode: EnumProperty(
        name = "Export Mode",
        items = [
            ('ACTIVE_OBJECT', "Selected", "Export the currently active object"),
            ('ACTIVE_COLLECTION', "Selected Collections", "Exports only selected collection"),
            ],
        default = 'ACTIVE_OBJECT',
        description = "Execution mode", 
        options = {'HIDDEN'},
    )

    @classmethod
    def poll(cls, context):
        scn = context.scene.CAPScn
        select_tab = int(str(scn.selection_switch))

        if select_tab == 1:
            if len(context.selected_objects) > 1:
                return False

        else:
            if len(search_utils.GetSelectedCollections()) > 1:
                return False
        
        return True



    def execute(self, context):
        
        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences
        cap_scn = context.scene.CAPScn
        cap_file = None

        target_object = None
        target_collection = None

        # ////////////////////////////////////////////
        # IDENTIFY TEST CANDIDATE

        # this is for the object tab of the 3D view menu
        if self.set_mode == 'ACTIVE_OBJECT':
            target_object = context.active_object
        
        # this is for the collections tab of the 3D view menu
        elif self.set_mode == 'ACTIVE_COLLECTION':
            target_collection = search_utils.GetActiveCollection()
        
        # this is for the list menu
        elif self.set_mode == 'ACTIVE_LIST':
            list_tab = int(str(cap_scn.list_switch))

            if list_tab == 1:
                index = cap_scn.object_list_index
                target_object = cap_scn.object_list[index].object

            elif list_tab == 2:
                index = cap_scn.collection_list_index
                target_collection = cap_scn.collection_list[index].collection


        # ////////////////////////////////////////////
        # SETUP PACK SCRIPT ENVIRONMENT
        # TODO : Ensure object + collection gathering code in export_operators can be used here.
        bpy.ops.scene.new(type = 'NEW')
        test_scene = context.scene
        test_scene.name = ">Capsule Test Scene<"

        # ////////////////////////////////////////////
        # EXECUTE + ADD TO COLLECTION


        # ////////////////////////////////////////////
        # TIDY PACK SCRIPT ENVIRONMENT





        return {'FINISHED'}

