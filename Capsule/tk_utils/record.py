# ///////////////////////////////////////////////////////////////////
# Records and restores contexts and checks for errors.
# ///////////////////////////////////////////////////////////////////

import bpy

from mathutils import Vector
from . import collections as collection_utils
from . import select as select_utils
from . import locations as loc_utils
from . import paths as path_utils

from . import object_ops, object_transform


def SaveSceneContext(context):
    """
    Records all selection, edit mode, object constraint and view layer properties and saves it for later.
    """

    #print("NEW SETUP SCENE PROCESS")

    scene_records = {}

    # If the current context isn't the 3D View, we need to change that before anything else.
    # TODO: This is busted, doesn't account for maximized areas.
    scene_records['active_area_type'] = bpy.context.area.type

    for area in context.screen.areas:
        if area != context.area:
            scene_records['region_override'] = area.regions[0]
            #print("got a region override - ", scene_records['region_override'])
            break

    context.area.type = 'VIEW_3D'
    

    # We also need to store current 3D View selections.
    selected_record = []
    if context.active_object is not None:
        for sel in context.selected_objects:
            if sel.name != context.active_object.name:
                selected_record.append(sel)
    else:
        for sel in context.selected_objects:
            selected_record.append(sel)

    scene_records['active_object'] = context.active_object
    scene_records['selected_objects'] = selected_record

    # Save the current cursor location
    cursor_loc = bpy.data.scenes[bpy.context.scene.name].cursor.location
    scene_records['cursor_location'] = [cursor_loc[0], cursor_loc[1], cursor_loc[2]]

    # Keep a record of the current object mode 
    scene_records['view_mode'] = bpy.context.mode
    bpy.ops.object.mode_set(mode= 'OBJECT')


    # ======================
    # Setup a new view layer

    # I dont actually need this, might be useful later
    # scene_records['current_view_layer'] = bpy.context.view_layer.name

    bpy.ops.scene.view_layer_add()
    bpy.context.view_layer.name = ">> Capsule <<"
    scene_records['capsule_view_layer'] = ">> Capsule <<"


    # ======================
    # Preserve all scene object information
    
    object_records = []

    for item in context.scene.objects:
        record = {}
        record['item'] = item
        record['item_name'] = item.name

        # Record object visibility
        # FIXME : hide_viewport is a global property, and isn't the same as Outliner/3D View hides.  Need to get and set that data when fixed.
        # https://devtalk.blender.org/t/view-layer-api-access-wishlist-collection-expand-set/5517
        record['is_hidden'] = item.hide_viewport
        record['is_selectable'] = item.hide_select
        #print('Hide records = ', record['is_hidden'], ' ', record['is_selectable'])

        item.hide_select = False


        # Record object loc/rot/scale locks if applicable
        transform_locks = []
        for i, x in enumerate(item.lock_location):
            transform_locks.append(item.lock_location[i])
        for i, x in enumerate(item.lock_rotation):
            transform_locks.append(item.lock_rotation[i])
        for i, x in enumerate(item.lock_scale):
            transform_locks.append(item.lock_scale[i])
        
        if True in transform_locks:
            record['transform_locks'] = transform_locks
        
        item.lock_location = (False, False, False)
        item.lock_rotation = (False, False, False)
        item.lock_scale = (False, False, False)


            # If any armatures are in any non-object modes, we need to change this
        #print("Searching for armatures...")
        if item.type == 'ARMATURE':
            mode = object_ops.SwitchObjectMode('OBJECT', item)
            
            if mode != None:
                record['armature_mode'] = mode


        # Add constraint records if the object has any.
        if len(item.constraints) > 0:

            constraint_list = []

            # Record the current object location for later
            true_location = loc_utils.FindWorldSpaceObjectLocation(context, item)

            # Placeholder for later, once all constraints are isolated and muted.
            constraint_location = Vector((0.0, 0.0, 0.0))

            #print("true_location", true_location)
            #print("true_location", true_location)
            record['true_location'] = true_location
            record['constraint_location'] = constraint_location

            # Iterate through and save constraint settings
            i = 0
            for constraint in item.constraints:
                constraint_list.append( {'index': i, 'enabled': constraint.mute, 'influence': constraint.influence} )
                i += 1
            
            record['constraint_list'] = constraint_list

            # Mute and isolate them
            for entry in constraint_list:
                constraint = item.constraints[entry['index']]

                # Mute the constraint
                constraint.mute = True
                constraint.influence = 0.0

        # Add the new record
        object_records.append(record)
    
    
    # Now the records have been created, we can alter constraint and object positions.
    for record in object_records:
        if 'constraint_list' in record:
            item = record['item']
            record['constraint_location'] = loc_utils.FindWorldSpaceObjectLocation(context, item)
            
            #print("NEW CONSTRAINT LOCATION", item.name, record['constraint_location'])

            #print("Moving Object...", item.name, record['true_location'])
            object_transform.MoveObjectFailsafe(item, context, record['true_location'], scene_records['region_override'])
            #print("New Object Location = ", item.location)
            #print("New Object Location = ", item.location)

    # Now we can unhide and deselect everything
    bpy.ops.object.hide_view_clear()
    bpy.ops.object.select_all(action= 'DESELECT')

    records = {}
    records['scene'] = scene_records
    records['object'] = object_records
    return records


