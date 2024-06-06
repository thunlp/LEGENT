from legent import Environment, Observation, generate_scene, ResetInfo

env = Environment(env_path="auto", rendering_options={"style": 0})
try:

    def build_scene_with_skybox():
        scene = generate_scene(room_num=1)
        
        # Remove all walls
        instance = []
        for i in scene["instances"]:
            if "wall" in i["prefab"].lower():
                continue
            instance.append(i)
        scene["instances"] = instance
        
        # Change the skybox
        # Download the image from https://sketchfab.com/3d-models/free-skybox-sunroof-in-the-city-6ce2eb7cb56f4efaa4212c2fc37099b2#download
        #   or https://drive.google.com/file/d/1p1GU7hb88PPTHrLYMo1elNRXSPQLchdF/view?usp=sharing
        # TODO: Change this to the absolute path of the downloaded image file
        path_to_skybox = "F:/Downloads/free-skybox-sunroof-in-the-city/textures/sunroof_city_6k.jpg"
        scene["skybox"] = {
            "map":path_to_skybox,
            "color": "#FFFFFF",
            "exposure": 0.6,
            "rotation": 0
        }
        return scene

    obs: Observation = env.reset(ResetInfo(build_scene_with_skybox()))
    while True:
        if obs.text == "#RESET":
            env.reset(ResetInfo(build_scene_with_skybox()))
        obs = env.step()
finally:
    env.close()
