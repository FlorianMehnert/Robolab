#!/usr/bin/env python3

# This file was provided by a tutor

from enum import IntEnum, unique
from typing import List, Optional, Tuple, Dict, Set
import math


# IMPORTANT NOTE: DO NOT IMPORT THE ev3dev.ev3 MODULE IN THIS FILE

@unique
class Direction(IntEnum):
    """ Directions in shortcut """
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270


# simple alias, no magic here
Weight = int
""" 
    Weight of a given path (received from the server)
    value:  -1 if blocked path
            >0 for all other paths
            never 0
"""


class Planet:
    """
    Contains the representation of the map and provides certain functions to manipulate it according to the specifications
    """

    def __init__(self):
        """ Initializes the data structure """
        self.target = None
        self.paths: Set[Tuple[Tuple[Tuple[int, int], Direction], Tuple[Tuple[int, int], Direction], Weight]] = set()

    def addPath(self, start: Tuple[Tuple[int, int], Direction], target: Tuple[Tuple[int, int], Direction],
                weight: int):
        """
         Adds a bidirectional path defined between the start and end coordinates to the map and assigns the weight to it
        example:
            add_path(((0, 3), Direction.NORTH), ((0, 3), Direction.WEST), 1)
        :param start: 2-Tuple
        :param target:  2-Tuple
        :param weight: Integer
        :return: void
        """
        self.paths.add((start, target, weight))
        self.paths.add((target, start, weight))

    def getPaths(self) -> Dict[Tuple[int, int], Dict[Direction, Tuple[Tuple[int, int], Direction, Weight]]]:
        """
        Returns all paths
        example:
            get_paths() returns:
            {
                (0, 3): {
                    Direction.NORTH: ((0, 3), Direction.WEST, 1),
                    Direction.EAST: ((1, 3), Direction.WEST, 2)
                },
                (1, 3): {
                    Direction.WEST: ((0, 3), Direction.EAST, 2),
                    ...
                },
                ...
            }
        :return: Dict
        """
        path_dict = dict()
        for path in self.paths:
            if path[0][0] not in path_dict:
                path_dict[path[0][0]] = dict()
            path_dict[path[0][0]][path[0][1]] = (path[1][0], path[1][1], path[2])
        return path_dict

    def shortestPath(self, start: Tuple[int, int], target: Tuple[int, int]) -> Optional[
        List[Tuple[Tuple[int, int], Direction]]]:
        """
        Returns a shortest path between two nodes
        examples:
            shortest_path((0,0), (2,2)) returns: [((0, 0), Direction.EAST), ((1, 0), Direction.NORTH)]
            shortest_path((0,0), (1,2)) returns: None
        :param start: 2-Tuple
        :param target: 2-Tuple
        :return: List, Direction
        """
        if target == start:
            return []

        distance: Dict[Tuple[int, int], int] = dict()
        predecessor: Dict[Tuple[int, int], Tuple[int, int]] = dict()
        all_paths = self.getPaths()
        unchecked_verts = set(all_paths.keys())

        if target not in unchecked_verts:
            return None

        self.initDicts(start, distance, predecessor, unchecked_verts)
        while unchecked_verts:
            cur_vertex = None
            min_dist = math.inf
            for tup in unchecked_verts:
                if distance[tup] < min_dist:
                    min_dist = distance[tup]
                    cur_vertex = tup

            unchecked_verts.remove(cur_vertex)
            if cur_vertex == target:
                break
            for neighbor in self.getNeighbor(cur_vertex, all_paths):
                if neighbor[0] in unchecked_verts:
                    self.updateDistance(cur_vertex, neighbor, distance, predecessor)
        return self.buildShortestPath(target, predecessor, all_paths)

    def initDicts(self, start, distance, predecessor, unchecked_verts):
        for tup in unchecked_verts:
            distance[tup] = math.inf
            predecessor[tup] = None
        distance[start] = 0

    def getNeighbor(self, cur_vertex, all_paths):
        return {(tup, weight) for tup, _, weight in all_paths[cur_vertex].values()}

    def updateDistance(self, cur_vertex, neighbor, distance, predecessor):
        alternative_dist = distance[cur_vertex] + neighbor[1]
        if alternative_dist < distance[neighbor[0]]:
            distance[neighbor[0]] = alternative_dist
            predecessor[neighbor[0]] = cur_vertex

    def buildShortestPath(self, target, predecessor, all_paths):
        work_path = [target]
        path: Optional[List[Tuple[Tuple[int, int], Direction]]] = []
        cur_vertex = target
        while predecessor[cur_vertex] is not None:
            cur_vertex = predecessor[cur_vertex]
            work_path.insert(0, cur_vertex)
        for i in range(len(work_path) - 1):
            tup = work_path[i]
            best_direction = None
            best_weight = math.inf
            for direction in all_paths[tup].keys():
                cur_tup = all_paths[tup][direction]
                if cur_tup[0] == work_path[i + 1]:
                    if cur_tup[2] < best_weight:
                        best_weight = cur_tup[2]
                        best_direction = direction
            path.append((tup, best_direction))
        return path
