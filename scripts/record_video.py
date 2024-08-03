from legent import Environment, Action, ResetInfo, generate_scene, time_string
from legent.action.api import TakePhoto
from legent.utils.math import look_at_xz
import numpy as np
import os
import imageio
import math


env = Environment(env_path="auto", camera_resolution_width=1024, camera_field_of_view=60, action_mode=0, rendering_options={"use_default_light": 0, "style": 0, "background": 0})
try:
    scene = generate_scene()
    env.reset(ResetInfo(scene))

    path = f"scene_video/{time_string()}"  # Video save path
    os.makedirs(path, exist_ok=True)
    images = [os.path.join(path, img) for img in os.listdir(path) if img.endswith(".png")]
    [os.remove(image) for image in images]

    center = np.array([5, 0, 5])  # Scene center, around which the camera rotates
    radius = 15  # Radius of the camera around the center (larger radius makes the room appear smaller)
    camera_height = 5  # Camera height
    look_down_angle = 30  # Camera's downward viewing angle

    time = 3  # Rotation time (time for one complete rotation of the room)
    fps = 12  # Frame rate

    num_photos = fps * time
    step_angle = 360 / num_photos

    def rotate_camera(center, radius):
        for i in range(num_photos):
            print(i)
            angle = (i + 1) * step_angle
            camera_position = np.array([center[0] + radius * math.sin(angle / 180 * math.pi), center[1] + camera_height, center[2] + radius * math.cos(angle / 180 * math.pi)])
            camera_rotation = np.array([look_down_angle, look_at_xz(camera_position, center), 0])

            action = Action()
            action.api_calls = [TakePhoto(os.path.abspath(f"{path}/frame{i:04d}.png"), camera_position.tolist(), camera_rotation.tolist(), 512, 512)]
            env.step(action)

    rotate_camera(center, radius)

    def create_video(image_folder, output_path, fps):
        images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
        images.sort()

        writer = imageio.get_writer(output_path, fps=fps, codec="libx264")
        for image_name in images:
            image_path = os.path.join(image_folder, image_name)
            image = imageio.imread(image_path)
            writer.append_data(image)
        writer.close()

    create_video(path, f"{path}/video.mp4", fps=fps)
except Exception as e:
    print(e)
    env.close()
    raise
finally:
    env.close()
