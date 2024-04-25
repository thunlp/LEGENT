floor_plan_prompt = """You are an experienced interior designer. Please assist me in crafting a floor plan of a house. Each room is a rectangle, and you need to define the four coordinates.
Note: the units for the coordinates are meters.
Example output:
living room | [(0, 0), (0, 8), (5, 8), (5, 0)]
kitchen | [(5, 0), (5, 5), (8, 5), (8, 0)]

Here are some guidelines for you:
1. A room's size range (length or width) is 2.5m to 8m. The maximum area of a room is 48 m$^2$. Please provide a floor plan within this range and ensure the room is not too small or too large.
2. It is okay to have one room in the floor plan if you think it is reasonable.
3. The room name should be unique.
4. Please ensure that all rooms are connected, not overlapped, and do not contain each other.
5. Try to make your output different and unique, but adhere to the commen sense of what a house floor plan would be like.

Now, I need a design for {input}.
Additional requirements: {additional_requirements}.
Your response should be direct and without additional text at the beginning or end."""


doorway_prompt = """I need assistance in designing the connections between rooms. The connections could be of three types: doorframe (no door installed), doorway (with a door), or open (no wall separating rooms). 
The output format should be: room 1 | room 2 | wall vertices | connection type. 

Note:
1. There should be at least one door to exterior so that people can go in and out of the house.
2. Ensure that your output is distinctive and original, while maintaining the common sense of where a door would conventionally be situated.


Example output:
exterior | living room | (0,0), (0,8) | doorway
living room | kitchen | (5,0), (5,3) | open

Necessary information of each room:
The design under consideration is {input}. Here are the vertices that can place doors between rooms (including exterior): {common_walls}. 

Adhere to these additional requirements: {additional_requirements}.
Provide your response succinctly, without additional text at the beginning or end."""


floor_object_selection_prompt =  """Assist me in selecting floor-based large objects to furnish each empty room. The following is a list of objects for you to choose from: {object_categories}.

Present your recommendations in this format: wall id | wall vertices | object1, object2, ...
The wall vertices are the wall which you are to place the object against, and the objects will be placed near to each other in the order you give. If you'd like to place one or multiple adjacent objects like carpet or table and chairs in the middle of the room (instead of against wall), just leave the "wall id | wall vertices" to "- | -".

Example output:
[living room]
1 | (0,0), (0,1.5) | Coffee_Table, Chair
1 | (0,2.8), (0,8) | Sofa, Table, Sofa
2 | (5,0), (5,8) | Plant, TV_Table, Plant, Library
- | - | Chair, RoomTable, Chair
- | - | Carpet

Note:
1. You should not select objects that are inappropriate to be placed on the floor; try to select as **many** objects as possible and reasonable that match the room type and wall length. 
2. You can place multiple objects with the same cateory in the room but against different walls. 
3. Remember that each wall should be placed at least one object. Try to place as many as possible.
4. Try to make your output different, novel and diversified, but adhere to the commen sense of how a room would be furnished.

Currently, the design in progress is {input}. Here are the wall_id and vertices of each wall in each room that can place objects: 
{object_wall_vertices}

Please also consider the following additional requirements: {additional_requirements}.
Your response should be precise, without additional text at the beginning or end."""


small_object_selection_prompt =  """As an experienced room designer, you are tasked to bring life into the room by strategically placing more *small* objects. Those objects should only be arranged *on the flat surface" of large objects which serve as receptacles. 
The output should be formatted as follows: "receptacle: (small object-1, quantity), (small object-2, quantity) ..."
There's no restriction on the number of small objects you can select for each receptacle. An example of this format is as follows:
[living room]
Sofa0: (Pillow, 1), (Book, 2), (TV_Remote, 1)
TV_Table0: (TV, 1), (GameConsole, 1), (Vase, 1)
[bedroom]
...

Now, we are designing {input}. 
The available receptacles in the room include: {receptacles}. 
The available small objects include: {small_objects}. 
You should **only** choose from these small objects to place on top of the available receptacles.

Additional requirements for this design project are as follows: {additional_requirements}. 
Your response should solely contain the information about the placement of objects and should not include any additional text before or after the main content."""