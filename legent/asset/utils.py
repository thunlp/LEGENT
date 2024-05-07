import trimesh
from pygltflib import GLTF2


def get_mesh_size(input_file):
    """Get the bounding box of a mesh file.
    Args:
        input_file: str, the path of the mesh file.
    Returns:
        mesh_size: np.ndarray, the size of the mesh file.
    """
    mesh = trimesh.load(input_file)
    min_vals, max_vals = mesh.bounds[0], mesh.bounds[1]
    return max_vals - min_vals


def get_mesh_vertical_size(input_file):
    """Get the vertical size of a mesh file.
    Args:
        input_file: str, the path of the mesh file.
    Returns:
        vertical_size: float, the vertical size of the mesh file.
    """
    mesh_size = get_mesh_size(input_file)
    return mesh_size[1]


def get_mesh_colliders(input_file):
    import coacd

    mesh = trimesh.load(input_file, force="mesh")
    mesh = coacd.Mesh(mesh.vertices, mesh.faces)
    parts = coacd.run_coacd(mesh)  # a list of convex hulls.
    return parts


def convert_obj_to_gltf(input_file, output_file):
    # Load an OBJ file
    mesh = trimesh.load(input_file)

    # Export to GLTF
    mesh.export(output_file, file_type="gltf")

    glb = GLTF2().load(output_file)
    for material in glb.materials:
        material.pbrMetallicRoughness.metallicFactor = 0
        material.pbrMetallicRoughness.roughnessFactor = 1

    glb.save(output_file)
