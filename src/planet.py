#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
from enum import IntEnum, unique
from typing import List, Tuple, Dict, Union

Weight = int
"""
Weight of a given path (received from the server)

Value:  -1 if blocked path
        >0 for all other paths
        never 0
"""


@unique
class Direction(IntEnum):
    """ Directions in shortcut """
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270


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
        self.start = None  # Tuple[Tuple[int, int], Direction]
        self.newPlanet = True

    def addPath(self, start: Tuple[Tuple[int, int], Direction], target: Tuple[Tuple[int, int], Direction],
                weight: int):
        """
         Adds a bidirectional path defined between the start and end coordinates to the map and assigns the weight to it

        Example:
            add_path(((0, 3), Direction.NORTH), ((0, 3), Direction.WEST), 1)
        :param start: 2-Tuple
        :param target:  2-Tuple
        :param weight: Integer,
            Weight of a given path (received from the server)
            Value: -3 if no existing path
                -2 if unknown available path
                -1 if blocked path,
                0 discovered paths, unknown if free or blocked,
                >0 for all free paths
        :param weight: Integer
        :return: void
        """
        if start[0] not in self.paths:
            self.addNode(start[0])
        if target[0] not in self.paths:
            self.addNode(target[0])

        # no existing path
        if weight == -3 and self.paths[start[0]][start[1]][2] == -2:
            self.paths[start[0]][start[1]] = (self.paths[start[0]][start[1]][0], self.paths[start[0]][start[1]][1], -3)
            # print("Path Start: " + self.paths[start[0]][start[1]] + ";\tTarget: no")
        # existing path but no more information
        elif weight == 0 and self.paths[start[0]][start[1]][2] == -2:
            self.paths[start[0]][start[1]] = (self.paths[start[0]][start[1]][0], self.paths[start[0]][start[1]][1], -1)
            # print("Path Start: " + self.paths[start[0]][start[1]] + ";\tTarget: no")
        # blocked path
        elif weight == -1:
            # target known and not stored
            if not self.paths[start[0]][start[1]][0] and start != target:
                self.paths[start[0]][start[1]] = (target[0], target[1], -1)
                self.paths[target[0]][target[1]][0] = (start[0], start[1], -1)
                # print("Path Start: " + self.paths[start[0]][start[1]] + ";\tTarget: " + self.paths[target[0]][target[1]])
            else:
                self.paths[start[0]][start[1]] = (
                    self.paths[start[0]][start[1]][0], self.paths[start[0]][start[1]][1], -1)
                # print("Path Start: " + self.paths[start[0]][start[1]] + ";\tTarget: no")
        elif weight > 0:
            self.paths[start[0]][start[1]] = (target[0], target[1], weight)
            self.paths[target[0]][target[1]] = (start[0], start[1], weight)
            # print("Path Start: " + self.paths[start[0]][start[1]] + ";\tTarget: " + self.paths[target[0]][target[1]])
        return

    def addUnknownPath(self, start: Tuple[Tuple[int, int], Direction]):
        # to backtrack unknown paths
        self.paths[start] = ()
        return

    def removePath(self, path: Tuple[Tuple[int, int], Direction]):
        # removes path with obstacle
        self.paths.pop(path)
        return

    def setAttachedPaths(self, node: Tuple[int, int], dirList: List[Direction]):
        if node not in self.paths:
            self.addNode(node)
        for dir in self.paths[node]:
            if dir in dirList:
                self.addPath((node, dir), (node, dir), 0)
            else:
                self.addPath((node, dir), (node, dir), -3)

    def addNode(self, node: Tuple[int, int]):
        """
        Add new node in path dictionary with unknown path status

        Example:
            addNode((3, 4))
        :param node: 2-Tuple (posX, posY)
        :return: void
        """
        nodepaths = {}
        for dir in Direction:
            nodepaths[dir] = ((), 0, -2)
        self.paths[node] = nodepaths

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
        for node in self.paths:
            pathdict[node] = {}
            for dir in self.paths[node]:
                if dir[2] > 0:
                    pathdict[node][dir] = self.paths[node][dir]
        return pathdict

    def getTargets(self, direction, target):  # dict in dict
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

    def setStart(self, coord: List[int], orientation: Direction):
        """
        Set start node of planet. Tuple is new set at every node

        Examples:
            setStart((42, 42), Direction.NORTH)
        : return: void
        """
        self.start = (coord, orientation)

    def setStartCoord(self, coord: Tuple[int, int]):
        """
        Set start coordinates of planet. Tuple is new set at every node

        Examples:
            setStartCoord((42, 42))
        : return: void
        """
        self.start = (coord, self.start[1])

    def setStartDirection(self, orientation: Direction):
        """
        Set start orientation of planet. Direction is new set at every node

        Examples:
            setStartDirection((42, 42), Direction.NORTH)
        : return: void
        """
        self.start = (self.start[0], orientation)

    def shortestPath(self, start: Tuple[int, int], target: Tuple[int, int]) -> Union[
        None, List[Tuple[Tuple[int, int], Direction]]]:
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

    def shortestPathDijkstra(self, start: Tuple[int, int], target: Tuple[int, int]) -> Union[
        None, List[Tuple[Tuple[int, int], Direction]]]:
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
        table = {}  # Dict[node, Tuple[int, int]: 3-Tuple(weight: int, previous: int, Direction)]
        targetKnown = False
        startKnown = False

        if start == target:
            return [start, 0]
        # Initialization of table
        for node in paths:
            table.update({node: (0x7fffff, (int, int), Direction)})
            if node == target:
                targetKnown = True
            if node == start:
                startKnown = True
        if not targetKnown or not startKnown:
            return None
        table[start] = (0, start)

        # Weight calculation
        while countNode > len(visitedNodes):
            currentNode = ((int, int), 0x7fffff, (int, int))  # (node, weight, previous)
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
        # finds the closest unvisited path
        compare = 100  # might need to change value
        newCoord = []
        for key in self.paths:
            (coord, direction) = key
            if self.paths[key] == ():
                # find the closest point
                (a, b) = coord
                (c, d) = position
                if abs((a + b) - (c - d)) <= compare:
                    newCoord = key
                    compare = abs((a + b) - (c - d))
        if newCoord == []:
            return  # map explored
        else:
            return self.shortestPath(position, newCoord)
