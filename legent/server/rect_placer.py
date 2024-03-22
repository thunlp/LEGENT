from typing import Tuple
from pyqtree import Index


class RectPlacer:
    def __init__(self, bbox: Tuple[float, float, float, float]) -> None:
        """
        Args:
            bbox (Tuple[float, float, float, float]): (xmin, ymin, xmax, ymax)
        """
        self.bbox = bbox
        self.spindex = Index(bbox=bbox)

    def place_rectangle(
        self, name: str, bbox: Tuple[float, float, float, float]
    ) -> bool:
        """place a rectangle into the 2d space without overlapping

        Args:
            name (str): rectangle name
            bbox (Tuple[float, float, float, float]): (xmin, ymin, xmax, ymax)

        Returns:
            bool: whether successfully placed without overlapping
        """
        matches = self.spindex.intersect(bbox)
        if matches:
            return False
        else:
            self.spindex.insert(name, bbox)
            return True

    def place(self, name, x, z, x_size, z_size):
        """place a rectangle into the 2d space without overlapping

        Args:
            name (str): rectangle name
            x (float): x position
            z (float): z position
            x_size (float): x size
            z_size (float): z size

        Returns:
            bool: whether successfully placed without overlapping
        """
        return self.place_rectangle(
            name, (x - x_size / 2, z - z_size / 2, x + x_size / 2, z + z_size / 2)
        )

    def insert(self, name: str, bbox: Tuple[float, float, float, float]):
        """force place a rectangle into the 2d space"""
        self.spindex.insert(name, bbox)
