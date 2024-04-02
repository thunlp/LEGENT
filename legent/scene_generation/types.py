import random
from typing import Dict, List, Tuple, TypedDict

from attrs import define

BoundaryGroups = Dict[Tuple[int, int], List[Tuple[float, float]]]


@define
class SamplingVars:
    interior_boundary_scale: float
    """Amount in meters with which each interior boundary is scaled.

    This is often useful to set more than 1 because most single doors are between
    :math:`(1.0 : 1.1)` meters. Thus, if a scale of :math:`1.0` was used, there wouldn't
    be any eligable doors with a single panel wall separator.
    """

    max_floor_objects: int
    """The maximum number of objects that can be placed on the floor of each room."""

    @classmethod
    def sample(cls) -> "SamplingVars":
        return SamplingVars(
            interior_boundary_scale=random.uniform(1.6, 2.2),
            max_floor_objects=random.choices(
                population=[1, 4, 5, 6, 7],
                weights=[1 / 200, 1 / 100, 1 / 50, 1 / 10, 173 / 200],
                k=1,
            )[0],
        )


class Vector3(TypedDict):
    x: float
    y: float
    z: float


class Object(TypedDict):
    id: str
    assetId: str
    """The id of the asset in the asset database."""

    rotation: Vector3
    """The global rotation of the object."""

    position: Vector3
    """The global (x, y, z) position of the object."""

    children: List["Object"]
    """Objects that are parented to the receptacle."""

    kinematic: bool
    """True if the object can be moved, False otherwise.

    Large objects, such as Fridges and Toilets often shouldn't be moveable, and 
    can result in a variety of bugs.
    """
