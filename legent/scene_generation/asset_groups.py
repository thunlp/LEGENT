import copy
import random
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
)

import numpy as np
from attr import field
from attrs import define

from .objects import ObjectDB
from .types import Object, Vector3


@define
class Asset:
    asset_id: str
    """The unique AI2-THOR identifier of the asset."""

    top_down_poly: Sequence[Tuple[float, float]]
    """Full bounding box area that the polygon takes up. Including padding, excludes margin."""

    top_down_poly_with_margin: Sequence[Tuple[float, float]]
    """Full bounding box area that the polygon takes up. Includes padding and margin."""

    rotation: int
    """The yaw rotation of the object."""

    position: Vector3
    """Center position of the asset. Includes padding, excludes margin."""

    anchor_type: Literal["inCorner", "onEdge", "inMiddle"]
    """Specifies the location of the asset in the room."""

    room_id: int
    """The id of the procedural room."""

    object_n: int
    """The number of assets/asset groups in the scene before placing this asset."""

    states: Dict[str, Any]

    odb: ObjectDB

    poly_xs: List[float] = field(init=False)
    poly_zs: List[float] = field(init=False)

    margined_poly_xs: List[float] = field(init=False)
    margined_poly_zs: List[float] = field(init=False)

    def __attrs_post_init__(self) -> None:
        self.poly_xs = [p[0] for p in self.top_down_poly]
        self.poly_zs = [p[1] for p in self.top_down_poly]

        self.margined_poly_xs = [p[0] for p in self.top_down_poly_with_margin]
        self.margined_poly_zs = [p[1] for p in self.top_down_poly_with_margin]

    @property
    def asset_dict(self) -> Object:
        return Object(
            id=f"{self.room_id}|{self.object_n}",
            position=self.position,
            rotation=Vector3(x=0, y=self.rotation, z=0),
            assetId=self.asset_id,
            kinematic=bool(
                self.pt_db.PLACEMENT_ANNOTATIONS.loc[
                    self.pt_db.ASSET_ID_DATABASE[self.asset_id]["objectType"]
                ]["isKinematic"]
            ),
            **self.states,
        )


@define
class AssetGroup:
    asset_group_name: str
    """The name of the asset group."""

    top_down_poly: Sequence[Tuple[float, float]]
    """Full bounding box area that the polygon takes up. Including padding, excludes margin."""

    top_down_poly_with_margin: Sequence[Tuple[float, float]]
    """Full bounding box area that the polygon takes up. Includes padding and margin."""

    objects: List[Dict[str, Any]]
    """
    Must have keys for:
    - position: Vector3 the center position of the asset in R^3 (includes padding).
    - rotation: float the top down rotation of the object in degrees
    - assetId: str
    - instanceId: str the instanceId of the asset within the group.
    """

    anchor_type: Literal["inCorner", "onEdge", "inMiddle"]
    """Specifies the location of the asset group in the room."""

    room_id: int
    """The id of the procedural room."""

    object_n: int
    """The number of assets/asset groups in the scene before placing this asset."""

    odb: ObjectDB

    poly_xs: List[float] = field(init=False)
    poly_zs: List[float] = field(init=False)

    margined_poly_xs: List[float] = field(init=False)
    margined_poly_zs: List[float] = field(init=False)

    def __attrs_post_init__(self) -> None:
        self.poly_xs = [p[0] for p in self.top_down_poly]
        self.poly_zs = [p[1] for p in self.top_down_poly]

        self.margined_poly_xs = [p[0] for p in self.top_down_poly_with_margin]
        self.margined_poly_zs = [p[1] for p in self.top_down_poly_with_margin]

    @property
    def assets_dict(self) -> List[Object]:
        # NOTE: Assign "above" objects to be children to parent receptacle
        asset_group_metadata = self.odb.ASSET_GROUPS[self.asset_group_name][
            "assetMetadata"
        ]
        parent_children_pairs = []
        for child_id, metadata in asset_group_metadata.items():
            if (
                "parentInstanceId" in metadata
                and metadata["position"]["verticalAlignment"] == "above"
            ):
                parent_id = str(metadata["parentInstanceId"])
                parent_children_pairs.append((parent_id, child_id))

        objects = {
            obj["instanceId"]: Object(

                id=f"{self.room_id}|{self.object_n}|{i}",
                position=obj["position"],
                rotation=Vector3(x=0, y=obj["rotation"], z=0),
                assetId=obj["assetId"],
                # kinematic=bool(
                #     self.odb.PLACEMENT_ANNOTATIONS.loc[
                #         self.odb.OBJECT_TO_TYPE[obj["assetId"]]["objectType"]
                #     ]["isKinematic"]
                # ),
            )
            for i, obj in enumerate(self.objects)
        }

        # NOTE: assign children to "children" object and then remove them as keys
        # in the objects dict.
        child_instance_ids = set()
        for parent_id, child_id in parent_children_pairs:
            if "children" not in objects[parent_id]:
                objects[parent_id]["children"] = []
            objects[parent_id]["children"].append(objects[child_id])
            child_instance_ids.add(child_id)
        for child_id in child_instance_ids:
            del objects[child_id]

        return list(objects.values())


