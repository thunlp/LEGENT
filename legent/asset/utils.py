def get_mesh_size(input_file, visualize=False):
    """Get the bounding box of a mesh file.
    Args:
        input_file: str, the path of the mesh file.
    Returns:
        mesh_size: np.ndarray, the size of the mesh file.
    """

    import trimesh

    mesh = trimesh.load(input_file)
    min_vals, max_vals = mesh.bounds[0], mesh.bounds[1]

    def show_bbox(bounding_box):
        bbox = bounding_box
        bbox.visual.face_colors = [1, 0, 0, 0.3]
        bbox.visual.edge_colors = [0, 0, 1, 0.8]
        scene = trimesh.Scene([mesh, bbox])
        scene.show()

    if visualize:
        show_bbox(bounding_box=mesh.bounding_box)

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

    import trimesh
    import coacd

    mesh = trimesh.load(input_file, force="mesh")
    mesh = coacd.Mesh(mesh.vertices, mesh.faces)
    parts = coacd.run_coacd(mesh)  # a list of convex hulls.
    return parts


def convert_obj_to_gltf(input_file, output_file):

    import trimesh
    from pygltflib import GLTF2

    # Load an OBJ file
    mesh = trimesh.load(input_file)

    # Export to GLTF
    mesh.export(output_file, file_type="glb")

    glb = GLTF2().load(output_file)
    for material in glb.materials:
        material.pbrMetallicRoughness.metallicFactor = 0
        material.pbrMetallicRoughness.roughnessFactor = 1

    glb.save(output_file)