def RestoreSceneContext(context, record):
    """
    Restores all selection, edit mode, object constraint and view layer properties from a previously saved scene context.
    """

    scene_records = record['scene']
    object_records = record['object']

    for record in object_records:
        item = record['item']
        
            # Restore constraint object positions
        if 'constraint_list' in record:
            #print(record)
            #print(record)
            object_transform.MoveObjectFailsafe(item, context, record['constraint_location'], scene_records['region_override'])
            #print("New Object Location = ", item.name, item.location)

            # Restore Constraint Defaults
            for constraint_record in record['constraint_list']:
                index = constraint_record['index']
                item.constraints[index].mute = constraint_record['enabled']
                item.constraints[index].influence = constraint_record['influence']
        
        # Restore visibility defaults
        #print('Hide records = ', record['is_hidden'], ' ', record['is_selectable'])
        item.hide_set(record['is_hidden'])
        item.hide_select = record['is_selectable']

        # Restore transform locks
        if 'transform_locks' in record:
            lock_list = record['transform_locks']

            item.lock_location[0] = lock_list[0]
            item.lock_location[1] = lock_list[1]
            item.lock_location[2] = lock_list[2]
            item.lock_rotation[0] = lock_list[3]
            item.lock_rotation[1] = lock_list[4]
            item.lock_rotation[2] = lock_list[5]
            item.lock_scale[0] = lock_list[6]
            item.lock_scale[1] = lock_list[7]
            item.lock_scale[2] = lock_list[8]
        
        # Restore armature mode
        if 'armature_mode' in record:
            mode = object_ops.SwitchObjectMode(record['armature_mode'], item)


    # ======================
    # Delete the created view layer.
    # ======================
    bpy.ops.scene.view_layer_remove()

    # Re-select the objects previously selected
    if scene_records['active_object'] is not None:
        select_utils.FocusObject(scene_records['active_object'])

    for sel in scene_records['selected_objects']:
        select_utils.SelectObject(sel)

    if scene_records['active_object'] is None and len(scene_records['selected_objects']) == 0:
        bpy.ops.object.select_all(action= 'DESELECT')

    # Restore the 3D view mode
    bpy.ops.object.mode_set(mode = scene_records['view_mode'])

    # Restore the 3D cursor
    bpy.data.scenes[bpy.context.scene.name].cursor.location = scene_records['cursor_location']

    # Restore the panel type
    # FIXME : This currently doesn't work with the Blender 2.8 area bug.
    context.area.type = scene_records['active_area_type']

    #print("Rawr")


