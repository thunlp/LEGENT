from legent import Environment, Observation, generate_scene, ResetInfo, get_mesh_size, load_json
from PIL import Image as PILImage
from pygltflib import GLTF2, Scene, Node, Mesh, Primitive, Buffer, BufferView, Accessor, Image, Texture, TextureInfo, Material, PbrMetallicRoughness, ImageFormat
from base64 import b64encode
import struct
import io
import os
import compress_pickle
import trimesh
import numpy as np
from use_objaverse import objaverse_object


def convert_holodeck_asset_to_gltf(asset_path, output_file):
    uid = os.path.basename(asset_path)
    mesh_data = compress_pickle.load(f"{asset_path}/{uid}.pkl.gz")

    # Vertex data
    vertices = [coord for v in mesh_data["vertices"] for coord in (v["x"], v["y"], v["z"])]

    # Normal vectors for each vertex
    normals = [coord for v in mesh_data["normals"] for coord in (v["x"], v["y"], v["z"])]

    # Holodeck has a y rotation. We need to rotate the object to make it face the right direction.
    def rotate(vs, y_rot_offset):  # Rotation offset in degrees
        vs = vs.reshape(-1, 3)

        # Convert rotation offset from degrees to radians and negate it (inverse rotation)
        radians = -np.radians(y_rot_offset)

        # Calculate the cosine and sine of the negative rotation angle
        cosTheta = np.cos(radians)
        sinTheta = np.sin(radians)

        # Rotation matrix for Y-axis rotation
        rotation_matrix = np.array([[cosTheta, 0, sinTheta], [0, 1, 0], [-sinTheta, 0, cosTheta]])

        # Apply the inverse rotation to each vertex
        transformed_vs = np.dot(vs, rotation_matrix)

        # Holodeck model is left-handed, while glTF is right-handed.
        # We need to flip the z axis of positions and normals.
        transformed_vs[:, 2] *= -1

        vs = transformed_vs.reshape(-1)
        return vs

    y_rot_offset = mesh_data["yRotOffset"]
    # NOTE: Holodeck use GPT4-V to annotate the front view. It is not always aligned with the positive direction of the Z-axis and consistent with LEGENT's default assets.
    # For TV 20de33c317ce49a687b9fe8075d60e8a, it is aligned.
    # For bed cd956b2abec04b52ac48bea1ec141d60, it is not aligned.
    vertices = rotate(np.array(vertices), y_rot_offset)
    normals = rotate(np.array(normals), y_rot_offset)

    vertices, normals = vertices.tolist(), normals.tolist()

    # Holodeck texture starts from the top left corner, while glTF texture starts from the bottom left corner.
    # We need to calculate the y coordinate of UVs.
    # UV coordinates for each vertex
    uvs = [coord for v in mesh_data["uvs"] for coord in (v["x"], 1 - v["y"])]

    # Holodeck model is left-handed, while glTF is right-handed.
    # We need to reverse the winding order of triangles.
    # Indices for the triangle
    indices = mesh_data["triangles"]
    indices = [index for tri in [indices[i : i + 3][::-1] for i in range(0, len(indices), 3)] for index in tri]

    # Create an empty GLTF file
    gltf = GLTF2(asset={"version": "2.0"})

    # Create buffers
    # Pack data into binary using struct
    vertex_data = struct.pack("<" + "f" * len(vertices), *vertices)
    normal_data = struct.pack("<" + "f" * len(normals), *normals)
    uv_data = struct.pack("<" + "f" * len(uvs), *uvs)
    if len(vertices) // 3 > 0xFFFF:  # Check if any index exceeds the unsigned short range
        index_data = struct.pack("<" + "I" * len(indices), *indices)  # unsigned int
    else:
        index_data = struct.pack("<" + "H" * len(indices), *indices)  # unsigned short
    # Encode as base64
    vertex_buffer = Buffer(uri="data:application/octet-stream;base64," + b64encode(vertex_data).decode("ascii"))
    normal_buffer = Buffer(uri="data:application/octet-stream;base64," + b64encode(normal_data).decode("ascii"))
    uv_buffer = Buffer(uri="data:application/octet-stream;base64," + b64encode(uv_data).decode("ascii"))
    index_buffer = Buffer(uri="data:application/octet-stream;base64," + b64encode(index_data).decode("ascii"))

    gltf.buffers.extend([vertex_buffer, normal_buffer, uv_buffer, index_buffer])

    # Create buffer views
    vertex_buffer_view = BufferView(buffer=0, byteOffset=0, byteLength=len(vertex_data), target=34962)
    normal_buffer_view = BufferView(buffer=1, byteOffset=0, byteLength=len(normal_data), target=34962)
    uv_buffer_view = BufferView(buffer=2, byteOffset=0, byteLength=len(uv_data), target=34962)
    index_buffer_view = BufferView(buffer=3, byteOffset=0, byteLength=len(index_data), target=34963)

    gltf.bufferViews.extend([vertex_buffer_view, normal_buffer_view, uv_buffer_view, index_buffer_view])

    # Create accessors
    vertex_accessor = Accessor(bufferView=0, byteOffset=0, componentType=5126, count=len(vertices) // 3, type="VEC3")
    normal_accessor = Accessor(bufferView=1, byteOffset=0, componentType=5126, count=len(normals) // 3, type="VEC3")
    uv_accessor = Accessor(bufferView=2, byteOffset=0, componentType=5126, count=len(uvs) // 2, type="VEC2")
    if len(vertices) // 3 > 0xFFFF:
        index_accessor = Accessor(bufferView=3, byteOffset=0, componentType=5125, count=len(indices), type="SCALAR")  # unsigned int
    else:
        index_accessor = Accessor(bufferView=3, byteOffset=0, componentType=5123, count=len(indices), type="SCALAR")  # unsigned short

    gltf.accessors.extend([vertex_accessor, normal_accessor, uv_accessor, index_accessor])

    # Create images for the textures
    jpg2png = False

    # Load the JPEG image
    def create_gltf_image(path):
        if jpg2png:
            img = PILImage.open(path)
            # Convert the image to PNG format
            with io.BytesIO() as png_io:
                img.save(png_io, format="PNG")
                png_data = png_io.getvalue()

            # Encode the PNG image to base64
            encoded_img = b64encode(png_data).decode("ascii")
            return Image(uri="data:image/png;base64," + encoded_img)
        else:
            return Image(uri=path)

    # Encode the image to base64
    image_base_color = create_gltf_image(f"{asset_path}/albedo.jpg")
    image_normal = create_gltf_image(f"{asset_path}/normal.jpg")
    image_emission = create_gltf_image(f"{asset_path}/emission.jpg")
    gltf.images.extend([image_base_color, image_normal, image_emission])
    if not jpg2png:
        gltf.convert_images(ImageFormat.DATAURI)

    # Create textures that use the images
    texture_base_color = Texture(source=0)
    texture_normal = Texture(source=1)
    texture_emission = Texture(source=2)

    gltf.textures.extend([texture_base_color, texture_normal, texture_emission])

    # Create a material that uses the texture
    material = Material(pbrMetallicRoughness=PbrMetallicRoughness(baseColorTexture=TextureInfo(index=0), metallicFactor=0, roughnessFactor=1), normalTexture=TextureInfo(index=1), emissiveTexture=TextureInfo(index=2), emissiveFactor=[1.0, 1.0, 1.0])
    gltf.materials.append(material)

    # Create a mesh that uses the material
    # https://github.com/KhronosGroup/glTF-Tutorials/blob/main/gltfTutorial/gltfTutorial_009_Meshes.md#indexed-and-non-indexed-geometry
    mesh = Mesh(primitives=[Primitive(attributes={"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, indices=3, material=0)])
    gltf.meshes.append(mesh)

    # Create a scene with one node that references the mesh
    node = Node(mesh=0)
    gltf.nodes.append(node)
    scene = Scene(nodes=[0])
    gltf.scenes.append(scene)

    # Set the default scene
    gltf.scene = 0

    # Save the GLTF file to disk
    gltf.save(output_file)


def convert_crm_obj_to_gltf(input_file, output_file):
    # Load an OBJ file
    mesh = trimesh.load(input_file)

    # Export to GLTF
    mesh.export(output_file, file_type="gltf")

    glb = GLTF2().load(output_file)
    for material in glb.materials:
        material.pbrMetallicRoughness.metallicFactor = 0
        material.pbrMetallicRoughness.roughnessFactor = 1

    glb.save(output_file)


env = Environment(env_path=None)

try:

    def build_scene_with_custom_objects():
        scene = generate_scene(room_num=1)

        # NOTE: Here we convert the assets in runtime. However, it is recommended to convert the assets beforehand and use the converted assets directly.

        # ================== Example of using generated assets ==================
        # Download the generated example from https://drive.google.com/file/d/1do5HyqUjEC76Rqg8ZSz0l8wgqHhbhUxP/view?usp=sharing
        # Or generate the assets using the CRM model from https://github.com/thu-ml/CRM
        # TODO: Change this to the path of the generated OBJ file
        crm_generated_obj = "path/to/crm/generated/xxx.obj"

        convert_crm_obj_to_gltf(crm_generated_obj, "crm_example.gltf")

        # Add CRM generated example
        asset = os.path.abspath("crm_example.gltf")
        asset_size = get_mesh_size(asset)
        asset_y_size = asset_size[1]
        scene["instances"].append({"prefab": asset, "position": [2, asset_y_size / 2, 1], "rotation": [0, 0, 0], "scale": [0.1, 0.1, 0.1], "type": "interactable"})

        # ================== Example of using Holodeck assets ==================
        # Download from https://drive.google.com/file/d/1MQbFbNfTz94x8Pxfkgbohz4l46O5e3G1/view?usp=sharing
        # TODO: Change this to the path of the Holodeck data folder
        holodeck_data_path = "path/to/holodeck_data/data/objaverse_holodeck/09_23_combine_scale/processed_2023_09_23_combine_scale"

        # Some example uids:
        # cd956b2abec04b52ac48bea1ec141d60  modern bed
        # 000a0c5cdc3146ea87485993fbaf5352  statue
        # 493cf761ada14c0bbc1f5b71369d8d93  sofa
        # 7c6aa7d97a8443ce8fdd01bdc5ec9f15  table
        # 20de33c317ce49a687b9fe8075d60e8a  TV
        # TODO: Change this to the uid of the Holodeck object you want to import
        uid = "000a0c5cdc3146ea87485993fbaf5352"

        convert_holodeck_asset_to_gltf(f"{holodeck_data_path}/{uid}", f"holodeck_example.gltf")

        # Add Holodeck example
        asset = os.path.abspath("holodeck_example.gltf")
        asset_size = get_mesh_size(asset)
        scale = 1  # max(uid2size[uid] / asset_size)  # scale the size to the annotated size
        y_size = asset_size[1] * scale
        scene["instances"].append({"prefab": asset, "position": [2, y_size / 2, 3], "rotation": [0, 0, 0], "scale": [scale, scale, scale], "type": "kinematic"})

        # Add Objaverse example. Orignal version of the Holodeck example.
        ori = objaverse_object(uid)
        ori_size = get_mesh_size(ori)
        scale = y_size / ori_size[1]
        y_size = ori_size[1] * scale
        scene["instances"].append({"prefab": ori, "position": [2, y_size / 2, 5], "rotation": [0, 0, 0], "scale": [scale, scale, scale], "type": "kinematic"})

        return scene

    obs: Observation = env.reset(ResetInfo(build_scene_with_custom_objects()))
    while True:
        if obs.text == "#RESET":
            scene = build_scene_with_custom_objects()
            env.reset(ResetInfo(scene))
        obs = env.step()
finally:
    env.close()
