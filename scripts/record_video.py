from legent import Environment, Action, ResetInfo, generate_scene, time_string
from legent.action.api import TakePhoto
from legent.utils.math import look_at_xz
import numpy as np
import os
import math


env = Environment(env_path="auto", camera_resolution_width=1024, camera_field_of_view=60, action_mode=0, rendering_options={"use_default_light": 1, "style": 0, "background": 0})
try:
    scene = generate_scene()
    env.reset(ResetInfo(scene))

    path = f"scene_video/{time_string()}"  # Video save path
    os.makedirs(path, exist_ok=True)
    images = [os.path.join(path, img) for img in os.listdir(path) if img.endswith(".png")]
    [os.remove(image) for image in images]

    radius = 10  # Radius of the camera around the center (larger radius makes the scene appear smaller)
    look_down_angle = 45  # Camera's downward viewing angle

    center = np.array([scene["center"][0], 0, scene["center"][2]])  # Scene center, around which the camera rotates
    camera_height = np.tan(look_down_angle / 180 * math.pi) * radius

    time = 3  # Rotation time (time for one complete rotation of the room)
    fps = 12  # Frame rate
    resolution = 1024  # Image resolution

    num_photos = fps * time
    step_angle = 360 / num_photos

    def rotate_camera(center, radius):
        for i in range(num_photos):
            print(i)
            angle = (i + 1) * step_angle
            camera_position = np.array([center[0] + radius * math.sin(angle / 180 * math.pi), center[1] + camera_height, center[2] + radius * math.cos(angle / 180 * math.pi)])
            camera_rotation = np.array([look_down_angle, look_at_xz(camera_position, center), 0])

            action = Action()
            action.api_calls = [TakePhoto(os.path.abspath(f"{path}/frame{i:04d}.png"), camera_position.tolist(), camera_rotation.tolist(), resolution, resolution, 60)]
            env.step(action)

    rotate_camera(center, radius)

    def create_video(image_folder, output_path, fps):
        # !pip install moviepy
        from moviepy.editor import ImageSequenceClip
        import os

        image_files = [img for img in os.listdir(image_folder) if img.endswith(".png")]
        image_files.sort()

        image_paths = [os.path.join(image_folder, img) for img in image_files]
        clip = ImageSequenceClip(image_paths, fps=fps)
        clip.write_videofile(output_path, codec="libx264")

    create_video(path, f"{path}/video.mp4", fps=fps)
except Exception as e:
    print(e)
    env.close()
    raise
finally:
    env.close()