# FIXME : Check if needed and/or is working.
def MuteArmatureConstraints(context):
    """
    Performs two operations together:
    - Records all armatures and preserves their constraints.
    - Mutes them afterwards to prevent interference in the Capsule export.
    """

    # # This process may fail, so if the user doesn't want us to process the armature constraints then stop right here.
    # if self.export_preset.preserve_armature_constraints is True:
    #     return

    # We need to do similar constraint evaluation for armatures
    # Find translate constraints. mute them and move the affected bones
    # to make the plugin movement successful.
    record = {}
    record['armature_constraints'] = []
    record['armature_objects'] = []

    for item in context.scene.objects:
        if item.type == 'ARMATURE':
            for bone in item.pose.bones:
                i = 0
                for constraint in bone.constraints:
                    if item not in record['armature_objects']:
                        trueLocation = loc_utils.FindWorldSpaceBoneLocation(item, context, bone)
                        constraintLocation = Vector((bone.location[0], bone.location[1], bone.location[2]))

                        entry = {'object_name': item.name, 'bone_name': bone.name, 'true_location': trueLocation, 'constraint_location': constraintLocation}
                        record['armature_objects'].append(entry)

                    entry = {'object_name': item.name, 'bone_name': bone.name, 'index': i, 'enabled': constraint.mute, 'influence': constraint.influence}
                    record['armature_constraints'].append(entry)

                    i += 1

    #print("-"*40)
    #print("-"*40)

    # NOW WE CAN FUCKING MUTE THEM
    for entry in record['armature_constraints']:
        item = context.scene.objects[entry['object_name']]
        for bone in item.pose.bones:
            if bone.name == entry['bone_name']:
                constraint = bone.constraints[entry['index']]

                # Mute the constraint
                constraint.mute = True
                constraint.influence = 0.0

    #print("-"*40)
    #print("-"*40)

    # Reset the constraint location now we have a 'true' location
    for entry in record['armature_objects']:
        item = context.scene.objects[entry['object_name']]
        for bone in item.pose.bones:
            if bone.name == entry['bone_name']:
                entry['constraint_location'] = loc_utils.FindWorldSpaceBoneLocation(item, context, bone)
                #print("NEW CONSTRAINT LOCATION", item.name, bone.name, entry['constraint_location'])

    #print("-"*40)
    #print("-"*40)

    # Now all problematic constraints have been turned off, we can safely move
    # objects to their initial positions
    for entry in record['armature_objects']:
        item = context.scene.objects[entry['object_name']]
        for bone in item.pose.bones:
            if bone.name == entry['bone_name']:
                #print("Moving Bone...", item.name, bone.name, entry['true_location'])
                object_transform.MoveBone(item, bone, context, entry['true_location'])
                #print("New Bone Location = ", bone.location)

    #print("-"*40)
    #print("-"*40)

    return record

# FIXME : Check if needed and/or is working.
def RestoreArmatureConstraints(context, record):
    """
    Restores any armature constraint changes that were made to prepare the scene for export.
    """

    # if self.export_preset.preserve_armature_constraints is True:
    #     return

    # Restore constraint object positions
    for entry in record['armature_objects']:
        item = context.scene.objects[entry['object_name']]
        for bone in item.pose.bones:
            if bone.name == entry['bone_name']:
                #print("Moving Bone...", item.name, bone.name)
                object_transform.MoveBone(item, bone, context, entry['constraint_location'])
                #print("New Bone Location = ", bone.location)

    # Restore Constraint Defaults
    for entry in record['armature_constraints']:
        item = bpy.data.objects[entry['object_name']]
        for bone in item.pose.bones:
            if bone.name == entry['bone_name']:
                index = entry['index']
                bone.constraints[index].mute = entry['enabled']
                bone.constraints[index].influence = entry['influence']