def get_placable_surface(input_file, size_is_correct, visualize):
    # Uniformly emit rays downward to obtain a set of intersection points. The set of intersection points on the same horizontal plane forms a placable surface.
    import trimesh
    import numpy as np

    scene_or_mesh = trimesh.load_mesh(input_file)
    # Ensure it is a mesh by converting if it's a scene
    if isinstance(scene_or_mesh, trimesh.Scene):
        # This combines all meshes in the scene into a single mesh
        mesh = scene_or_mesh.dump(concatenate=True)
    else:
        mesh = scene_or_mesh

    vis_scene = trimesh.Scene()
    vis_scene.add_geometry(mesh)

    def add_vis_points(points, point_scale=1, color=[0, 0, 255, 255]):

        for pos in points:
            sphere = trimesh.creation.icosphere(subdivisions=3, radius=(mesh.bounds[1][0] - mesh.bounds[0][0]) / 100 * point_scale)
            sphere.visual.vertex_colors = color
            vis_scene.add_geometry(sphere)
            transformation_matrix = trimesh.transformations.translation_matrix(pos)
            sphere.apply_transform(transformation_matrix)

    # Get the bounds.
    # Add a small offset to the bounds to prevent the issue where rays at the edges tangent to objects do not have intersection points.
    # mesh.bounds = [min_x, min_y, min_z] [max_x, max_y, max_z]
    bounds_min_x = mesh.bounds[0][0] + 0.01
    bounds_max_x = mesh.bounds[1][0] - 0.01
    bounds_min_z = mesh.bounds[0][2] + 0.01
    bounds_max_z = mesh.bounds[1][2] - 0.01

    if size_is_correct:
        # Shoot a ray every 0.05 meters.
        density = 0.05
        rays_x = int((mesh.bounds[1][0] - mesh.bounds[0][0]) / density)  # Number of rays in the X-axis direction
        rays_z = int((mesh.bounds[1][2] - mesh.bounds[0][2]) / density)  # Number of rays in the Z-axis direction
        rays_x = max(min(rays_x, 20), 2)
        rays_z = max(min(rays_z, 20), 2)
    else:
        rays_x = 20
        rays_z = 20

    def ij_to_pos(i, j):
        x = bounds_min_x + (bounds_max_x - bounds_min_x) * i / (rays_x - 1)
        z = bounds_min_z + (bounds_max_z - bounds_min_z) * j / (rays_z - 1)
        return x, z

    # STEP 1: Emit rays downward (perpendicular to the xz plane).
    is_hit = np.zeros((rays_x, rays_z), dtype=int)  # Initialize to 0, indicating no hit.
    hit_y = np.zeros((rays_x, rays_z))  # The y-coordinate of the hit point.

    for i in range(rays_x):
        for j in range(rays_z):
            x, z = ij_to_pos(i, j)
            # Start emitting from 0.3 meters above the bounding box.
            ray_origin = np.array([x, mesh.bounds[1][1] + 0.3, z])

            def ray_cast(ray_origin, ray_direction):
                ray_origins = np.array([ray_origin])
                ray_directions = np.array([ray_direction])

                # https://github.com/mikedh/trimesh/blob/7853a5ebae3b35275f4d8d65cbc48bcd3a3c8a40/trimesh/ray/ray_pyembree.py#L83
                locations, index_ray, index_tri = mesh.ray.intersects_location(ray_origins=ray_origins, ray_directions=ray_directions)

                if len(locations) > 0:
                    # Find the index of the maximum y-value
                    max_y_index = np.argmax(locations[:, 1])
                    # Get the maximum y-value
                    max_y_value = locations[max_y_index][1]
                    return True, max_y_value
                else:
                    return False, 0

            hit, point_y = ray_cast(ray_origin, np.array([0, -1, 0]))
            if hit:
                is_hit[i, j] = 1
                hit_y[i, j] = point_y

    if visualize:
        points = []
        for i in range(rays_x):
            for j in range(rays_z):
                if is_hit[i, j]:
                    p = ij_to_pos(i, j)
                    points.append([p[0], hit_y[i][j], p[1]])
        add_vis_points(points, point_scale=1, color=[0, 0, 255, 255])

    same_plane_eps = (mesh.bounds[1][0] - mesh.bounds[0][0]) / 100

    def find_most_points_on_same_y():
        planes = []  # planes[plane_i] is the i, j coordinates of all points on the plane

        for i in range(rays_x):
            for j in range(rays_z):
                if is_hit[i, j] != 1:
                    continue

                # Check if the point can be incorporated into an existing plane
                for plane_points in planes:
                    if abs(hit_y[plane_points[0][0], plane_points[0][1]] - hit_y[i, j]) <= same_plane_eps:
                        plane_points.append((i, j))
                        break
                else:
                    # If the point cannot be incorporated into any existing plane, create a new plane.
                    planes.append([(i, j)])

        # Find the group with the most points.
        if not planes:
            return []
        placeable_points = max(planes, key=len)

        # Check if there is a protrusion in the middle of the plane.
        bounds_min_i, bounds_max_i = min(i for i, _ in placeable_points), max(i for i, _ in placeable_points)
        bounds_min_j, bounds_max_j = min(j for _, j in placeable_points), max(j for _, j in placeable_points)
        placeable_y = hit_y[placeable_points[0][0], placeable_points[0][1]]
        for i in range(bounds_min_i, bounds_max_i + 1):
            for j in range(bounds_min_j, bounds_max_j + 1):
                if placeable_y - hit_y[i, j] > same_plane_eps * 2:
                    return []

        if len(placeable_points) < 16:
            return []

        return placeable_points

    placeable_points = find_most_points_on_same_y()

    if visualize:
        points = []
        for i, j in placeable_points:
            p = ij_to_pos(i, j)
            points.append([p[0], hit_y[i][j], p[1]])
        add_vis_points(points, point_scale=1.2, color=[0, 255, 0, 255])

    # If a plane with sufficient points is found, determine the largest rectangular area on this plane.
    placeable_rects = []

    for i, j in placeable_points:
        if is_hit[i, j] != 1:
            continue

        # Initialize boundaries for the rectangle
        i_min, i_max = i, i
        j_min, j_max = j, j
        # Expand the rectangle as far as possible
        expanding = True
        while expanding:
            expanding = False

            # Expand to the top
            if i_min > 0 and all(is_hit[i_min - 1, k] == 1 for k in range(j_min, j_max + 1)):
                i_min -= 1
                expanding = True
            # Expand to the right
            if i_max < rays_x - 1 and all(is_hit[i_max + 1, k] == 1 for k in range(j_min, j_max + 1)):
                i_max += 1
                expanding = True
            # Expand to the top
            if j_min > 0 and all(is_hit[k, j_min - 1] == 1 for k in range(i_min, i_max + 1)):
                j_min -= 1
                expanding = True
            # Expand to the bottom
            if j_max < rays_z - 1 and all(is_hit[k, j_max + 1] == 1 for k in range(i_min, i_max + 1)):
                j_max += 1
                expanding = True

        # After the rectangle is formed, set the included points to a value that marks them as processed.
        for ii in range(i_min, i_max + 1):
            for jj in range(j_min, j_max + 1):
                is_hit[ii, jj] = 2

        # The y-coordinate of the placement surface
        y = hit_y[i, j]
        # The placeable rectangular plane on y (relative to the mesh's center)
        x_min, z_min = ij_to_pos(i_min, j_min)
        x_max, z_max = ij_to_pos(i_max, j_max)

        # Check if the rectangle is large enough to be considered placeable
        if x_max - x_min > 0.15 and z_max - z_min > 0.15:
            center_x = (mesh.bounds[1][0] + mesh.bounds[0][0]) / 2
            center_y = (mesh.bounds[1][1] + mesh.bounds[0][1]) / 2
            center_z = (mesh.bounds[1][2] + mesh.bounds[0][2]) / 2

            placeable_rects.append({"y": y - center_y, "x_min": x_min - center_x, "z_min": z_min - center_z, "x_max": x_max - center_x, "z_max": z_max - center_z})  # adjust Y relative to the mesh's center

    if visualize:
        vis_scene.show()

    return placeable_rects
