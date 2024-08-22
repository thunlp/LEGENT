from legent import Environment, Observation, generate_scene, ResetInfo

env = Environment(env_path=None)
try:

    def build_scene_with_lights():
        scene = generate_scene(room_num=1)

        scene["walls"] = []
        scene["lights"] = []
        
        # Example 1: Add a spot light
        light_position = [5, 3, 4]
        light_rotation = [90, 0, 0]
        # (Optional) Add a square object on the ceiling to represent the light
        scene["walls"].append(
            {"position": light_position, "rotation": light_rotation, "size": [0.8, 0.8, 0.01], "material": "Light"}
        )
        # Add the light source
        scene["lights"].append(
            {
                "name": "SpotLight0",
                "lightType": "Spot",  # Point, Spot, Directional
                "position": light_position,
                "rotation": light_rotation,
                "spotAngle": 180.0,
                "useColorTemperature": True,
                "colorTemperature": 5500.0,
                "color": [1.0, 1.0, 1.0],
                "intensity": 15,  # brightness
                "range": 15,
                "shadowType": "None",  # Hard, Soft, None
            }
        )
        
        # Example 2: Add a point light
        light_position = [2, 2, 2]
        light_rotation = [90, 0, 0]
        scene["walls"].append(
            {"position": light_position, "rotation": light_rotation, "size": [0.1, 0.1, 0.1], "material": "Light"}
        )
        scene["lights"].append(
            {
                "name": "PointLight0",
                "lightType": "Point",
                "position": light_position,
                "rotation": light_rotation,
                "useColorTemperature": True,
                "colorTemperature": 5500.0,
                "color": [1.0, 1.0, 1.0],
                "intensity": 1,  # brightness
                "range": 15,
                "shadowType": "Soft",
            }
        )
        
        return scene

    obs: Observation = env.reset(ResetInfo(build_scene_with_lights()))
    while True:
        if obs.text == "#RESET":
            env.reset(ResetInfo(build_scene_with_lights()))
        obs = env.step()
finally:
    env.close()
