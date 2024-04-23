# Action Space

Actions can generally be divided into planning and control. Some environments offer actions like `goto(object)`, which belong to planning. Planning actions cannot operate in unannotated scenes. The potential of control actions is significantly greater, both in terms of operational capability and generalization ability. LEGENT adopts control actions. However, LEGENT currently does not employ real robot controls, which theoretically would require precise control of each joint's rotation and more, making it overly complex for researchers not working with physical robots. While ensuring that the action is a control type, we have also simplified the control difficulty as much as possible.

Below is the actions of an agent. Note that, along with basic move-forward action (equivalent to pressing the forward key on the keyboard), LEGENT also supports moving forward over any distance immediately (`teleport_forward`). During the continuous move-forward process, the information increment in repeatedly "move forward, move forward, move forward" is very small. This is not a great issue for small models. However, in cases where the computation cost is significantly high for large models during training, using the 'move forward with a distance' can greatly increase the information of the samples. When deployed for use, the model infers the distance to move forward, allowing to wait until this distance is covered before performing the next inference, effectively avoiding the huge overhead brought by inferring every frame. This action design is firstly employed by LEGENT, as a platform aimed at large models.

| Action           | Descriptions                   | Details                                                                                                                                                                         |
| ---------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| text             | text send to the player        | string.<br> If it is empty, it means nothing to sent.                                                                                                                           |
| move_forward     | move forward in the next frame | bool. If True, go forward. When `use_teleport==False`, it becomes effective.                                                                                                    |
| teleport_forward | move forward with a distance   | float. The number of meters to travel forward. When `use_teleport==True`, it becomes effective.                                                                                 |
| rotate_right     | rotate camera horizontally     | float. [-180, 180). Positive value means rotating right. Negative values mean rotating left                                                                                     |
| rotate_down      | rotate camera vertically       | float. [-90, 90). Positive value means rotating downwards. Negative values mean rotating upwards                                                                                |
| grab             | grab                           | bool. If True and the agent is holding an object, grab the object at the center of the image. If True and not holding, put the object on the surface at the center of the image |
| api_calls        | api calls to the environment   | List[Callable]. The api returns will be put in the returned observations.                                                                                                       |

The types of these actions vary, but they are all expressed by codes for the model. For example:
``` python
speak("OK")
move_forward(2.4)
rotate_right(35)
```

Below is the APIs provided to python by the environment.

| API          | Descriptions                                                                                                                                                                 | Params                                      | Returns                                           |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------- |
| PathToUser   | Obtain the key points of the path to walk towards the player. The agent can walk to the player along the key points one by one in straight line without barriers in between. | None                                        | api_returns['corners'] is the list of key points. |
| PathToObject | Obtain the key points of the path to walk towards an object.                                                                                                                 | The index of the object in the scene config | api_returns['corners'] is the list of key points. |