def CheckCapsuleErrors(context, target_objects, target_collections):
    # Ensures that the scene is setup with correct settings, before proceeding
    # with the export.

    preferences = context.preferences
    addon_prefs = preferences.addons['Capsule'].preferences
    cap_file = bpy.data.objects[addon_prefs.default_datablock].CAPFile
    
    # TODO: Collect all errors for all objects and select them all at the end
    # in order to make it easier for people to correct common mistakes.

    # TODO: Find a better way to handle invalid enumerations.
    
    # TODO: Export Selected doesn't have any impact on this, we should only check
    # items that are in the export.

    # Check all active file presets for valid directory names
    # These lists will be analysed later
    sub_directory_check = []
    statement = None

    if target_objects == None:
        target_objects = context.scene.objects
    if target_collections == None:
        target_collections = collection_utils.GetSceneCollections(context.scene, True)
    
    # The errors that will be reported back.
    error_objects = {}
    error_objects['no_export'] = []
    error_objects['no_location'] = []

    # ////////////////////////////////////////////////
    # OBJECTS
    

    # Checks for any easily-preventable errors
    for item in target_objects:
        if item.CAPObj.enable_export is True:
            cap_obj = item.CAPObj
            
            # Check for Valid Presets
            # EnumProperty types are ints when valid and empty strings when invalid
            if cap_obj.export_preset == '':
                error_objects['no_export'].append(item)
                continue
            
            if cap_obj.location_preset == '':
                error_objects['no_location'].append(item)
                continue
            
            cap_export_enum = int(cap_obj.export_preset)
            cap_location_enum = int(cap_obj.location_preset)
            exports_len = len(cap_file.export_presets)
            locations_len = len(cap_file.location_presets)

            # Check Export Key
            if cap_export_enum == 0 or cap_export_enum > exports_len:
                error_objects['no_export'].append(item)

            # Check Location Preset
            if cap_location_enum == 0 or cap_location_enum > locations_len:
                error_objects['no_location'].append(item)


    # Total up any errors found.
    max_error_value = 0
    max_error = ''
    target_objects = []
    for k, v in error_objects.items():
        if (len(v) > max_error_value):
            max_error_value = len(v)
            max_error = k
            target_objects = v
    

    # If any were found, report the biggest issue and select the objects that had it.
    if max_error_value > 0:
        if max_error == 'no_export':
            statement = "The selected object(s) require a Export Preset to be defined - check the Export Lists to see all missing properties."

        elif max_error == 'no_location':
            statement = "The selected object(s) require a Location Preset to be defined - check the Export Lists to see all missing properties."
        
        bpy.ops.object.select_all(action= 'DESELECT')

        for item in target_objects:
            select_utils.SelectObject(item)
        
        return statement


    # ////////////////////////////////////////////////
    # COLLECTIONS

    # TODO: The Collection should be selected, not the objects!

    error_collections = {}
    error_collections['no_export'] = []
    error_collections['no_location'] = []
    error_collections['no_root'] = []


    # Check all scene collections for potential errors
    for collection in target_collections:
        if collection.CAPCol.enable_export is True:
            cap_col = collection.CAPCol

            # Check Origin Point
            if cap_col.origin_point == 'Object':
                if cap_col.root_object is None:
                    error_collections['no_root'].append(collection)

            # Check for Valid Presets
            # EnumProperty types are ints when valid and empty strings when invalid
            if cap_col.export_preset == '':
                error_collections['no_export'].append(collection)
                continue
            
            if cap_col.location_preset == '':
                error_collections['no_location'].append(collection)
                continue


            cap_export_enum = int(cap_col.export_preset)
            cap_location_enum = int(cap_col.location_preset)
            exports_len = len(cap_file.export_presets)
            locations_len = len(cap_file.location_presets)
            

            # Check Export Key
            if cap_export_enum == 0 or cap_export_enum > exports_len:
                error_collections['no_export'].append(collection)

            # Check Export Location
            if cap_location_enum <= 0 or cap_location_enum > locations_len:
                error_collections['no_location'].append(collection)


    # Total up any errors found.
    max_error_value = 0
    max_error = ''
    target_collections = []
    for k, v in error_collections.items():
        if (len(v) > max_error_value):
            max_error_value = len(v)
            max_error = k
            target_objects = v
    

    # If any were found, report the biggest issue and select the objects that had it.
    if max_error_value > 0:
        if max_error == 'no_root':
            statement = " % s collection(s) require a Root Object to be defined - check the Export Lists to see all missing properties." % (max_error_value)

        elif max_error == 'no_export':
            statement = "% s collection(s) require an Export Preset to be defined - check the Export Lists to see all missing properties." % (max_error_value)

        elif max_error == 'no_location':
            statement = "% s collection(s) require a Location Preset to be defined - check the Export Lists to see all missing properties." % (max_error_value)
        
        return statement
    

    # ////////////////////////////////////////////////
    # PATHS AND DIRECTORIES

    # Check all Location Presets to ensure the chatacters contained are valid.
    i = 0
    while i < len(cap_file.location_presets):
        enumIndex = i
        enumIndex -= 1

        defaultFilePath = cap_file.location_presets[enumIndex].path
        #print("Checking File Paths...", defaultFilePath)

        if defaultFilePath == "":
            statement = "The File Location '" + cap_file.location_presets[enumIndex].name + "' has no file path.  Please set one before attempting to export."
            return statement
        
        # TODO: Ensure this would properly validate a directory
        if defaultFilePath[-1] != '\\':
            statement = "The File Location '" + cap_file.location_presets[enumIndex].name + "' points to a file rather than a directory.  Please ensure it points to a folder."
            return statement


        i += 1
    
    # # Check all collected sub-directory names for invalid characters if we can't replace them.
    if addon_prefs.substitute_directories is False:
        for name in sub_directory_check:
            #print("Checking Directory...", name)
            result = path_utils.CheckSystemChar(context, name[1])
            returnStatement = ""

            if len(result) != 0:
                characterlead = ", is using the invalid file character "
                end = ".  Please remove the invalid character from the path name."

                if len(result) > 1:
                    characterlead = ", is using the invalid file characters "
                    end = ".  Please remove the invalid characters from the path name."

                while len(result) != 0:
                    text = result.pop()
                    returnStatement += text + " "

                statement = "The" + name[0] + " " + name[1] + ", belonging to the export, " + name[3] + characterlead + returnStatement + end
                return statement


    return None