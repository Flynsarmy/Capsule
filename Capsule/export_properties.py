
import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, PointerProperty, CollectionProperty, EnumProperty
from bpy.types import AddonPreferences, PropertyGroup
from .export_formats import CAP_ExportFormat, CAP_FormatData_FBX, CAP_FormatData_OBJ, CAP_FormatData_GLTF

def CAP_Update_TagName(self, context):

    user_preferences = context.user_preferences
    addon_prefs = user_preferences.addons[__package__].preferences

    if addon_prefs.plugin_is_ready is True:
        exp = bpy.data.objects[addon_prefs.default_datablock].CAPExp
        currentTag = exp.tags[exp.tags_index]
        tag_name = currentTag.name

        # Get tags in all current passes, and edit them
        for expPass in export.passes:
            passTag = expPass.tags[export.tags_index]
            passTag.name = tag_name

    return None


def DrawAnimationWarning(self, context):
        layout = self.layout
        layout.label("Hey!  The animation feature is currently experimental, and may result in")
        layout.label("objects being repositioned after exporting, and in the FBX file.")
        layout.separator()
        layout.label("The animation features should work fine if you're exporting armature animations,")
        layout.label("any other kinds of object animations are unlikely to export correctly, and if")
        layout.label("attempted, you may find your scene translated slightly.  If this happens though,")
        layout.label("simply use the undo tool.")
        layout.separator()
        layout.label("Hopefully i'll have this fully functional in the next version :)")


def CAP_Update_AnimationWarning(self, context):
    if self.export_animation_prev is False and self.export_animation is True:
        bpy.context.window_manager.popup_menu(DrawAnimationWarning, title="Animation Warning", icon='INFO')
    self.export_animation_prev = self.export_animation

class CAP_ExportTag(PropertyGroup):
    # The main Export Tag collection property, used for storing the actual tags used in an Export Preset

    name = StringProperty(
        name="Tag Name",
        description="The name of the tag.",
        update=CAP_Update_TagName
        )

    name_filter = StringProperty(
        name="Tag",
        description="The text you wish to use as a filter, when sorting through object names."
        )

    name_filter_type = EnumProperty(
        name="Tag Type",
        description="Where the name filter is being looked for.",
        items=(
        ('1', 'Suffix', ''),
        ('2', 'Prefix', ''),),
        )

    object_type = EnumProperty(
        name="Object Type",
        items=(
            ('1', 'All', 'Applies to all object types.'),
            ('2', 'Mesh', 'Applies to mesh object types only.'),
            ('3', 'Curve', 'Applies to curve object types only.'),
            ('4', 'Surface', 'Applies to surface object types only.'),
            ('5', 'Metaball', 'Applies to metaball object types only.'),
            ('6', 'Font', 'Applies to font object types only.'),
            ('7', 'Armature', 'Applies to armature object types only.'),
            ('8', 'Lattice', 'Applies to lattice object types only.'),
            ('9', 'Empty', 'Applies to empty object types only.'),
            ('10', 'Camera', 'Applies to camera object types only.'),
            ('11', 'Lamp', 'Applies to lamp object types only.'),
            ('12', 'Speaker', 'Applies to speaker object types only.')
            ),
        default='1'
        )

    # Special preferences for special export presets.
    x_user_deletable = BoolProperty(default=True)
    x_user_editable_type = BoolProperty(default=True)


class CAP_ExportPassTag(PropertyGroup):
    # The Export Tag reference, used inside Export Passes to list the available tags.
    # Also specified for that pass, whether or not it is to be used.

    name = StringProperty(
        name="Tag Name",
        description="The name of the tag.",
        default=""
        )
    prev_name = StringProperty(
        name="Previous Tag Name",
        description="A backup tag name designed to prevent editing of tag names when viewing them. (Internal Only)",
        default=""
        )
    index = IntProperty(
        name="Tag Index",
        description="Where the tag is located in the Export Preset, so it can be looked up later (Internal Only)",
        default=0
        )
    use_tag = BoolProperty(
        name="",
        description="Determines whether or not the tag gets used in the pass.",
        default=False
        )

class CAP_ExportPass(PropertyGroup):
    # Used to define properties for a single export pass.

    name = StringProperty(
        name="Pass Name",
        description="The name of the selected pass."
        )

    enable = BoolProperty(
        name="Enable Pass",
        description="Lets you enable or disable the pass for use when exporting objects.",
        default=True
    )

    file_suffix = StringProperty(
        name="File Suffix",
        description="An optional string that if used, will be appended to all the names of files produced through this pass."
        )
    sub_directory = StringProperty(
        name="Sub-Directory",
        description="If enabled, a folder will be created inside the currently defined file path (and any other defined folders for the File Preset), where all exports from this pass will be placed into."
        )

    tags = CollectionProperty(type=CAP_ExportPassTag)
    tags_index = IntProperty(default=0)

    export_individual = BoolProperty(
        name="Export Individual",
        description="If enabled, the pass will export every individual object available in the pass into individual files, rather than a single file.",
        default=False
        )

    export_animation = BoolProperty(
        name="Export Animation",
        description="(EXPERIMENTAL) If ticked, animations found in objects or groups in this pass, will be exported.",
        default=False,
        update=CAP_Update_AnimationWarning
        )
    export_animation_prev = BoolProperty(default=False)

    apply_modifiers = BoolProperty(
        name="Apply Modifiers",
        description="If enabled, all modifiers on every object in the pass will be applied.",
        default=False
        )

    triangulate = BoolProperty(
        name="Triangulate Export",
        description="If enabled, all objects in the pass will be triangulated automatically using optimal triangulation settings, unless a Triangulation modifier is already present.",
        default=False
        )

    use_tags_on_objects = BoolProperty(
        name="Use Tags for Objects",
        description="If enabled, active tag filters will also apply to any single-object exports in this pass, as well as those in the scene that share the same name - which will also be exported with it.",
        default=False
        )

