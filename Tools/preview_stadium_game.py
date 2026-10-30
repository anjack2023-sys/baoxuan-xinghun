"""Batch-only: capture PIE views in isolated maps, then close this editor instance."""
import hashlib
import json
import time
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT=ROOT/'screenshots/stadium-game-preview'
OUT.mkdir(parents=True,exist_ok=True)
MAIN_HASH=hashlib.sha256((ROOT/'Content/Maps/Main.umap').read_bytes()).hexdigest()
LEVELS=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
STATE={'phase':'start','t':time.monotonic(),'handle':None,'index':1 if (OUT/'before_PIE.png').exists() else 0,'views':[],
       'main_sha256_before':MAIN_HASH,'busy':False}
if STATE['index']:
    STATE['views'].append({'name':'before','screenshot':str(OUT/'before_PIE.png'),
        'world':'/Game/Maps/UEDPIE_0_Main.Main','game_mode':'PrototypeBattleMode','camera':'BattleCamera'})
CASES=[('before','/Game/Maps/Main',None),
       ('industrial','/Game/Maps/StadiumIndustrialPreview_v1',
        '/Game/ArtPreview/IndustrialGame_v1/industrial-bowl-original/StaticMeshes/industrial-bowl-original.industrial-bowl-original'),
       ('original','/Game/Maps/StadiumOriginalPreview_v1','/Game/Imported/Stadium/SM_Stadium.SM_Stadium')]

def report():
    (OUT/'report.json').write_text(json.dumps({k:v for k,v in STATE.items() if k!='handle'},indent=2),encoding='utf8')

def transition(phase):
    STATE['phase']=phase;STATE['t']=time.monotonic();report()
    unreal.log('STADIUM_GAME_PREVIEW '+phase)

def find(label):
    return next(a for a in ACTORS.get_all_level_actors() if a.get_actor_label()==label)

def prepare(case):
    name,map_path,mesh_path=case
    if mesh_path and not unreal.EditorAssetLibrary.does_asset_exist(map_path):
        # Save As avoids retaining a duplicated UWorld during editor map cleanup.
        assert unreal.EditorLoadingAndSavingUtils.save_map(UES.get_editor_world(),map_path)
    assert LEVELS.load_level(map_path)
    if not mesh_path:
        return
    bowl=find('SmoothBowl_v1')
    component=bowl.get_component_by_class(unreal.StaticMeshComponent)
    mesh=unreal.load_asset(mesh_path)
    assert isinstance(mesh,unreal.StaticMesh),mesh_path
    component.set_static_mesh(mesh)
    for i in range(component.get_num_materials()):
        component.set_material(i,mesh.get_material(i))
    if name=='original':
        mat_path='/Game/ArtPreview/OriginalGame_v1/M_OriginalSource'
        mat=unreal.load_asset(mat_path)
        if mat is None:
            mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_OriginalSource','/Game/ArtPreview/OriginalGame_v1',unreal.Material,unreal.MaterialFactoryNew())
            tex=unreal.load_asset('/Game/Imported/Stadium/TEX_stadium_basecolor')
            assert tex, 'Original texture missing'
            sample=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionTextureSample)
            sample.texture=tex
            unreal.MaterialEditingLibrary.connect_material_property(sample,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
            for prop,value in [(unreal.MaterialProperty.MP_ROUGHNESS,.65),(unreal.MaterialProperty.MP_METALLIC,.25)]:
                node=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant)
                node.r=value
                unreal.MaterialEditingLibrary.connect_material_property(node,'',prop)
            unreal.MaterialEditingLibrary.recompile_material(mat)
            assert unreal.EditorAssetLibrary.save_loaded_asset(mat)
        component.set_material(0,mat)
    body=mesh.get_editor_property('body_setup')
    body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    bounds=mesh.get_bounds(); e=bounds.box_extent
    # Reorient only when the imported narrow axis is not vertical.
    rotation=unreal.Rotator()
    if e.y<e.z and e.y<e.x: rotation=unreal.Rotator(0,0,90)
    elif e.x<e.z and e.x<e.y: rotation=unreal.Rotator(90,0,0)
    bowl.set_actor_rotation(rotation,False)
    bowl.set_actor_scale3d(unreal.Vector(1,1,1))
    bowl.set_actor_location(unreal.Vector(),False,True)
    origin,extent=bowl.get_actor_bounds(False)
    # Industrial rim is radius .2945 m; use its actual playable diameter, not clamps.
    scale=230./29.45 if name=='industrial' else 250./max(extent.x,extent.y)
    bowl.set_actor_scale3d(unreal.Vector(scale,scale,scale))
    origin,extent=bowl.get_actor_bounds(False)
    bowl.set_actor_location(unreal.Vector(-origin.x,-origin.y,0),False,True)
    hit=component.line_trace_component(unreal.Vector(0,0,600),unreal.Vector(0,0,-200),True,False,False)
    STATE['trace_return']=str(hit)
    # Python line_trace_component returns (impact point, normal, bone, hit result).
    if isinstance(hit,tuple):
        impact=hit[0]
    else:
        assert hit is not None,'No bowl center collision'
        impact=hit.impact_point
    z=42.-impact.z
    current=bowl.get_actor_location()
    bowl.set_actor_location(unreal.Vector(current.x,current.y,z),False,True)
    camera=find('BattleCamera')
    # Use the real gameplay camera with a wider framing to include industrial clamps.
    camera.set_actor_location(unreal.Vector(20,1000,750),False,True)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(-25,0,65)),False)
    camera.camera_component.set_field_of_view(56)
    male=find('MaleLead')
    male.set_actor_scale3d(unreal.Vector(2.165,2.165,2.165))
    male.set_actor_location(unreal.Vector(-(extent.x+80),-35,0),False,True)
    assert LEVELS.save_current_level()
    STATE[name+'_setup']={'map':map_path,'mesh':mesh_path,'scale':scale,'center_z_cm':42.,'offset_z_cm':z,
                          'rotation':str(rotation),'collision':'actual visible mesh, complex query'}
    report()

