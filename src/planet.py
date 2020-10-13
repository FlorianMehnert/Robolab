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
        self.planetname = ""

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
        #to backtrack unknown paths
        self.paths[start] = ()
        return
    
    def removePath(self, path: Tuple[Tuple[int, int], Direction]):
        #removes path with obstacle
        self.paths.pop(path)
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
        pathdict = {}
        for key in self.paths:
            (coord,direction) = key
            if coord in pathdict:
                 pathdict[key] = pathdict[key].update(self.getTargets(direction, self.paths[key]))
            else:
                pathdict[coord] = self.getTargets(direction, self.paths[key])
        return pathdict


    def getTargets(self,direction,target):      #dict in dict
        try:
            helpdict[direction] = (target)
        except:
            helpdict = {direction: target}
        return helpdict


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

    def getName(self) -> str:
        """
        Get name of planet.

        Examples:
            getName() returns: "Reis"
            getName() returns: ""
        : return: str
        """
        return self.planetname

    def setName(self, name: str):
        """
        Set name of planet.

        Examples:
            setName("Reis")
        : return: void
        """
        self.planetname = name

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
        return self.shortestPathDijkstra(start, target)

    def shortestPathDijkstra(self, start: Tuple[int, int], target: Tuple[int, int]) -> Union[None, List[Tuple[Tuple[int, int], Direction]]]:
        """
        Returns a shortest path between two nodes using Djikstra algorithm

        Examples:
            shortest_path((0,0), (2,2)) returns: [((0, 0), Direction.EAST), ((1, 0), Direction.NORTH)]
            shortest_path((0,0), (1,2)) returns: None
        :param start: 2-Tuple
        :param target: 2-Tuple
        :return: 2-Tuple[List, Direction]
        """
        # TODO: What happens if no connection is known between start and target.
        visitedNodes = []
        paths = self.getPaths()
        countNode = len(paths)
        table = {}# Dict[node: Tuple[int, int]: 3-Tuple(weight: int, previous: int, Direction)]
        targetKnown = False
        startKnown = False

        if start == target:
            return [start, 0]
        # Initialization of table
        for node in paths:
            table.update(node, (0x7fffff, (int, int), Direction))
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
                            table[paths[currentNode[0]][dir][0]][0] = totalWeight
                            table[paths[currentNode[0]][dir][0]][1] = currentNode[0]
                            table[paths[currentNode[0]][dir][0]][2] = dir
            visitedNodes.append(currentNode[0])

        # Find shortest path
        shortestPathReverse = []
        nextNode = target
        while nextNode == start:
            shortestPathReverse.append((nextNode, table[nextNode][2]))
            nextNode = table[nextNode][1]
        shortestPathReverse.append((nextNode, table[nextNode][2]))
        shortestPath = []
        while len(shortestPathReverse) > 0:
            shortestPath.append(shortestPathReverse.pop)
        return shortestPath


    def getNewPath(self, position: Tuple[int, int]) -> Union[None, List[Tuple[Tuple[int, int], Direction]]]:
        #finds the closest unvisited path
        compare = 100       #might need to change value
        newCoord = []
        for key in self.paths:
            (coord,direction) = key
            if self.paths[key] == ():
                #find the closest point
                (a,b) = coord
                (c,d) = position
                if abs((a + b) - (c - d)) <= compare:
                     newCoord = key
        if newCoord == []:
            return #map explored
        else:
            return self.shortestPath(position,newCoord)