class CAP_ExportPreset(PropertyGroup):
    # Used to define properties for a single export preset.
    # Export presets include Capsule-specific features as well as .FBX exporter features
    # and any defined Passes and Tags.

    name = StringProperty(
        name = "Preset Name",
        description="The name of the export preset.",
        default=""
        )

    instance_id = IntProperty(
        name = "Instance ID",
        description="INTERNAL ONLY - Unique ID used to pair with format data, that holds the full export settings for the chosen file type."
        )

    description = StringProperty(
        name = "Description",
        description="(Internal Use Only) TBA",
        default=""
        )

    use_blend_directory = BoolProperty(
        name="Add Blend File Directory",
        description="If enabled, a folder will be created inside the currently defined file path, where all exports from this blend file will be placed into.  Useful for exporting multiple .blend file contents to the same destination.",
        default=False
        )

    use_sub_directory = BoolProperty(
        name="Add Object Directory",
        description="If enabled, a folder will be created inside the currently defined file path (and inside the Blend Folder if enabled), for every object or group created, where it's export results will be placed into.  Useful for complex object or group exports, with multiple passes.",
        default=False
        )

    filter_render = BoolProperty(
        name="Filter by Rendering",
        description="Will use the Hide Render option on objects (viewable in the Outliner) to filter whether or not an object can be exported.  If the object is hidden from the render, it will not export regardless of any other settings in this plugin."
        )


    passes = CollectionProperty(type=CAP_ExportPass)
    passes_index = IntProperty(default=0)
    tags = CollectionProperty(type=CAP_ExportTag)
    tags_index = IntProperty(default=0)

    format_type = EnumProperty(
        name="Format Type",
        items=
            (
            ('FBX', "FBX", "Export assets in an .fbx format."),
            ('OBJ', "OBJ", "Export assets in an .obj format."),
            ('GLTF', "GLTF", "Export assets in a .gltf format."),
            ),
        description="Defines what file type objects with this preset will export to and the export options available for this preset.",
        )

    # the data stored for FBX presets.
    data_fbx = PointerProperty(type=CAP_FormatData_FBX)

    # the data stored for OBJ presets.
    data_obj = PointerProperty(type=CAP_FormatData_OBJ)

    # the data stored for GLTF presets.
    data_gltf = PointerProperty(type=CAP_FormatData_GLTF)

    # A special system variable that defines whether it can be deleted from the Global Presets list.
    x_global_user_deletable = BoolProperty(default=True)


class CAP_LocationDefault(PropertyGroup):
    # Defines a single location default, assigned to specific objects to define where they should be exported to.

    name = StringProperty(
        name="",
        description="The name of the file path default."
        )

    path = StringProperty(name="",
        description="The file path to export the object to.",
        default="",
        subtype="FILE_PATH"
        )


class CAP_ExportPresets(PropertyGroup):
    """
    A property group passed onto the "default datablock", the empty object created in a blend file to store all the available export presets.
    """

    # the available file presets
    file_presets = CollectionProperty(type=CAP_ExportPreset)

    # the preset selected on the list panel, when viewed from the AddonPreferences window.
    file_presets_listindex = IntProperty(default=0)

    # if true, this object is the empty created for the purposes of storing preset data.
    is_storage_object = BoolProperty(default=False)

    # the available location presets created by the user
    location_presets = CollectionProperty(type=CAP_LocationDefault)

    # the location selected on the Locations panel, inside the 3D view
    location_presets_listindex = IntProperty(default=0)

    fbx_menu_options = EnumProperty(
        name="Export Options",
        description="",
        items=(
        ('Export', 'Export', 'A tab containing additional export paramaters exclusive to Capsule.'),
        ('Transform', 'Transform', 'A tab containing options to how objects are scaled and orientated in the export.'),
        ('Geometry', 'Geometry', 'A tab containing options for how object geometry is interpreted in the export.'),
        ('Armature', 'Armature', 'A tab containing options for how armature objects are interpreted in the export.'),
        ('Animation', 'Animation', 'A tab containing options for how animations are interpreted and used in the export.')
        ),)

    obj_menu_options = EnumProperty(
        name="Export Options",
        description="",
        items=(
        ('Export', 'Export', 'A tab containing general export paramaters.'),
        ('Transform', 'Transform', 'A tab containing options to how objects are scaled and orientated in the export.'),
        ('Object', 'Geometry', 'A tab containing options for how object geometry, materials and other associated assets are exported.'),
        ),
    )

    gltf_menu_options = EnumProperty(
        name="Export Options",
        description="",
        items=(
        ('Export', 'Export', 'A tab containing general export paramaters.'),
        ('Transform', 'Transform', 'A tab containing options to how objects are scaled and orientated in the export.'),
        ('Object', 'Object', 'A tab containing options for how object geometry is interpreted in the export.'),
        #('Extensions', 'Extensions', 'A tab containing options for how armature objects are interpreted in the export.'),
        ),
        )