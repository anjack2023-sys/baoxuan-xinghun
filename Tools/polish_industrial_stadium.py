"""Batch-only art pass: save the preview, capture PIE, then close this editor instance."""
import hashlib
import json
import math
import time
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT=ROOT/'screenshots/stadium-polish-v1'
OUT.mkdir(parents=True,exist_ok=True)
ASSETS='/Game/ArtPreview/IndustrialPolish_v1'
MAP='/Game/Maps/StadiumIndustrialPolish_v1'
LEVELS=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
MEL=unreal.MaterialEditingLibrary
MAIN_HASH=hashlib.sha256((ROOT/'Content/Maps/Main.umap').read_bytes()).hexdigest()


def material(name,color,roughness=.8,metal=.05):
    mat=unreal.load_asset(ASSETS+'/'+name) or TOOLS.create_asset(name,ASSETS,unreal.Material,unreal.MaterialFactoryNew())
    assert mat,name
    MEL.delete_all_material_expressions(mat)
    base=MEL.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector)
    base.constant=unreal.LinearColor(*color,1)
    MEL.connect_material_property(base,'',unreal.MaterialProperty.MP_BASE_COLOR)
    for prop,value in [(unreal.MaterialProperty.MP_ROUGHNESS,roughness),(unreal.MaterialProperty.MP_METALLIC,metal),
                       (unreal.MaterialProperty.MP_SPECULAR,.22)]:
        node=MEL.create_material_expression(mat,unreal.MaterialExpressionConstant)
        node.r=value;MEL.connect_material_property(node,'',prop)
    MEL.recompile_material(mat)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def box(name,location,size,mat):
    actor=ACTORS.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*location))
    actor.set_actor_label(name)
    comp=actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    comp.set_material(0,mat)
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.set_actor_scale3d(unreal.Vector(*(v/100 for v in size)))
    return actor


def rect(name,location,target,color,intensity,width,height):
    actor=ACTORS.spawn_actor_from_class(unreal.RectLight,unreal.Vector(*location))
    actor.set_actor_label(name)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*location),unreal.Vector(*target)),False)
    comp=actor.get_component_by_class(unreal.RectLightComponent)
    comp.set_editor_property('intensity_units',unreal.LightUnits.LUMENS)
    comp.set_intensity(intensity)
    comp.set_light_color(unreal.LinearColor(*color,1))
    comp.set_editor_property('source_width',width)
    comp.set_editor_property('source_height',height)
    comp.set_editor_property('attenuation_radius',2500)
    return actor