def run_tick(dt):
    try:
        elapsed=time.monotonic()-STATE['t']
        phase=STATE['phase']
        if phase=='start' and elapsed>3:
            prepare(CASES[STATE['index']]);transition('wait_editor')
        elif phase=='wait_editor' and elapsed>3:
            LEVELS.editor_request_begin_play();transition('wait_pie')
        elif phase=='wait_pie':
            world=UES.get_game_world()
            if world and elapsed>4:
                pc=unreal.GameplayStatics.get_player_controller(world,0)
                assert pc and pc.get_view_target().actor_has_tag('BattleCamera')
                mode=unreal.GameplayStatics.get_game_mode(world)
                assert mode.get_class().get_name()=='PrototypeBattleMode'
                unreal.SystemLibrary.execute_console_command(world,'showhud',pc)
                STATE['views'].append({'name':CASES[STATE['index']][0],'world':world.get_path_name(),
                                      'game_mode':mode.get_class().get_name(),'camera':pc.get_view_target().get_actor_label()})
                transition('warmup')
            elif elapsed>60: raise RuntimeError('PIE world timeout')
        elif phase=='warmup' and elapsed>4:
            world=UES.get_game_world();pc=unreal.GameplayStatics.get_player_controller(world,0)
            name=CASES[STATE['index']][0]
            path=str(OUT/(name+'_PIE.png')).replace('\\','/')
            unreal.SystemLibrary.execute_console_command(world,'HighResShot 1600x900 filename="'+path+'"',pc)
            STATE['views'][-1]['screenshot']=path
            transition('flush')
        elif phase=='flush' and elapsed>3:
            LEVELS.editor_request_end_play();transition('end_pie')
        elif phase=='end_pie' and elapsed>3 and not UES.get_game_world():
            STATE['index']+=1
            if STATE['index']<len(CASES):
                prepare(CASES[STATE['index']]);transition('wait_editor')
            else:
                STATE['main_sha256_after']=hashlib.sha256((ROOT/'Content/Maps/Main.umap').read_bytes()).hexdigest()
                assert STATE['main_sha256_after']==MAIN_HASH,'Main map changed unexpectedly'
                assert all(Path(v['screenshot']).is_file() for v in STATE['views'])
                transition('complete')
                unreal.unregister_slate_post_tick_callback(STATE['handle'])
                unreal.SystemLibrary.quit_editor()
        if STATE['phase'] not in ('complete','failed') and elapsed>90:
            raise RuntimeError('Phase timeout '+phase)
    except Exception:
        STATE['error']=traceback.format_exc();transition('failed')
        unreal.log_error(STATE['error'])
        unreal.unregister_slate_post_tick_callback(STATE['handle'])
        unreal.SystemLibrary.quit_editor()

def tick(dt):
    if STATE['busy']: return
    STATE['busy']=True
    try: run_tick(dt)
    finally: STATE['busy']=False

STATE['handle']=unreal.register_slate_post_tick_callback(tick)
report()
