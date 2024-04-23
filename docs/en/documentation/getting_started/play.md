# Play

## Start the Environment Client

### in one command (recommended)

```
legent launch --use_default_scene
```

This command will launch the latest client in the .legent/client folder. If you want to launch a specific client, run:

```
legent launch --env_path <path-to-the-client>  --use_default_scene
```

By default, a predefined 3D scene is displayed, where you and a robot agent are positioned in a first-person view.

### step by step manually

The scenes in LEGENT are all generated on the Python side. The client side obtains scenes by requesting the scene server (or using `legent.Environment` in the toolkit).
Start the scene generator by running:

```
legent serve
```

To start the client, simply open it like any regular software. For example, by double-clicking the executable file.

Or enter the following command in the console:
``` bash
"<path-to-the-executable-file>" --width <screen-width> --height <screen-height>
```


## Manual Controll

### character controll

Move the mouse to rotate the perspective.<br>
Press W, A, S, D to move the character.<br>
Press G or left mouse button to grab/release an object.<br>
Press Enter to chat.

### view controll

Press C to switch between the first-person-view and the third-person-view.<br>
Press V to switch between your view, the agent's view, and a panoramic top-down view.<br>
Press X to switch between full screen and windowed screen.<br>
Press Esc to unfocus the game client.

Currently the robot will not have any response. Next, we will use the Python side to [control the robot](/documentation/environment/basic_usage/).
