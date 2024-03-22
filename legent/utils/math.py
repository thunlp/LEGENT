import numpy as np
from scipy.spatial.transform import Rotation
from typing import Dict


def vec_xz(position: Dict):
    return np.array([position['x'], position['z']])


def vec(position: Dict):
    return np.array([position['x'], position['y'], position['z']])


def normalize(v: np.ndarray):
    magnitude = np.linalg.norm(v)
    # Check if the magnitude is zero to avoid division by zero
    if magnitude == 0:
        return v
    # Normalize the vector
    return v / magnitude


def compute_signed_angle_2d_dir(v_source: np.ndarray, v_target: np.ndarray) -> float:
    """Compute angle between two 2D directions

    Args:
        v_source (np.ndarray): source 2D direction
        v_target (np.ndarray): target 2D direction

    Returns:
        float: degree to rotate to right from source direction to target direction
    """
    if len(v_source) == 3:
        v_source = [v_source[0], v_source[2]]
    if len(v_target) == 3:
        v_target = [v_target[0], v_target[2]]
    v1, v2 = normalize(v_target), normalize(v_source)
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    cross_product = v1[0] * v2[1] - v1[1] * v2[0]
    angle = np.arctan2(cross_product, dot_product)
    degree = angle / np.pi * 180  # degrees to rotate to right
    return degree


def compute_angle_to_y_axis(v: np.ndarray) -> float:
    """Compute angle between a 3D direction and the positive direction of the y-axis

    Args:
        v (np.ndarray): 3D direction

    Returns:
        float: degree bewteen v and the positive direction of the y-axis, ranging from [0, 180]
    """
    v = normalize(v)
    angle = np.arccos(v[1] / 1.0)
    degree = angle / np.pi * 180
    return degree


def compute_angle_to_y_axis_diff(v_source: np.ndarray, v_target: np.ndarray) -> float:
    """Compute angle difference between 3D directions relative to the y-axis

    Args:
        v_source (np.ndarray): source 3D direction
        v_target (np.ndarray): target 3D direction

    Returns:
        float: degree to rotate downwards from source direction to target direction
    """
    return compute_angle_to_y_axis(v_target) - compute_angle_to_y_axis(v_source)


def clip_angle(angle, max_degree):
    if angle > max_degree:
        angle = max_degree
    elif angle < -max_degree:
        angle = -max_degree
    return angle


def distance(v1: np.ndarray, v2: np.ndarray) -> float:
    return float(np.linalg.norm(v1 - v2))


def convert_euler_angles(y0):
    """
    Convert euler angles from [180, y0, 180] to [0, y1, 0].
    For example, [180, 30, 180] and [0, 120, 0] are the same in the game.
    """
    y1 = 180 - y0
    y1 = y1 % 360  # Ensuring the angle is within the range [0, 360)
    return y1


def foward_to_rotation_matrix(forward_vector):
    forward_vector = forward_vector / np.linalg.norm(forward_vector)
    up_vector = np.array([0, 1, 0])
    right_vector = normalize(np.cross(up_vector, forward_vector))
    up_vector = normalize(np.cross(forward_vector, right_vector))

    rotation_matrix = np.column_stack((right_vector, up_vector, forward_vector))  # np.array([right_vector, up_vector, forward_vector]).T
    return rotation_matrix

# Creates a rotation with the specified forward and upwards directions


def look_rotation(forward_vector):
    r = Rotation.from_matrix(foward_to_rotation_matrix(forward_vector))
    r = r.as_euler('xyz', degrees=True)
    if r[0] != 0 and r[2] != 0:
        r[1] = convert_euler_angles(r[1])
    return r


def is_point_on_box(point, box_center, box_size, box_forward=None, box_rotation=None):
    # Calculate the position of the point relative to the center of the box
    relative_point = point - box_center

    if box_rotation:
        rotation = Rotation.from_euler('xyz', box_rotation, degrees=True)
    else:
        rotation = Rotation.from_matrix(foward_to_rotation_matrix(box_forward))

    # Transform the position of the point relative to the box center to the box's local coordinate system
    point_local = rotation.inv().apply(relative_point)

    # Check if the transformed point position is within the boundaries of the box
    # Only x and z coordinates are checked because we are interested in the projection on the xz plane
    half_size = box_size / 2

    xz_inner = all(-half_size[i] <= point_local[i] <= half_size[i] for i in [0, 2])
    y_higher = point_local[1] > half_size[1]
    return xz_inner and y_higher
