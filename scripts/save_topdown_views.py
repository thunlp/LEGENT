from legent import Environment, ResetInfo, generate_scene, SaveTopDownView
import os

save_folder = f'{os.getcwd()}/topdown_views'
os.makedirs(save_folder, exist_ok=True)

env = Environment(env_path="auto", camera_resolution=1024, camera_field_of_view=120)

try:
    for i in range(10):
        absolute_path = f'{save_folder}/{i:04d}.png'
        print(f"save scene {i} to {absolute_path}")
        scene=generate_scene()
        
        # Adjust top down camera
        scene['center'][1] -= 3 # y camera move downward
        scene['center'][2] -= 8 # z camera move backward
        scene['center_rotation'] = [45, 0, 0] # rotate down 45 degrees
        
        obs = env.reset(ResetInfo(scene, api_calls=[SaveTopDownView(absolute_path=absolute_path)]))

        # If you want to interact with the scene, uncomment the following codes.
        # while True:
        #     if obs.text == "#RESET":
        #         env.reset(ResetInfo(scene=generate_scene()))
        #     obs = env.step()
finally:
    env.close()

