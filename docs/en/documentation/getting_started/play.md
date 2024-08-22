# Play

## Start the Environment Client

### in one command (recommended)

```
legent launch --scene 0
```

This command will launch the latest client in the .legent/env/client folder. If you want to launch a specific client, run:

```
legent launch --env_path <path-to-the-client>  --scene 0
```

A predefined 3D scene will be displayed, where you and a robot agent are positioned in a first-person view.

??? note "A reminder for Windows users"

    If you're using a Windows computer with a VPN enabled, please disable it. Otherwise, the client cannot get the scene file from the launched scene server. We'll investigate this issue further in future updates.

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


## Default Scenes

Currently, LEGENT has two default scenes: 0 (stylized) and 1 (realistic). You can use these scenes by running `legent launch --scene 0` or legent `launch --scene 1` respectively.