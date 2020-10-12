#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
from enum import IntEnum, unique
from typing import List, Tuple, Dict, Union


@unique
class Direction(IntEnum):
    """ Directions in shortcut """
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270


Weight = int
"""
Weight of a given path (received from the server)

Value:  -1 if blocked path
        >0 for all other paths
        never 0
"""


class Planet:
    """
    Contains the representation of the map and provides certain functions to manipulate or extend
    it according to the specifications
    """

    def __init__(self):
        """ Initializes the data structure """
        self.target = None
        self.paths = {}

    def addPath(self, start: Tuple[Tuple[int, int], Direction], target: Tuple[Tuple[int, int], Direction],
                 weight: int):
        """
         Adds a bidirectional path defined between the start and end coordinates to the map and assigns the weight to it

        Example:
            add_path(((0, 3), Direction.NORTH), ((0, 3), Direction.WEST), 1)
        :param start: 2-Tuple
        :param target:  2-Tuple
        :param weight: Integer
        :return: void
        """
        if start[0] not in self.paths:
            self.addNode(start[0])
        if target[0] not in self.paths:
            self.addNode(target[0])

        if target is None:
            self.paths[start][start[1]] = False
        else:
            self.paths[start][start[1]] = (target[0], target[1], weight)
            self.paths[target][target[1]] = (start[0], start[1], weight)
        return


    def addUnknownPath(self, start: Tuple[Tuple[int, int], Direction]):
        self.paths[start] = ()
        return

    def addNode(self, node: Tuple[int, int]):
        nodepaths = {}
        for dir in Direction:
            nodepaths[dir].update(None)
        self.paths[node].update(nodepaths)

    def getPaths(self) -> Dict[Tuple[int, int], Dict[Direction, Tuple[Tuple[int, int], Direction, Weight]]]:
        """
        Returns all paths

        Example:
            {
                (0, 3): {
                    Direction.NORTH: ((0, 3), Direction.WEST, 1),
                    Direction.EAST: ((1, 3), Direction.WEST, 2),
                    Direction.WEST: ((0, 3), Direction.NORTH, 1)
                },
                (1, 3): {
                    Direction.WEST: ((0, 3), Direction.EAST, 2),
                    ...
                },
                ...
            }
        :return: Dict
        """

        for key in self.paths:
            (coord,direction) = key
            pathdict = {}
            if coord in pathdict:
                 pathdict[start] = pathdict[key].update(self.get_targets(direction, self.paths[key]))
            else:
                pathdict[coord] = self.get_targets(direction, self.paths[key])
            pathdict = {coord: self.get_targets(direction, self.paths[key])}
        return pathdict


    def getTarget(self) -> Tuple[int, int]:
        """
        Get target on planet.

        Examples:
            getTarget() returns: (3, 7)
            getTarget() returns: None
        : return: 2-Tuple[int, int]
        """
        return self.target

    def setTarget(self, node: Tuple[int, int]):
        """
        Set target on planet.

        Examples:
            setTarget((31, 41))
        : return: void
        """
        self.target = node

    def shortestPath(self, start: Tuple[int, int], target: Tuple[int, int]) -> Union[None, List[Tuple[Tuple[int, int], Direction]]]:
        """
        Returns a shortest path between two nodes

        Examples:
            shortest_path((0,0), (2,2)) returns: [((0, 0), Direction.EAST), ((1, 0), Direction.NORTH)]
            shortest_path((0,0), (1,2)) returns: None
        :param start: 2-Tuple
        :param target: 2-Tuple
        :return: 2-Tuple[List, Direction]
        """

        # YOUR CODE FOLLOWS (remove pass, please!)
        pass
