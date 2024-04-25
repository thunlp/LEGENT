import trimesh


def get_mesh_size(file_path):
    """Get the bounding box of a mesh file.
    Args:
        file_path: str, the path of the mesh file.
    Returns:
        mesh_size: np.ndarray, the size of the mesh file.
    """
    mesh = trimesh.load(file_path)
    min_vals, max_vals = mesh.bounds[0], mesh.bounds[1]
    return max_vals - min_vals


def get_mesh_vertical_size(file_path):
    """Get the vertical size of a mesh file.
    Args:
        file_path: str, the path of the mesh file.
    Returns:
        vertical_size: float, the vertical size of the mesh file.
    """
    mesh_size = get_mesh_size(file_path)
    return mesh_size[1]
