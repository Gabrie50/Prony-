import bpy
import bmesh
import mathutils
from mathutils import Vector, noise
import random
import math
import numpy as np

# ===== CONFIGURAÇÃO INICIAL =====
def clear_scene():
    """Limpar completamente a cena"""
    # Remover todos os objetos
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Limpar materiais órfãos
    for material in bpy.data.materials:
        if material.users == 0:
            bpy.data.materials.remove(material)
    
    # Limpar meshes órfãos
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

def setup_scene():
    """Configurar cena para Blender 4.5"""
    scene = bpy.context.scene
    
    # Configurar unidades
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    
    # Configurar world shader para ambiente
    world = scene.world
    world.use_nodes = True
    world_nodes = world.node_tree.nodes
    world_nodes.clear()
    
    # Background shader
    bg_node = world_nodes.new(type='ShaderNodeBackground')
    bg_node.inputs[0].default_value = (0.5, 0.7, 0.9, 1.0)  # Cor do céu
    bg_node.inputs[1].default_value = 0.8
    
    output_node = world_nodes.new(type='ShaderNodeOutputWorld')
    world.node_tree.links.new(bg_node.outputs[0], output_node.inputs[0])

# ===== MATERIAIS AVANÇADOS =====
def create_material_pbr(name, base_color, roughness=0.8, metallic=0.0, specular=0.5, 
                       emission_color=(0,0,0), emission_strength=0, alpha=1.0, 
                       normal_strength=1.0, use_subsurface=False):
    """Criar material PBR avançado para Blender 4.5"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    
    # Limpar nodes padrão
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Principled BSDF
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    # Configurar inputs
    bsdf.inputs['Base Color'].default_value = (*base_color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Specular IOR Level'].default_value = specular
    bsdf.inputs['Alpha'].default_value = alpha
    
    if emission_strength > 0:
        bsdf.inputs['Emission Color'].default_value = (*emission_color, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    
    if use_subsurface:
        bsdf.inputs['Subsurface Weight'].default_value = 0.1
        bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.2, 0.1)
    
    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Conectar
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    # Configurar blend mode se necessário
    if alpha < 1.0:
        mat.blend_method = 'BLEND'
    
    return mat

def create_procedural_terrain_material():
    """Material procedural para terreno com múltiplas camadas"""
    mat = bpy.data.materials.new(name="ProceduralTerrain")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Principled BSDF
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (400, 0)
    
    # Texture Coordinate
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    
    # Noise Texture para variação
    noise1 = nodes.new(type='ShaderNodeTexNoise')
    noise1.location = (-600, 200)
    noise1.inputs['Scale'].default_value = 5.0
    noise1.inputs['Detail'].default_value = 10.0
    
    noise2 = nodes.new(type='ShaderNodeTexNoise')
    noise2.location = (-600, -200)
    noise2.inputs['Scale'].default_value = 15.0
    noise2.inputs['Detail'].default_value = 5.0
    
    # ColorRamp para controlar distribuição
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (-400, 0)
    color_ramp.color_ramp.elements[0].color = (0.6, 0.35, 0.2, 1.0)  # Solo vermelho
    color_ramp.color_ramp.elements[1].color = (0.4, 0.25, 0.15, 1.0)  # Solo escuro
    
    # Mix nodes para combinar
    mix = nodes.new(type='ShaderNodeMix')
    mix.location = (-200, 0)
    mix.data_type = 'RGBA'
    mix.inputs['Fac'].default_value = 0.5
    
    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (600, 0)
    
    # Conectar nodes
    links = mat.node_tree.links
    links.new(tex_coord.outputs['Generated'], noise1.inputs['Vector'])
    links.new(tex_coord.outputs['Generated'], noise2.inputs['Vector'])
    links.new(noise1.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], mix.inputs['Color1'])
    links.new(noise2.outputs['Color'], mix.inputs['Color2'])
    links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_water_material():
    """Material avançado para água com reflexões"""
    mat = bpy.data.materials.new(name="AdvancedWater")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Principled BSDF
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (400, 0)
    bsdf.inputs['Base Color'].default_value = (0.1, 0.3, 0.6, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.1
    bsdf.inputs['Specular IOR Level'].default_value = 1.0
    bsdf.inputs['Transmission Weight'].default_value = 0.8
    bsdf.inputs['Alpha'].default_value = 0.8
    
    # Noise para ondulações
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)
    
    wave_texture = nodes.new(type='ShaderNodeTexWave')
    wave_texture.location = (-400, 0)
    wave_texture.wave_type = 'RINGS'
    wave_texture.inputs['Scale'].default_value = 10.0
    wave_texture.inputs['Distortion'].default_value = 2.0
    
    # Normal map
    normal_map = nodes.new(type='ShaderNodeNormalMap')
    normal_map.location = (200, -200)
    normal_map.inputs['Strength'].default_value = 0.5
    
    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (600, 0)
    
    # Conectar
    links = mat.node_tree.links
    links.new(tex_coord.outputs['Generated'], wave_texture.inputs['Vector'])
    links.new(wave_texture.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    mat.blend_method = 'BLEND'
    return mat

# ===== CRIAÇÃO DE GEOMETRIA =====
def create_terrain_cross_section():
    """Criar terreno em corte transversal com geometria detalhada"""
    # Criar mesh base
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    terrain = bpy.context.active_object
    terrain.name = "TerrainCrossSection"
    terrain.scale = (15, 10, 4)
    
    # Entrar em modo de edição
    bpy.context.view_layer.objects.active = terrain
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Subdivir para mais detalhes
    bpy.ops.mesh.select_all(action='SELECT')
    for _ in range(3):
        bpy.ops.mesh.subdivide()
    
    # Adicionar ruído para naturalidade
    bpy.ops.mesh.noise(factor=0.2)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Aplicar material procedural
    terrain_mat = create_procedural_terrain_material()
    terrain.data.materials.append(terrain_mat)
    
    return terrain

def create_geological_layers():
    """Criar camadas geológicas estratificadas"""
    layer_configs = [
        {"y_offset": -1.2, "thickness": 0.3, "color": (0.5, 0.3, 0.2), "name": "TopsoilLayer"},
        {"y_offset": -2.0, "thickness": 0.4, "color": (0.4, 0.25, 0.15), "name": "ClayLayer"}, 
        {"y_offset": -3.0, "thickness": 0.5, "color": (0.35, 0.2, 0.1), "name": "SandstoneLayer"},
        {"y_offset": -4.2, "thickness": 0.6, "color": (0.3, 0.15, 0.08), "name": "BedrockLayer"}
    ]
    
    layers = []
    for config in layer_configs:
        bpy.ops.mesh.primitive_cube_add(
            size=2, location=(0, 0, config["y_offset"])
        )
        layer = bpy.context.active_object
        layer.name = config["name"]
        layer.scale = (14.5, 9.5, config["thickness"])
        
        # Material da camada
        layer_mat = create_material_pbr(
            f"Material_{config['name']}", 
            config["color"], 
            roughness=0.9
        )
        layer.data.materials.append(layer_mat)
        layers.append(layer)
    
    return layers

def create_cerrado_vegetation():
    """Criar vegetação típica do Cerrado com distribuição natural"""
    tree_positions = []
    
    # Gerar posições naturais com ruído
    for i in range(15):
        x = random.uniform(-12, -4)
        y = random.uniform(-4, 4)
        z = 0.5 + noise.noise((x*0.1, y*0.1, 0)) * 0.3
        tree_positions.append((x, y, z))
    
    cerrado_trees = []
    
    for i, pos in enumerate(tree_positions):
        # Criar tronco com forma mais natural
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8, radius=random.uniform(0.12, 0.18), 
            depth=random.uniform(1.8, 2.8), location=pos
        )
        trunk = bpy.context.active_object
        trunk.name = f"CerradoTrunk_{i:02d}"
        
        # Deformar tronco para parecer mais natural
        bpy.context.view_layer.objects.active = trunk
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.randomize_transform(
            random_seed=i, loc_offset=0.1, scale_offset_uniform=0.05
        )
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Material do tronco
        trunk_mat = create_material_pbr(
            "CerradoTrunk", (0.4, 0.25, 0.15), roughness=0.95
        )
        trunk.data.materials.append(trunk_mat)
        
        # Criar copa irregular
        crown_height = pos[2] + trunk.dimensions.z/2 + random.uniform(0.8, 1.2)
        crown_pos = (pos[0], pos[1], crown_height)
        
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2, radius=random.uniform(0.9, 1.4), location=crown_pos
        )
        crown = bpy.context.active_object
        crown.name = f"CerradoCrown_{i:02d}"
        
        # Deformar copa
        crown.scale.z = random.uniform(0.6, 0.8)
        
        # Adicionar ruído à copa
        bpy.context.view_layer.objects.active = crown
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.noise(factor=0.15)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Material da copa
        crown_mat = create_material_pbr(
            "CerradoLeaves", (0.25, 0.45, 0.2), roughness=0.8, use_subsurface=True
        )
        crown.data.materials.append(crown_mat)
        
        cerrado_trees.extend([trunk, crown])
    
    return cerrado_trees

def create_amazon_rainforest():
    """Criar floresta amazônica densa e estratificada"""
    # Diferentes estratos da floresta
    strata_configs = [
        {"height_range": (4.0, 6.0), "density": 8, "radius_range": (0.25, 0.4), "crown_size": (1.5, 2.5)},
        {"height_range": (2.5, 4.0), "density": 12, "radius_range": (0.15, 0.25), "crown_size": (1.0, 1.5)},
        {"height_range": (1.0, 2.5), "density": 20, "radius_range": (0.08, 0.15), "crown_size": (0.6, 1.0)}
    ]
    
    amazon_trees = []
    tree_id = 0
    
    for strata in strata_configs:
        for _ in range(strata["density"]):
            # Posição dentro da área amazônica
            x = random.uniform(4, 13)
            y = random.uniform(-4, 4)
            z_base = random.uniform(0.3, 0.8)
            
            height = random.uniform(*strata["height_range"])
            radius = random.uniform(*strata["radius_range"])
            
            # Criar tronco
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=12, radius=radius, depth=height, location=(x, y, z_base)
            )
            trunk = bpy.context.active_object
            trunk.name = f"AmazonTrunk_{tree_id:02d}"
            
            # Material do tronco amazônico
            trunk_mat = create_material_pbr(
                "AmazonTrunk", (0.3, 0.2, 0.1), roughness=0.9
            )
            trunk.data.materials.append(trunk_mat)
            
            # Criar copa densa
            crown_size = random.uniform(*strata["crown_size"])
            crown_pos = (x, y, z_base + height/2 + crown_size * 0.8)
            
            bpy.ops.mesh.primitive_ico_sphere_add(
                subdivisions=3, radius=crown_size, location=crown_pos
            )
            crown = bpy.context.active_object
            crown.name = f"AmazonCrown_{tree_id:02d}"
            
            # Adicionar irregularidade à copa
            bpy.context.view_layer.objects.active = crown
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.noise(factor=0.2)
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Material da folhagem amazônica
            crown_mat = create_material_pbr(
                "AmazonCanopy", (0.1, 0.35, 0.15), roughness=0.7, use_subsurface=True
            )
            crown.data.materials.append(crown_mat)
            
            amazon_trees.extend([trunk, crown])
            tree_id += 1
    
    return amazon_trees

def create_river_system():
    """Criar sistema fluvial amazônico com meandros"""
    # Criar curva para o rio principal
    curve_data = bpy.data.curves.new(name="RiverCurve", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 12
    
    # Criar spline
    spline = curve_data.splines.new('BEZIER')
    # Pontos do rio com meandros naturais
    river_points = [
        (5.5, -4, 0.1), (6.5, -2, 0.1), (7.8, 0, 0.1), 
        (8.5, 2, 0.1), (9.2, 4, 0.1)
    ]
    
    spline.bezier_points.add(len(river_points) - 1)
    
    for i, point in enumerate(river_points):
        bp = spline.bezier_points[i]
        bp.co = point
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    
    # Criar objeto da curva
    river_curve_obj = bpy.data.objects.new("RiverCurve", curve_data)
    bpy.context.collection.objects.link(river_curve_obj)
    
    # Converter para mesh
    bpy.context.view_layer.objects.active = river_curve_obj
    bpy.ops.object.convert(target='MESH')
    
    # Aplicar modificadores
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    river_curve_obj.modifiers["Solidify"].thickness = 0.8
    river_curve_obj.modifiers["Solidify"].offset = -1
    
    bpy.ops.object.modifier_add(type='BEVEL')
    river_curve_obj.modifiers["Bevel"].width = 0.3
    
    # Material da água
    water_mat = create_water_material()
    river_curve_obj.data.materials.append(water_mat)
    
    return river_curve_obj

def create_underground_water_system():
    """Criar sistema de águas subterrâneas detalhado"""
    underground_segments = [
        {"start": (-8, -1, -0.8), "end": (-5, 0, -1.0)},
        {"start": (-5, 0, -1.0), "end": (-2, 0.5, -1.2)},
        {"start": (-2, 0.5, -1.2), "end": (1, 1, -1.0)},
        {"start": (1, 1, -1.0), "end": (4, 1.5, -0.8)},
        {"start": (4, 1.5, -0.8), "end": (6, 2, -0.5)}
    ]
    
    underground_rivers = []
    
    for i, segment in enumerate(underground_segments):
        start = Vector(segment["start"])
        end = Vector(segment["end"])
        center = (start + end) / 2
        direction = end - start
        length = direction.length
        
        # Criar geometria do rio subterrâneo
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16, radius=0.12, depth=length, location=center
        )
        underground_river = bpy.context.active_object
        underground_river.name = f"UndergroundRiver_{i:02d}"
        
        # Orientar na direção correta
        underground_river.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
        
        # Material da água subterrânea
        underground_mat = create_material_pbr(
            "UndergroundWater", (0.2, 0.4, 0.7), 
            roughness=0.2, alpha=0.8, emission_color=(0.1, 0.2, 0.4), emission_strength=0.5
        )
        underground_river.data.materials.append(underground_mat)
        
        underground_rivers.append(underground_river)
    
    return underground_rivers

def create_atmospheric_effects():
    """Criar efeitos atmosféricos: nuvens, chuva e evaporação"""
    effects = []
    
    # === NUVEM DE CHUVA ===
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=3, radius=1.8, location=(-8, 0, 7)
    )
    rain_cloud = bpy.context.active_object
    rain_cloud.name = "RainCloud"
    rain_cloud.scale = (2.5, 2.0, 1.2)
    
    # Deformar nuvem
    bpy.context.view_layer.objects.active = rain_cloud
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.noise(factor=0.3)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Material da nuvem
    cloud_mat = create_material_pbr(
        "CloudMaterial", (0.9, 0.9, 0.95), roughness=0.8, alpha=0.9,
        use_subsurface=True
    )
    rain_cloud.data.materials.append(cloud_mat)
    
    # === SISTEMA DE CHUVA ===
    # Adicionar sistema de partículas para chuva
    bpy.context.view_layer.objects.active = rain_cloud
    bpy.ops.object.particle_system_add()
    rain_system = rain_cloud.particle_systems[0]
    rain_settings = rain_system.settings
    
    rain_settings.name = "RainParticles"
    rain_settings.count = 500
    rain_settings.lifetime = 60
    rain_settings.normal_factor = 0
    rain_settings.emit_from = 'VOLUME'
    rain_settings.distribution = 'RAND'
    
    # Física das gotas
    rain_settings.physics_type = 'NEWTON'
    rain_settings.particle_size = 0.02
    rain_settings.size_random = 0.5
    rain_settings.effector_weights.gravity = 3.0
    
    # Velocidade inicial
    rain_settings.velocity_factor = 2.0
    
    # === COLUNA DE EVAPORAÇÃO ===
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16, radius=0.8, depth=5, location=(8, 0, 2.5)
    )
    evaporation = bpy.context.active_object
    evaporation.name = "EvaporationColumn"
    
    # Deformar coluna
    bpy.context.view_layer.objects.active = evaporation
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.noise(factor=0.1)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Material da evaporação
    evap_mat = create_material_pbr(
        "EvaporationMaterial", (0.95, 0.95, 1.0), roughness=0.1, alpha=0.3,
        emission_color=(0.9, 0.9, 1.0), emission_strength=0.2
    )
    evaporation.data.materials.append(evap_mat)
    
    effects.extend([rain_cloud, evaporation])
    return effects

def create_detailed_labels():
    """Criar legendas 3D com estilo científico"""
    labels_config = [
        {"text": "CERRADO", "location": (-8, -6, 3), "size": 1.8, "extrude": 0.05},
        {"text": "BACIA AMAZÔNICA", "location": (6, -6, 3), "size": 1.4, "extrude": 0.05},
        {"text": "EVAPORAÇÃO", "location": (9, -3, 6), "size": 1.0, "extrude": 0.03},
        {"text": "RIOS\nSUBTERRÂNEOS", "location": (0, -7, -1.5), "size": 0.9, "extrude": 0.03}
    ]
    
    labels = []
    
    for config in labels_config:
        # Criar texto
        font_curve = bpy.data.curves.new(type="FONT", name=f"Label_{config['text']}")
        font_curve.body = config["text"]
        font_curve.size = config["size"]
        font_curve.extrude = config["extrude"]
        font_curve.bevel_depth = 0.01
        font_curve.bevel_resolution = 2
        
        # Criar objeto
        font_obj = bpy.data.objects.new(name=f"Label_{config['text']}", object_data=font_curve)
        font_obj.location = config["location"]
        bpy.context.collection.objects.link(font_obj)
        
        # Material do texto
        text_mat = create_material_pbr(
            f"TextMat_{config['text']}", (1.0, 1.0, 1.0), roughness=0.3,
            emission_color=(1.0, 1.0, 1.0), emission_strength=0.5
        )
        font_obj.data.materials.append(text_mat)
        
        labels.append(font_obj)
    
    return labels

# ===== ILUMINAÇÃO E CÂMERA =====
def setup_advanced_lighting():
    """Configurar sistema de iluminação cinematográfico"""
    # === SOL PRINCIPAL ===
    bpy.ops.object.light_add(type='SUN', location=(10, -10, 15))
    sun = bpy.context.active_object
    sun.name = "MainSun"
    sun.data.energy = 4.0
    sun.data.angle = math.radians(5)  # Sol mais focado
    sun.rotation_euler = (math.radians(30), math.radians(30), 0)
    
    # === LUZ DE PREENCHIMENTO ===
    bpy.ops.object.light_add(type='AREA', location=(-8, -8, 12))
    fill_light = bpy.context.active_object
    fill_light.name = "FillLight"
    fill_light.data.energy = 2.0
    fill_light.data.size = 8
    fill_light.data.color = (0.8, 0.9, 1.0)
    
    # === LUZ DE CONTORNO ===
    bpy.ops.object.light_add(type='SPOT', location=(0, 12, 8))
    rim_light = bpy.context.active_object
    rim_light.name = "RimLight"
    rim_light.data.energy = 3.0
    rim_light.data.spot_size = math.radians(60)
    rim_light.data.spot_blend = 0.2
    rim_light.rotation_euler = (math.radians(-30), 0, math.radians(180))
    
    return [sun, fill_light, rim_light]

def setup_cinematic_camera():
    """Configurar câmera com enquadramento cinematográfico"""
    bpy.ops.object.camera_add(location=(20, -20, 15))
    camera = bpy.context.active_object
    camera.name = "MainCamera"
    
    # Configurar rotação para vista isométrica científica
    camera.rotation_euler = (math.radians(55), 0, math.radians(42))
    
    # Configurações da câmera
    camera.data.lens = 85  # Lente telefoto para menos distorção
    camera.data.sensor_width = 36
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 25.0
    camera.data.dof.aperture_fstop = 5.6
    
    # Definir como câmera ativa
    bpy.context.scene.camera = camera
    
    return camera

# ===== RENDERIZAÇÃO =====
def setup_render_settings():
    """Configurar settings de render para qualidade máxima"""
    scene = bpy.context.scene
    
    # Engine de render
    scene.render.engine = 'CYCLES'
    
    # Configurações de qualidade
    scene.cycles.samples = 256  # Alta qualidade
    scene.cycles.preview_samples = 64
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPTIX'  # Melhor denoiser para GPUs NVIDIA
    
    # Configurações de dispositivo
    scene.cycles.device = 'GPU'
    
    # Resolução
    scene.render.resolution_x = 2560
    scene.render.resolution_y = 1440
    scene.render.resolution_percentage = 100
    
    # Formato de saída
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '16'
    
    # Color Management
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = 0.5
    scene.view_settings.gamma = 1.0
    
    # Motion Blur e DOF
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5

def add_geometry_nodes_effects():
    """Adicionar efeitos procedurais com Geometry Nodes"""
    # === GRAMA PROCEDURAL ===
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0.02))
    grass_plane = bpy.context.active_object
    grass_plane.name = "GrassPlane"
    
    # Adicionar Geometry Nodes
    bpy.ops.object.modifier_add(type='NODES')
    grass_modifier = grass_plane.modifiers[-1]
    
    # Criar node group para grama
    grass_node_group = bpy.data.node_groups.new('GrassGenerator', 'GeometryNodeTree')
    grass_modifier.node_group = grass_node_group
    
    # Input e Output nodes
    group_input = grass_node_group.nodes.new('NodeGroupInput')
    group_output = grass_node_group.nodes.new('NodeGroupOutput')
    group_input.location = (-400, 0)
    group_output.location = (400, 0)
    
    # Distribute Points on Faces
    distribute_points = grass_node_group.nodes.new('GeometryNodeDistributePointsOnFaces')
    distribute_points.location = (-200, 0)
    distribute_points.inputs['Density'].default_value = 100.0
    
    # Instance on Points
    instance_points = grass_node_group.nodes.new('GeometryNodeInstanceOnPoints')
    instance_points.location = (0, 0)
    
    # Criar grama individual
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.01, depth=0.1, location=(0, 0, 50))
    grass_blade = bpy.context.active_object
    grass_blade.name = "GrassBlade"
    grass_blade.scale.z = 3
    
    # Conectar nodes
    grass_node_group.links.new(group_input.outputs['Geometry'], distribute_points.inputs['Mesh'])
    grass_node_group.links.new(distribute_points.outputs['Points'], instance_points.inputs['Points'])
    grass_node_group.links.new(instance_points.outputs['Instances'], group_output.inputs['Geometry'])
    
    # Material da grama
    grass_mat = create_material_pbr(
        "GrassMaterial", (0.2, 0.6, 0.1), roughness=0.8, use_subsurface=True
    )
    grass_plane.data.materials.append(grass_mat)
    
    return grass_plane

def create_particle_systems():
    """Criar sistemas de partículas avançados"""
    particle_objects = []
    
    # === PARTÍCULAS DE UMIDADE ===
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, 20))
    humidity_emitter = bpy.context.active_object
    humidity_emitter.name = "HumidityEmitter"
    humidity_emitter.scale = (20, 15, 0.1)
    
    # Sistema de partículas para umidade
    bpy.ops.object.particle_system_add()
    humidity_system = humidity_emitter.particle_systems[0]
    humidity_settings = humidity_system.settings
    
    humidity_settings.name = "HumidityParticles"
    humidity_settings.count = 1000
    humidity_settings.lifetime = 200
    humidity_settings.emit_from = 'VOLUME'
    humidity_settings.distribution = 'RAND'
    humidity_settings.physics_type = 'BOIDS'
    humidity_settings.particle_size = 0.005
    humidity_settings.size_random = 0.8
    
    # Configurar movimento tipo névoa
    humidity_settings.normal_factor = 0.1
    humidity_settings.brownian_factor = 0.05
    
    particle_objects.append(humidity_emitter)
    
    # === POEIRA ATMOSFÉRICA ===
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, 10))
    dust_emitter = bpy.context.active_object
    dust_emitter.name = "DustEmitter"
    dust_emitter.scale = (25, 20, 5)
    
    bpy.ops.object.particle_system_add()
    dust_system = dust_emitter.particle_systems[0]
    dust_settings = dust_system.settings
    
    dust_settings.name = "DustParticles"
    dust_settings.count = 500
    dust_settings.lifetime = 300
    dust_settings.emit_from = 'VOLUME'
    dust_settings.physics_type = 'NEWTON'
    dust_settings.particle_size = 0.003
    dust_settings.effector_weights.gravity = 0.1
    dust_settings.brownian_factor = 0.1
    
    particle_objects.append(dust_emitter)
    
    return particle_objects

def add_volumetrics():
    """Adicionar efeitos volumétricos para atmosfera"""
    # === VOLUME SCATTER PARA ATMOSFERA ===
    world = bpy.context.scene.world
    world_nodes = world.node_tree.nodes
    
    # Limpar nodes existentes
    for node in world_nodes:
        if node.type != 'OUTPUT_WORLD':
            world_nodes.remove(node)
    
    output_node = world_nodes['World Output']
    
    # Background
    bg_node = world_nodes.new(type='ShaderNodeBackground')
    bg_node.location = (-300, 100)
    bg_node.inputs['Color'].default_value = (0.5, 0.7, 0.9, 1.0)
    bg_node.inputs['Strength'].default_value = 0.8
    
    # Volume Scatter para atmosfera
    vol_scatter = world_nodes.new(type='ShaderNodeVolumeScatter')
    vol_scatter.location = (-300, -100)
    vol_scatter.inputs['Color'].default_value = (0.8, 0.9, 1.0, 1.0)
    vol_scatter.inputs['Density'].default_value = 0.01
    vol_scatter.inputs['Anisotropy'].default_value = 0.2
    
    # Conectar
    world.node_tree.links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])
    world.node_tree.links.new(vol_scatter.outputs['Volume'], output_node.inputs['Volume'])

def create_water_caustics():
    """Criar efeitos de cáusticas na água"""
    # Criar plano para receber cáusticas
    bpy.ops.mesh.primitive_plane_add(size=15, location=(8, 0, -0.1))
    caustics_plane = bpy.context.active_object
    caustics_plane.name = "CausticsPlane"
    
    # Material com cáusticas procedurais
    caustics_mat = bpy.data.materials.new(name="CausticsMaterial")
    caustics_mat.use_nodes = True
    nodes = caustics_mat.node_tree.nodes
    nodes.clear()
    
    # Principled BSDF
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (400, 0)
    bsdf.inputs['Base Color'].default_value = (0.8, 0.9, 1.0, 1.0)
    
    # Texture Coordinate
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    
    # Voronoi para padrão de cáusticas
    voronoi = nodes.new(type='ShaderNodeTexVoronoi')
    voronoi.location = (-600, 0)
    voronoi.voronoi_dimensions = '2D'
    voronoi.feature = 'F2'
    voronoi.inputs['Scale'].default_value = 15.0
    
    # Wave texture para movimento
    wave = nodes.new(type='ShaderNodeTexWave')
    wave.location = (-600, -300)
    wave.wave_type = 'RINGS'
    wave.inputs['Scale'].default_value = 8.0
    wave.inputs['Distortion'].default_value = 3.0
    
    # Mix para combinar
    mix = nodes.new(type='ShaderNodeMix')
    mix.location = (-400, 0)
    mix.data_type = 'RGBA'
    mix.inputs['Fac'].default_value = 0.7
    
    # ColorRamp para contraste
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (-200, 0)
    color_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    color_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    
    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (600, 0)
    
    # Conectar nodes
    links = caustics_mat.node_tree.links
    links.new(tex_coord.outputs['Generated'], voronoi.inputs['Vector'])
    links.new(tex_coord.outputs['Generated'], wave.inputs['Vector'])
    links.new(voronoi.outputs['Distance'], mix.inputs['Color1'])
    links.new(wave.outputs['Color'], mix.inputs['Color2'])
    links.new(mix.outputs['Result'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], bsdf.inputs['Emission Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    caustics_plane.data.materials.append(caustics_mat)
    return caustics_plane

def add_wind_effects():
    """Adicionar efeitos de vento na vegetação"""
    # Criar força de vento
    bpy.ops.object.effector_add(type='WIND', location=(0, -15, 5))
    wind_force = bpy.context.active_object
    wind_force.name = "WindForce"
    wind_force.field.strength = 2.0
    wind_force.field.flow = 0.5
    wind_force.field.noise = 0.3
    wind_force.rotation_euler = (0, math.radians(15), 0)
    
    return wind_force

def create_composition_nodes():
    """Configurar nós de composição para pós-processamento"""
    # Ativar compositor
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    
    # Limpar nodes existentes
    for node in tree.nodes:
        tree.nodes.remove(node)
    
    # Render Layers
    render_layers = tree.nodes.new(type='CompositorNodeRLayers')
    render_layers.location = (-300, 0)
    
    # Denoise (se necessário)
    denoise = tree.nodes.new(type='CompositorNodeDenoise')
    denoise.location = (-100, 100)
    
    # Color Balance
    color_balance = tree.nodes.new(type='CompositorNodeColorBalance')
    color_balance.location = (100, 0)
    color_balance.correction_method = 'LIFT_GAMMA_GAIN'
    
    # Vignette effect
    ellipse_mask = tree.nodes.new(type='CompositorNodeEllipseMask')
    ellipse_mask.location = (-100, -200)
    ellipse_mask.width = 0.8
    ellipse_mask.height = 0.8
    
    blur = tree.nodes.new(type='CompositorNodeBlur')
    blur.location = (100, -200)
    blur.size_x = 20
    blur.size_y = 20
    
    mix_vignette = tree.nodes.new(type='CompositorNodeMixRGB')
    mix_vignette.location = (300, -100)
    mix_vignette.blend_type = 'MULTIPLY'
    mix_vignette.inputs['Fac'].default_value = 0.3
    
    # Output
    composite = tree.nodes.new(type='CompositorNodeComposite')
    composite.location = (500, 0)
    
    # Conectar nodes
    links = tree.links
    links.new(render_layers.outputs['Image'], denoise.inputs['Image'])
    links.new(denoise.outputs['Image'], color_balance.inputs['Image'])
    links.new(render_layers.outputs['Image'], ellipse_mask.inputs['Mask'])
    links.new(ellipse_mask.outputs['Mask'], blur.inputs['Image'])
    links.new(color_balance.outputs['Image'], mix_vignette.inputs['Image1'])
    links.new(blur.outputs['Image'], mix_vignette.inputs['Image2'])
    links.new(mix_vignette.outputs['Image'], composite.inputs['Image'])

# ===== FUNÇÃO PRINCIPAL =====
def main():
    """Função principal para criar toda a cena do ciclo da água"""
    print("="*60)
    print("🌊 INICIANDO CRIAÇÃO DA CENA DO CICLO DA ÁGUA")
    print("🎯 Versão: Blender 4.5 - Qualidade Cinematográfica")
    print("="*60)
    
    # === FASE 1: PREPARAÇÃO ===
    print("\n📋 FASE 1: Preparando ambiente...")
    clear_scene()
    setup_scene()
    print("✅ Ambiente preparado")
    
    # === FASE 2: CRIAÇÃO DO TERRENO ===
    print("\n🏔️ FASE 2: Criando estrutura geológica...")
    terrain = create_terrain_cross_section()
    layers = create_geological_layers()
    print(f"✅ Terreno criado com {len(layers)} camadas geológicas")
    
    # === FASE 3: VEGETAÇÃO ===
    print("\n🌳 FASE 3: Criando vegetação...")
    cerrado_trees = create_cerrado_vegetation()
    amazon_trees = create_amazon_rainforest()
    print(f"✅ Vegetação criada:")
    print(f"   🌿 Cerrado: {len(cerrado_trees)//2} árvores")
    print(f"   🌲 Amazônia: {len(amazon_trees)//2} árvores")
    
    # === FASE 4: SISTEMA HÍDRICO ===
    print("\n💧 FASE 4: Criando sistema hídrico...")
    river = create_river_system()
    underground_rivers = create_underground_water_system()
    caustics = create_water_caustics()
    print(f"✅ Sistema hídrico criado:")
    print(f"   🏞️ Rio principal: 1 sistema")
    print(f"   🌊 Rios subterrâneos: {len(underground_rivers)} segmentos")
    print(f"   ✨ Efeitos de cáusticas aplicados")
    
    # === FASE 5: EFEITOS ATMOSFÉRICOS ===
    print("\n☁️ FASE 5: Criando atmosfera...")
    atmospheric_effects = create_atmospheric_effects()
    particle_systems = create_particle_systems()
    wind = add_wind_effects()
    add_volumetrics()
    print(f"✅ Atmosfera criada:")
    print(f"   ☁️ Efeitos atmosféricos: {len(atmospheric_effects)}")
    print(f"   💨 Sistemas de partículas: {len(particle_systems)}")
    print(f"   🌪️ Campo de vento ativo")
    
    # === FASE 6: EFEITOS PROCEDURAIS ===
    print("\n🔧 FASE 6: Aplicando efeitos procedurais...")
    grass_plane = add_geometry_nodes_effects()
    print("✅ Grama procedural aplicada")
    
    # === FASE 7: LEGENDAS ===
    print("\n📝 FASE 7: Criando legendas...")
    labels = create_detailed_labels()
    print(f"✅ {len(labels)} legendas científicas criadas")
    
    # === FASE 8: ILUMINAÇÃO ===
    print("\n💡 FASE 8: Configurando iluminação cinematográfica...")
    lights = setup_advanced_lighting()
    print(f"✅ Sistema de iluminação configurado:")
    print(f"   ☀️ {len(lights)} fontes de luz criadas")
    
    # === FASE 9: CÂMERA ===
    print("\n📷 FASE 9: Posicionando câmera...")
    camera = setup_cinematic_camera()
    print("✅ Câmera cinematográfica configurada")
    
    # === FASE 10: RENDER E PÓS-PROCESSAMENTO ===
    print("\n🎬 FASE 10: Configurando render...")
    setup_render_settings()
    create_composition_nodes()
    print("✅ Configurações de render otimizadas:")
    print("   📊 Resolução: 2560x1440")
    print("   🔥 Engine: Cycles GPU")
    print("   ✨ Samples: 256 (alta qualidade)")
    print("   🎨 Pós-processamento ativo")
    
    # === RELATÓRIO FINAL ===
    print("\n" + "="*60)
    print("🎉 CENA CRIADA COM SUCESSO!")
    print("="*60)
    print("📊 ESTATÍSTICAS FINAIS:")
    print(f"   🎯 Objetos totais: {len(bpy.context.scene.objects)}")
    print(f"   🎨 Materiais: {len(bpy.data.materials)}")
    print(f"   💡 Luzes: {len([obj for obj in bpy.context.scene.objects if obj.type == 'LIGHT'])}")
    print(f"   📝 Textos: {len([obj for obj in bpy.context.scene.objects if obj.type == 'FONT'])}")
    print("\n🚀 PRÓXIMOS PASSOS:")
    print("   1. Navegue pela viewport (scroll do mouse para zoom)")
    print("   2. Pressione F12 para renderizar")
    print("   3. Pressione Numpad 0 para ver pela câmera")
    print("   4. Use Shift+Numpad 7/1/3 para vistas ortogonais")
    print("\n💡 DICAS DE OTIMIZAÇÃO:")
    print("   - Viewport Shading: Material Preview")
    print("   - Para render rápido: reduza Samples para 64")
    print("   - Para máxima qualidade: aumente para 512")
    print("="*60)

# ===== EXECUÇÃO DO SCRIPT =====
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO DURANTE A EXECUÇÃO: {str(e)}")
        print("🔧 Verifique se está usando Blender 4.5 ou superior")
        import traceback
        traceback.print_exc()
    else:
        print("\n✅ Script executado com sucesso!")
        print("🎬 Sua cena do ciclo da água está pronta para render!")
