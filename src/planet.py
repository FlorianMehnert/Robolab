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

    def add_path(self, start: Tuple[Tuple[int, int], Direction], target: Tuple[Tuple[int, int], Direction],
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

        # YOUR CODE FOLLOWS (remove pass, please!)
        pass

    def get_paths(self) -> Dict[Tuple[int, int], Dict[Direction, Tuple[Tuple[int, int], Direction, Weight]]]:
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

        # YOUR CODE FOLLOWS (remove pass, please!)
        pass

    def shortest_path(self, start: Tuple[int, int], target: Tuple[int, int]) -> Union[None, List[Tuple[Tuple[int, int], Direction]]]:
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

    def shortest_path_dijkstra(self, start: Tuple[int, int], target: Tuple[int, int]) -> Union[None, List[Tuple[Tuple[int, int], Direction]]]:
        visitedNodes = []
        paths = self.get_paths()
        countNode = len(paths)
        table = {}# Dict[node: Tuple[int, int]: 2-Tuple(weight: int, previous: int)]
        targetKnown = False
        startKnown = False

        if start == target:
            return [start, 0]
        # Initialization of table
        for node in paths:
            table.update(node, (0x7fffff, (int, int)))
            if node == target:
                targetKnown = True
            if node == start:
                startKnown = True
        if not targetKnown or not startKnown:
            return None
        table[start] = (0, start)

        # Weight calculation
        while countNode > len(visitedNodes):
            currentNode = ((int, int), 0x7fffff, (int, int)) # (node, weight, previous)
            # Select node with lowest weight
            for node in table:
                if node[0] in visitedNodes:
                    continue
                if node[1] < currentNode[1]:
                    currentNode = node
            # Update table
            for dir in Direction:
                if dir in paths[currentNode[0]]:
                    if paths[currentNode[0]][dir][0] not in visitedNodes:
                        totalWeight = currentNode[1] + paths[currentNode[0]][dir][2]
                        if totalWeight < table[paths[currentNode[0]][dir][0]][1]:
                            table[paths[currentNode[0]][dir][0]][1] = totalWeight
                            table[paths[currentNode[0]][dir][0]][2] = currentNode[0]
            visitedNodes.append(currentNode[0])