class AssetGroupGenerator:
    def __init__(
        self,
        name: str,  # The name of the asset group.
        data: Dict[str, Any],  # The parsed json data of the asset group.
        odb: ObjectDB,
    ) -> None:
        self.name = name
        self.data = data
        self.odb = odb

        self.__attrs_post_init__()

    def __attrs_post_init__(self):
        """Preprocesses the asset group data to be in a better format.

        - Tansforms asset_metadata[assetIds] from
          [asset_type]: [...assetIds] to [...(asset_type, asset_id)].
        - Transforms the asset database from [asset_type]: [...asset]
          to [asset_type]: [...[asset_id]: [asset]].
        """
        self.data = copy.deepcopy(self.data)
        self.cache = {}

        def flatten_asset_ids() -> None:
            """Tansforms asset_metadata[assetIds] from [asset_type]: [...assetIds]
            to [...(asset_type, asset_id)] and filter assets by split.
            """
            for asset_metadata in self.data["assetMetadata"].values():
                out = []
                for asset_type, asset_ids in asset_metadata["assetIds"].items():
                    for asset_id in asset_ids:
                        out.append((asset_type, asset_id))
                if not out:
                    raise Exception(f"No valid asset groups for {self.name} ! ")
                asset_metadata["assetIds"] = out

        flatten_asset_ids()

    @property
    def dimensions(self) -> Vector3:
        """Get the dimensions of the asset group.

        The dimensions are set to the maximum possible extent of the asset
        group, independently in each direction.

        TODO: Consider accounting for randomness in the dtheta dimensions.
        """
        if "dimensions" not in self.cache:
            self._set_dimensions()
        return self.cache["dimensions"]

    def _set_dimensions(self) -> None:
        import pandas as pd
        asset_group_assets = {
            asset["name"]: set([asset_id for asset_type, asset_id in asset["assetIds"]])
            for asset in self.data["assetMetadata"].values()
        }

        assets = {
            asset_name: pd.DataFrame(
                [
                    {
                        "assetId": asset_id,
                        "assetType": self.odb.OBJECT_TO_TYPE[asset_id],
                        "xSize": self.odb.PREFABS[asset_id]["size"]["x"],
                        "ySize": self.odb.PREFABS[asset_id]["size"]["y"],
                        "zSize": self.odb.PREFABS[asset_id]["size"]["z"],
                    }
                    for asset_id in asset_ids
                ]
            )
            for asset_name, asset_ids in asset_group_assets.items()
        }

        max_y = -np.inf
        chosen_asset_ids = {"largestXAssets": dict(), "largestZAssets": dict()}
        for asset_name, asset_df in assets.items():
            x_max_asset_id = asset_df.iloc[asset_df["xSize"].idxmax()]["assetId"]
            z_max_asset_id = asset_df.iloc[asset_df["zSize"].idxmax()]["assetId"]

            chosen_asset_ids["largestXAssets"][asset_name] = (
                self.odb.OBJECT_TO_TYPE[x_max_asset_id],
                x_max_asset_id,
            )
            chosen_asset_ids["largestZAssets"][asset_name] = (
                self.odb.OBJECT_TO_TYPE[z_max_asset_id],
                z_max_asset_id,
            )

            if asset_df["ySize"].max() > max_y:
                max_y = asset_df["ySize"].max()

        # TODO: eventually turn off randomness.
        x_dim_assets = self.sample_object_placement(
            chosen_asset_ids=chosen_asset_ids["largestXAssets"]
        )
        z_dim_assets = self.sample_object_placement(
            chosen_asset_ids=chosen_asset_ids["largestZAssets"]
        )

        self.cache["dimensions"] = Vector3(
            x=x_dim_assets["bounds"]["x"]["length"],
            y=max_y,
            z=z_dim_assets["bounds"]["z"]["length"],
        )

    @staticmethod
    def rotate_bounding_box(
        theta: float,
        bbox_size: Dict[str, float],
        x_center: float = 0,
        z_center: float = 0,
    ) -> Dict[str, Dict[str, float]]:
        """Rotate a top-down 2D bounding box.

        Args:
            theta: The rotation of the bounding box in degrees.
            bbox_size: The size of the bounding box. Must have keys for {"x", "z"}.
            x_center: The center x position of the bounding box.
            z_center: The center z position of the bounding box.
        """
        bb_corners = [
            (x_center + bbox_size["x"] / 2, z_center + bbox_size["z"] / 2),
            (x_center - bbox_size["x"] / 2, z_center + bbox_size["z"] / 2),
            (x_center - bbox_size["x"] / 2, z_center - bbox_size["z"] / 2),
            (x_center + bbox_size["x"] / 2, z_center - bbox_size["z"] / 2),
        ]
        theta_rad = theta * np.pi / 180.0
        for i, (x, z) in enumerate(bb_corners):
            x_ = (
                x_center
                + (x - x_center) * np.cos(theta_rad)
                + (z - z_center) * np.sin(theta_rad)
            )
            z_ = (
                z_center
                - (x - x_center) * np.sin(theta_rad)
                + (z - z_center) * np.cos(theta_rad)
            )
            bb_corners[i] = (x_, z_)
        return {
            "x": {
                "min": min(bb_corners, key=lambda bb_corner: bb_corner[0])[0],
                "max": max(bb_corners, key=lambda bb_corner: bb_corner[0])[0],
            },
            "z": {
                "min": min(bb_corners, key=lambda bb_corner: bb_corner[1])[1],
                "max": max(bb_corners, key=lambda bb_corner: bb_corner[1])[1],
            },
        }

    def sample_object_placement(
        self,
        allow_clipping: bool = True,
        floor_position: float = 0,
        use_thumbnail_assets: bool = False,
        chosen_asset_ids: Optional[Dict[str, Tuple[str, str]]] = None,
    ) -> List[Dict[str, Any]]:
        """Sample object placement.

        Args:
            chosen_asset_ids: Maps from the "name" in assetMetadata to the chosen
                (assetType, assetId) of that asset. Note that assets with the same
                name have the same chosen assetId.
            floor_position: The position of the floor.
            use_thumbnail_assets If the randomly chosen asset should be the one
                shown in the thumbnail specified in the JSON.

        Returns:
            A dict mapping each assetId to an (x, y, z) position.
        """
        if not allow_clipping:
            raise NotImplementedError(
                "Currently, only allow_clipping == True is supported."
            )

        out = {
            "objects": [],
            "bounds": {
                "x": {
                    "min": float("inf"),
                    "max": float("-inf"),
                },
                "z": {
                    "min": float("inf"),
                    "max": float("-inf"),
                },
            },
        }

        asset_stack = [
            {"parentId": None, "tree": parent_asset}
            for parent_asset in reversed(self.data["treeData"])
        ]

        # assets with the same name have the same assetIds chosen
        if chosen_asset_ids is None:
            chosen_asset_ids = dict()

        # quick lookup for the placement of parent positions
        parent_asset_lookup = dict()

        while asset_stack:
            asset = asset_stack.pop()
            instance_id = str(asset["tree"]["instanceId"])

            if "children" in asset["tree"]:
                for child_asset in asset["tree"]["children"]:
                    asset_stack.append({"parentId": instance_id, "tree": child_asset})

            asset_metadata = self.data["assetMetadata"][instance_id]

            # NOTE: choose the asset id
            name = asset_metadata["name"]
            if name in chosen_asset_ids:
                asset_type, asset_id = chosen_asset_ids[name]
            elif use_thumbnail_assets:
                asset_id = asset_metadata["shownAssetId"]
                asset_type = self.odb.OBJECT_TO_TYPE[asset_id]
            else:
                asset_type, asset_id = random.choice(asset_metadata["assetIds"])
            chosen_asset_ids[name] = (asset_type, asset_id)

            # set the y position of the asset
            bbox_size = self.odb.PREFABS[asset_id]["size"]

            # NOTE: add in randomness
            dtheta = asset_metadata["randomness"]["dtheta"]
            theta_offset = random.random() * dtheta * 2 - dtheta
            theta = asset_metadata["rotation"] + theta_offset

            # calculate the bounding box after rotating the object.
            bbox_bounds = AssetGroupGenerator.rotate_bounding_box(
                theta=theta, bbox_size=bbox_size
            )

            # NOTE: determine where to place the asset
            if asset["parentId"] is None:
                # NOTE: position represents an absolute position
                center_position = asset_metadata["position"]
                x_center, z_center = center_position["x"], center_position["z"]
                y_center = floor_position + bbox_size["y"] / 2
                bbox_bounds["y"] = {
                    "min": floor_position,
                    "max": floor_position + bbox_size["y"],
                }
            else:
                # NOTE: position is relative to the parent
                parent = parent_asset_lookup[asset["parentId"]]

                x_center = parent["position"]["x"] + asset_metadata["position"]["x"]
                z_center = parent["position"]["z"] + asset_metadata["position"]["z"]

                parent_x_length = -(
                    parent["bbox"]["x"]["max"] - parent["bbox"]["x"]["min"]
                )
                parent_z_length = (
                    parent["bbox"]["z"]["max"] - parent["bbox"]["z"]["min"]
                )

                anchor = asset_metadata["position"]["relativeAnchorToParent"]
                if anchor in {0, 1, 2}:
                    z_center -= parent_z_length / 2
                elif anchor in {6, 7, 8}:
                    z_center += parent_z_length / 2

                if anchor in {0, 3, 6}:
                    x_center -= parent_x_length / 2
                elif anchor in {2, 5, 8}:
                    x_center += parent_x_length / 2

                x_alignment = asset_metadata["position"]["xAlignment"]
                z_alignment = asset_metadata["position"]["zAlignment"]

                bbox_x_length = bbox_bounds["x"]["max"] - bbox_bounds["x"]["min"]
                bbox_z_length = bbox_bounds["z"]["max"] - bbox_bounds["z"]["min"]

                if x_alignment == 0:
                    x_center -= bbox_x_length / 2
                elif x_alignment == 2:
                    x_center += bbox_x_length / 2

                if z_alignment == 0:
                    z_center -= bbox_z_length / 2
                elif z_alignment == 2:
                    z_center += bbox_z_length / 2

                if asset_metadata["position"]["verticalAlignment"] == "nextTo":
                    y_center = parent["floorPosition"] + bbox_size["y"] / 2
                    bbox_bounds["y"] = {
                        "min": parent["floorPosition"],
                        "max": parent["floorPosition"] + bbox_size["y"],
                    }
                elif asset_metadata["position"]["verticalAlignment"] == "above":
                    # NOTE: This is naive. It places objects at of the parent
                    # object's bounding box height. Consider a more advanced height
                    # calculation that looks at the contours of an object instead
                    # of just using the bounding box.
                    y_center = (
                        parent["floorPosition"] + parent["height"] + bbox_size["y"] / 2
                    )
                    bbox_bounds["y"] = {
                        "min": parent["floorPosition"] + parent["height"],
                        "max": parent["floorPosition"]
                        + parent["height"]
                        + bbox_size["y"],
                    }

            bbox_bounds["x"]["min"] += x_center
            bbox_bounds["x"]["max"] += x_center
            bbox_bounds["z"]["min"] += z_center
            bbox_bounds["z"]["max"] += z_center

            for k in ["x", "z"]:
                if bbox_bounds[k]["min"] < out["bounds"][k]["min"]:
                    out["bounds"][k]["min"] = bbox_bounds[k]["min"]
            for k in ["x", "z"]:
                if bbox_bounds[k]["max"] > out["bounds"][k]["max"]:
                    out["bounds"][k]["max"] = bbox_bounds[k]["max"]
            out["bounds"]["y"] = bbox_bounds["y"]

            parent_asset_lookup[instance_id] = {
                "position": {"x": x_center, "y": y_center, "z": z_center},
                "floorPosition": y_center - bbox_size["y"] / 2,
                "height": bbox_size["y"],
                "bbox": bbox_bounds,
                "assetId": asset_id,
            }

            out["objects"].append(
                {
                    "instanceId": instance_id,
                    "assetId": asset_id,
                    "assetType": asset_type,
                    "position": {"x": x_center, "y": y_center, "z": z_center},
                    "rotation": theta,
                    "bbox": bbox_bounds,
                }
            )

        # NOTE: cache the center and length of the group
        for k in ["x", "y", "z"]:
            out["bounds"][k]["length"] = (
                out["bounds"][k]["max"] - out["bounds"][k]["min"]
            )
            out["bounds"][k]["center"] = (
                out["bounds"][k]["min"] + out["bounds"][k]["max"]
            ) / 2

        return out