def build():
    by_label={a.get_actor_label():a for a in ACTORS.get_all_level_actors()}
    male=by_label['MaleLead']
    assert abs(male.get_actor_scale3d().x-2.165)<.001
    bowl=by_label['SmoothBowl_v1'].get_component_by_class(unreal.StaticMeshComponent)
    before_hit=bowl.line_trace_component(unreal.Vector(0,0,600),unreal.Vector(0,0,-200),True,False,False)
    assert before_hit and abs(before_hit[0].z-42)<.01,str(before_hit)

    navy=material('M_VenueNavy',(.025,.037,.055),.86,.12)
    steel=material('M_VenueSteel',(.065,.082,.105),.65,.35)
    floor=material('M_VenueFloor',(.047,.057,.069),.83,.12)
    seam=material('M_FloorSeam',(.012,.018,.026),.95,0)
    gold=material('M_MutedGold',(.28,.20,.095),.55,.55)

    ground=by_label['GroundFallback']
    # Keep the calibrated floor height and a broad landing area; only change its visual footprint.
    ground.set_actor_scale3d(unreal.Vector(40,20,.15))
    ground.set_actor_location(unreal.Vector(0,530,-7.5),False,True)
    ground.get_component_by_class(unreal.StaticMeshComponent).set_material(0,floor)
    for x in [-1600,-1000,-550,550,1000,1600]:
        box('FloorJoint_X_'+str(x),(x,530,.06),(1.4,2000,.12),seam)
    for y in [-400,600,1100]:
        box('FloorJoint_Y_'+str(y),(0,y,.06),(4000,1.4,.12),seam)

    # A low physical boundary hides the transition from the near floor to the distant art.
    box('RearVenueWall',(0,-505,45),(3600,55,90),navy)
    box('RearVenueCap',(0,-495,93),(3600,65,6),steel)
    for x in [-1600,-1200,-800,-400,0,400,800,1200,1600]:
        box('RearWallPost_'+str(x),(x,-474,47),(10,8,86),steel)
    box('RearGoldInlay',(0,-472,70),(3520,1,1.5),gold)
    for x in [-1575,1575]:
        box('SideBoundary_'+str(x),(x,230,45),(35,1400,90),navy)
        box('SideBoundaryCap_'+str(x),(x,230,93),(43,1400,5),steel)

    # Reuse the already-reviewed arena artwork as a distant camera-facing backdrop.
    task=unreal.AssetImportTask()
    task.filename=str(ROOT/'docs/P3-art-inbox/batch2/env_arena_v1.png')
    task.destination_path=ASSETS;task.destination_name='T_EnvArena'
    task.automated=True;task.save=True;task.replace_existing=False
    if not unreal.EditorAssetLibrary.does_asset_exist(ASSETS+'/T_EnvArena'):
        TOOLS.import_asset_tasks([task])
    tex=unreal.load_asset(ASSETS+'/T_EnvArena')
    assert tex,'Arena background import failed'
    backdrop=unreal.load_asset(ASSETS+'/M_ArenaBackdrop') or TOOLS.create_asset('M_ArenaBackdrop',ASSETS,unreal.Material,unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(backdrop)
    backdrop.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    backdrop.set_editor_property('two_sided',True)
    sample=MEL.create_material_expression(backdrop,unreal.MaterialExpressionTextureSample)
    sample.texture=tex
    uv=MEL.create_material_expression(backdrop,unreal.MaterialExpressionTextureCoordinate)
    flip=MEL.create_material_expression(backdrop,unreal.MaterialExpressionMultiply)
    flip_scale=MEL.create_material_expression(backdrop,unreal.MaterialExpressionConstant2Vector)
    flip_scale.r=1.;flip_scale.g=-1.
    offset=MEL.create_material_expression(backdrop,unreal.MaterialExpressionAdd)
    flip_bias=MEL.create_material_expression(backdrop,unreal.MaterialExpressionConstant2Vector)
    flip_bias.r=0.;flip_bias.g=1.
    MEL.connect_material_expressions(uv,'',flip,'A')
    MEL.connect_material_expressions(flip_scale,'',flip,'B')
    MEL.connect_material_expressions(flip,'',offset,'A')
    MEL.connect_material_expressions(flip_bias,'',offset,'B')
    assert MEL.connect_material_expressions(offset,'',sample,'UVs'),'Backdrop UV connection failed'
    multiply=MEL.create_material_expression(backdrop,unreal.MaterialExpressionMultiply)
    strength=MEL.create_material_expression(backdrop,unreal.MaterialExpressionConstant)
    strength.r=24.
    MEL.connect_material_expressions(strength,'',multiply,'B')
    MEL.connect_material_expressions(sample,'RGB',multiply,'A')
    MEL.connect_material_property(multiply,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(backdrop);assert unreal.EditorAssetLibrary.save_loaded_asset(backdrop)
    camera=by_label['BattleCamera']
    camera.set_actor_location(unreal.Vector(20,1150,650),False,True)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(-25,0,80)),False)
    rotation=camera.get_actor_rotation()
    forward=unreal.MathLibrary.get_forward_vector(rotation)
    right=unreal.MathLibrary.get_right_vector(rotation)
    up=unreal.MathLibrary.get_up_vector(rotation)
    distance=6000.
    plane=ACTORS.spawn_actor_from_class(unreal.StaticMeshActor,camera.get_actor_location()+forward*distance)
    plane.set_actor_label('ArenaDistantBackdrop')
    plane.set_actor_rotation(unreal.MathLibrary.make_rotation_from_axes(right,up,forward),False)
    pc=plane.get_component_by_class(unreal.StaticMeshComponent)
    pc.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Plane'))
    pc.set_material(0,backdrop);pc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    pc.set_cast_shadow(False)
    width=2*distance*math.tan(math.radians(camera.camera_component.field_of_view/2))*1.03
    plane.set_actor_scale3d(unreal.Vector(width/100,width/1.6/100,1))

    # Retain the original artwork; use a calmer coated-metal response under actual lights.
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    texture=next(a.get_asset() for a in registry.get_assets_by_path('/Game/ArtPreview/IndustrialGame_v1',recursive=True)
                 if str(a.asset_class_path.asset_name)=='Texture2D')
    surface=unreal.load_asset(ASSETS+'/M_IndustrialCoated') or TOOLS.create_asset('M_IndustrialCoated',ASSETS,unreal.Material,unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(surface)
    sample=MEL.create_material_expression(surface,unreal.MaterialExpressionTextureSample)
    sample.texture=texture
    MEL.connect_material_property(sample,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
    for prop,value in [(unreal.MaterialProperty.MP_ROUGHNESS,.62),(unreal.MaterialProperty.MP_METALLIC,.18),
                       (unreal.MaterialProperty.MP_SPECULAR,.25)]:
        node=MEL.create_material_expression(surface,unreal.MaterialExpressionConstant)
        node.r=value;MEL.connect_material_property(node,'',prop)
    MEL.recompile_material(surface);assert unreal.EditorAssetLibrary.save_loaded_asset(surface)
    bowl.set_material(0,surface)

    rect('VenueSoftKey',(-450,100,850),(0,0,45),(1.,.94,.85),1800,650,450)
    rect('VenueCoolRim',(450,-450,650),(0,0,100),(.7,.83,1.),1100,500,350)
    rect('VenueFloorFill',(0,-650,650),(0,-850,0),(.85,.9,1.),4000,1800,500)
    rect('CharacterSoftFill',(-650,250,420),(-410,-35,100),(1.,.93,.84),600,300,350)

    after_hit=bowl.line_trace_component(unreal.Vector(0,0,600),unreal.Vector(0,0,-200),True,False,False)
    assert after_hit and abs(after_hit[0].z-before_hit[0].z)<.001
    assert abs(male.get_actor_scale3d().x-2.165)<.001
    assert LEVELS.save_current_level()
    return {'map':MAP,'center_collision_z_cm':after_hit[0].z,'character_scale':2.165,
            'background':'reviewed env_arena image as unlit distant backdrop; near floor/walls are 3D',
            'camera_cm':[20,1150,650],'camera_target_cm':[-25,0,80],
            'main_sha256_before':MAIN_HASH}


STATE={'phase':'start','time':time.monotonic(),'busy':False,'handle':None,'report':{}}

def tick(dt):
    if STATE['busy']:return
    STATE['busy']=True
    try:
        elapsed=time.monotonic()-STATE['time']
        if STATE['phase']=='start' and elapsed>3:
            assert LEVELS.load_level('/Game/Maps/StadiumIndustrialCharacter125_v1')
            assert unreal.EditorLoadingAndSavingUtils.save_map(UES.get_editor_world(),MAP)
            assert LEVELS.load_level(MAP)
            STATE.update(phase='wait_map',time=time.monotonic())
        elif STATE['phase']=='wait_map' and elapsed>5:
            STATE['report']=build()
            STATE.update(phase='wait_editor',time=time.monotonic())
        elif STATE['phase']=='wait_editor' and elapsed>6:
            LEVELS.editor_request_begin_play();STATE.update(phase='wait_pie',time=time.monotonic())
        elif STATE['phase']=='wait_pie' and elapsed>6:
            world=UES.get_game_world();assert world
            pc=unreal.GameplayStatics.get_player_controller(world,0)
            assert pc.get_view_target().actor_has_tag('BattleCamera')
            assert unreal.GameplayStatics.get_game_mode(world).get_class().get_name()=='PrototypeBattleMode'
            unreal.SystemLibrary.execute_console_command(world,'showhud',pc)
            STATE['report']['pie_world']=world.get_path_name()
            STATE.update(phase='warmup',time=time.monotonic())
        elif STATE['phase']=='warmup' and elapsed>5:
            world=UES.get_game_world();pc=unreal.GameplayStatics.get_player_controller(world,0)
            path=str(OUT/'industrial_polish_PIE.png').replace('\\','/')
            unreal.SystemLibrary.execute_console_command(world,'HighResShot 1600x900 filename="'+path+'"',pc)
            STATE['report']['screenshot']=path
            STATE.update(phase='flush',time=time.monotonic())
        elif STATE['phase']=='flush' and elapsed>4:
            assert Path(STATE['report']['screenshot']).is_file()
            after=hashlib.sha256((ROOT/'Content/Maps/Main.umap').read_bytes()).hexdigest()
            assert after==MAIN_HASH
            STATE['report'].update(status='complete',main_sha256_after=after)
            if (OUT/'error.txt').exists(): (OUT/'error.txt').unlink()
            (OUT/'report.json').write_text(json.dumps(STATE['report'],indent=2),encoding='utf8')
            unreal.unregister_slate_post_tick_callback(STATE['handle'])
            LEVELS.editor_request_end_play()
            unreal.log('INDUSTRIAL_ART_POLISH_COMPLETE')
            unreal.SystemLibrary.quit_editor()
    except Exception:
        (OUT/'error.txt').write_text(traceback.format_exc(),encoding='utf8')
        unreal.log_error(traceback.format_exc())
        unreal.unregister_slate_post_tick_callback(STATE['handle'])
        unreal.SystemLibrary.quit_editor()
    finally:STATE['busy']=False

STATE['handle']=unreal.register_slate_post_tick_callback(tick)
