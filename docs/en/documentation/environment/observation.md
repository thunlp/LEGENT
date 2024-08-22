# Observation Space

Below is the observations of an agent.

| Observation | Descriptions                                                    | Details                                                                                                                                                                         |
| ----------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| image       | the egocentric view of the agent                                | `camera_resolution_width`*`camera_resolution_height` numpy array                                                                           |
| text        | the text received by the agent (i.e. what the player just send) | string.<br /> If it is empty, it means nothing has been sent by the user. Note that the environment does not maintain a chat history. If needed, it should be recorded by the agent itself. |

You are only allowed to use image and chat as input for your agents. This is necessary to ensure the generalizability of the agent. However, during training or data generation you are allowed to use additional info from the environment. This information is returned along with the observation, with the content as follows.

| Observation | Descriptions                                    | Details            |
| ----------- | ----------------------------------------------- | ------------------ |
| game_states | all the game inner states                       | json object(Dict). |
| api_returns | the returns of the api_calls in the last action | json object(Dict). |

Below is the explanation for each field in game_states.

| Key                | Descriptions                                                                      | Details                                                                                                                                                                                                         |
| ------------------ | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| instances          | the information of all objects                                                    | `obs['instances'][i]['prefab'`] is the prefab name of the object.<br> `obs['instances'][i]['position']` is the position of the object.<br> `obs['instances'][i]['forward']` the direction the object is facing. |
| player             | the information of the player                                                     | `obs['player']['position']` is the position of the player.<br> `obs['player']['forward']` the direction the player is facing.                                                                                   |
| agent              | the information of the agent                                                      | `obs['agent']['position']` is the position of the agent.<br> `obs['agent']['forward']` the direction the agent is facing                                                                                  |
| player_camera       | The position of the player's camera, from which the egocentric image is obtained. | `obs['player_camera']['position']` is the position of the camera.<br> `obs['player_camera']['forward']` the direction the camera is facing.                                                                       |
| agent_camera        | The position of the agent's camera, from which the egocentric image is obtained.  | `obs['agent_camera']['position']` is the position of the camera.<br> `obs['agent_camera']['forward']` the direction the camera is facing.                                                                         |
| player_grab_instance | The index of the object that the player has grabbed.                              | `"player_grab_instance": i` means instances[i] is grabbed.                                                                                                                                                        |
| agent_grab_instance  | The index of the object that the agent has grabbed.                               | `"agent_grab_instance": i` means instances[i] is grabbed.                                                                                                                                                         |

This information is useful, for instance, for spatial calculations, determining task completion, or calculating rewards.
