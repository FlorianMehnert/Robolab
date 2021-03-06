#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
import math
from enum import IntEnum, unique
from typing import List, Tuple, Dict, Union, Optional
import debug

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
        self.debug = debug.Debug(3)
        self.target = None
        self.paths = {}
        self.planet_name = ""
        self.start = None  # Tuple[Tuple[int, int], Direction]
        self.new_planet = True
        self.stack: List[Tuple[Tuple[int, int], Direction, int]] = []

    def add_path(self, start: Tuple[Tuple[int, int], Direction], target: Tuple[Tuple[int, int], Direction],
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
            self.add_node(start[0])
        if target[0] not in self.paths:
            self.add_node(target[0])

        # no existing path
        if weight == -3 and self.paths[start[0]][start[1]][2] == -2:
            self.paths[start[0]][start[1]] = (start[0], start[1], -3)
            self.set_weight_in_stack(-3, start)
            # self.debug.bprint(f"Path Not Existing: {start}: {self.paths[start[0]][start[1]]}")
        # existing path but no more information
        elif weight == 0 and self.paths[start[0]][start[1]][2] == -2:
            self.paths[start[0]][start[1]] = (start[0], start[1], 0)
            self.set_weight_in_stack(0, start)
            # self.debug.bprint(f"Path Detected: {start}: {self.paths[start[0]][start[1]]}")
        # blocked path
        elif weight == -1 and self.paths[start[0]][start[1]][2] in (-2, 0):
            self.paths[start[0]][start[1]] = (target[0], target[1], -1)
            self.set_weight_in_stack(-1, start)
            # self.debug.bprint(f"Path Blocked: {start}: {self.paths[start[0]][start[1]]}")
        elif weight > 0 and self.paths[start[0]][start[1]][2] in (-2, 0):
            self.paths[start[0]][start[1]] = (target[0], target[1], weight)
            self.paths[target[0]][target[1]] = (start[0], start[1], weight)
            self.set_weight_in_stack(1, start)
            # self.debug.bprint(f"Path Free: {start}: {self.paths[start[0]][start[1]]}")

    def add_unknown_path(self, start: Tuple[Tuple[int, int], Direction]):
        # to backtrack unknown paths
        self.paths[start] = ()
        return

    def set_weight_in_stack(self, weight, position: Tuple[Tuple[int, int], Direction]):
        """
        only used while DFS is exploration algorithm
        changes the weight of certain elements in the stack
        weight -- the weight which the elements should be set to
        position -- the position at which the weight should be set to
        """
        cnt = 0
        for i in self.stack:
            if i[0] == position[0] and i[1] == position[1]:
                if weight in (0, -2):
                    self.stack[cnt] = (i[0], i[1], weight)
                else:
                    self.stack.pop(cnt)
                # self.debug.bprint(f"{colorCodes.red}stack after deletion:{colorCodes.reset}", self.stack)
                return
            cnt += 1
        self.stack.append((position[0], position[1], weight))

    def set_attached_paths(self, node: Tuple[int, int], dirList: List[Direction]):
        """
        adds attached paths of the current node in paths
        """
        if node not in self.paths:
            self.add_node(node)
        for dir in self.paths[node]:
            if dir in dirList:
                self.add_path((node, dir), (node, dir), 0)
            else:
                self.add_path((node, dir), (node, dir), -3)

    def add_node(self, node: Tuple[int, int]):
        """
        Add new node in path dictionary with unknown path status

        Example:
            addNode((3, 4))
        :param node: 2-Tuple (posX, posY)
        :return: void
        """
        nodepaths = {}
        for dir in Direction:
            nodepaths[dir] = ((0, 0), 0, -2)
            self.stack.append((node, dir, -2))
        self.paths[node] = nodepaths

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
        pathdict = {}
        for node in self.paths:
            for dir in self.paths[node]:
                if self.paths[node][dir][2] > 0:
                    if node not in pathdict:
                        pathdict[node] = {}
                    pathdict[node][dir] = self.paths[node][dir]
        return pathdict

    def get_paths_free_blocked_detected(self):
        """
        Get all free, blocked and detected path
        :return: Dict
        """
        pathdict = {}
        for node in self.paths:
            pathdict[node] = {}
            for dir in self.paths[node]:
                if self.paths[node][dir][2] > -1:
                    pathdict[node][dir] = self.paths[node][dir]
        return pathdict

    def get_paths_free_detected(self):
        """
        Get all free and detected path
        :return: Dict
        """
        pathdict = {}
        for node in self.paths:
            for dir in self.paths[node]:
                if self.paths[node][dir][2] > 0:
                    if node not in pathdict:
                        pathdict[node] = {}
                    pathdict[node][dir] = self.paths[node][dir]
        return pathdict

    def get_paths_detected_unknown(self):
        """
        Get all detected and unknown path
        :return: Dict
        """
        pathdict = {}
        for node in self.paths:
            for dir in self.paths[node]:
                if self.paths[node][dir][2] in (0, -2):
                    if node not in pathdict:
                        pathdict[node] = {}
                    pathdict[node][dir] = self.paths[node][dir]
        return pathdict

    def set_start(self, coord: List[int], orientation: Direction):
        """
        Set start node of planet. Tuple is new set at every node

        Examples:
            setStart((42, 42), Direction.NORTH)
        : return: void
        """
        self.start = (coord, orientation)

    def set_start_coord(self, coord: Tuple[int, int]):
        """
        Set start coordinates of planet. Tuple is new set at every node

        Examples:
            setStartCoord((42, 42))
        : return: void
        """
        self.start = (coord, self.start[1])

    def set_start_direction(self, orientation: Direction):
        """
        Set start orientation of planet. Direction is new set at every node

        Examples:
            setStartDirection((42, 42), Direction.NORTH)
        : return: void
        """
        self.start = (self.start[0], orientation)

    def is_known_node(self, node: Tuple[int, int]) -> bool:
        for dir in self.paths[node]:
            if self.paths[node][dir][2] == -2:
                return False
        return True

    def is_known_path(self, node: Tuple[int, int], direction: Direction) -> bool:
        """ Returns whether a path is already known.
        :param node: 2-Tuple
        :param direction: Direction
        :return: bool
        """
        if node not in self.paths:
            return False
        if self.paths[node][direction][2] > 0 or self.paths[node][direction][2] == -1:
            return True
        else:
            return False

    def get_path_target(self, node: Tuple[int, int], direction: Direction) \
            -> Optional[Tuple[Tuple[int, int], Direction]]:
        """
        Returns the target of a path.
        :param node: 2-Tuple[int, int]: Start node
        :param direction: Direction: Start direction
        :return: Optional[Tuple[Tuple[int, int], Direction]]
        """
        if node not in self.paths:
            return None
        return self.paths[node][direction][0], self.paths[node][direction][1]

    def shortest_path(self, start: Tuple[int, int], target: Tuple[int, int]) -> Union[
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
        return self.shortest_path_dijkstra(start, target)

    def shortest_path_dijkstra(self, start: Tuple[int, int], target: Tuple[int, int]) -> Union[
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
        paths = self.get_paths()
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
        shortest_path_reverse = []
        nextNode = target
        while nextNode == start:
            shortest_path_reverse.append((nextNode, table[nextNode][2]))
            nextNode = table[nextNode][1]
        shortest_path_reverse.append((nextNode, table[nextNode][2]))
        shortest_path = []
        while len(shortest_path_reverse) > 0:
            shortest_path.append(shortest_path_reverse.pop)
        return shortest_path

    def shortest_path_tutor(self, start: Tuple[int, int], target: Tuple[int, int]) -> Optional[
        List[Tuple[Tuple[int, int], Direction]]]:
        """
        Returns a shortest path between two nodes
        *** Method from Tutor Planet ***
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
        all_paths = self.get_paths()
        unchecked_verts = set(all_paths.keys())

        if target not in unchecked_verts:
            return None

        self.init_dicts_tutor(start, distance, predecessor, unchecked_verts)
        while unchecked_verts:
            cur_vertex = None
            min_dist = math.inf
            for tup in unchecked_verts:
                if distance[tup] < min_dist:
                    min_dist = distance[tup]
                    cur_vertex = tup
            if cur_vertex is None:
                return None
            unchecked_verts.remove(cur_vertex)
            if cur_vertex == target:
                break
            for neighbor in self.get_neighbor_tutor(cur_vertex, all_paths):
                if neighbor[0] in unchecked_verts:
                    self.update_distance_tutor(cur_vertex, neighbor, distance, predecessor)
        return self.build_shortest_path_tutor(target, predecessor, all_paths)

    def init_dicts_tutor(self, start, distance, predecessor, unchecked_verts):
        # *** Method from Tutor Planet ***
        for tup in unchecked_verts:
            distance[tup] = math.inf
            predecessor[tup] = None
        distance[start] = 0

    def get_neighbor_tutor(self, cur_vertex, all_paths):
        # *** Method from Tutor Planet ***
        return {(tup, weight) for tup, _, weight in all_paths[cur_vertex].values()}

    def update_distance_tutor(self, cur_vertex, neighbor, distance, predecessor):
        # *** Method from Tutor Planet ***
        alternative_dist = distance[cur_vertex] + neighbor[1]
        if alternative_dist < distance[neighbor[0]]:
            distance[neighbor[0]] = alternative_dist
            predecessor[neighbor[0]] = cur_vertex

    def build_shortest_path_tutor(self, target, predecessor, all_paths):
        # *** Method from Tutor Planet ***
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

    def get_paths_with_wrong_weight(self) -> List[Tuple[Tuple[int, int], Direction]]:
        """
        returns all paths that are either weight -3, -1 or >0
        """
        discovered: List[Tuple[Tuple[int, int], Direction]] = []
        paths = self.get_paths()
        for path in paths:
            for dir in paths[path]:
                weight = paths[path][dir][2]
                if weight != 0 and weight != -2:
                    discovered.append((path, dir))
        return discovered

    def update_stack(self, discovered: List[Tuple[Tuple[int, int], Direction]]):
        """
        takes a list with all known path beginnings and removes them from the stack
        discovered -- paths that should be reomved from the stack
        """
        for beginning in self.stack:
            if (beginning[0], beginning[1]) in discovered:
                self.stack.remove(beginning)

    def dfs(self) -> Direction:
        for path in self.stack:
            if path[2] != 0 and path[2] != -2:
                # remove all paths that are either blocked, not there or already known
                self.stack.remove(path)
        # paths = self.getPathsDetectedUnknown()
        # for path in paths.values():
        #     for i in path.values():
        #         if i not in self.stack and (i[2] == 0 or i[2] == -2):
        #             self.stack.append(i)
        if not self.stack == []:
            return self.stack[-1][1]

        else:
            return

    def get_direction_djikstra_list(self):
        # current node
        for dir in self.paths[self.start[0]]:
            if self.paths[self.start[0]][dir][2] in [0, -2]:
                return dir

        # other nodes
        unknownNode: Dict = self.get_paths_detected_unknown()
        if unknownNode == {}:
            return None
        unknownNode: List = unknownNode.keys()
        unknownNodeDistance: Dict = {}
        unknownNodeDir: Dict = {}
        for node in unknownNode:
            pathSteps: List = self.shortest_path_tutor(self.start[0], node)
            if pathSteps is None:
                continue
            weight = 0
            for step in pathSteps:
                weight += self.paths[step[0]][step[1]][2]
            unknownNodeDistance[node] = weight
            unknownNodeDir[node] = pathSteps[0][1]
        self.debug.bprint(f"unknownNodeDistance: {unknownNodeDistance}")
        if unknownNodeDistance == {}:
            # if only unreachable nodes are left
            return None
        # distance = sorted(unknownNodeDistance.values())[0]

        result_node = min(unknownNodeDistance, key=unknownNodeDistance.get)
        distance = unknownNodeDistance[result_node]
        self.debug.bprint(f"Target node to explored: {result_node} (Distance: {distance})")
        for node in unknownNodeDistance:
            if unknownNodeDistance[node] == distance:
                return unknownNodeDir[node]
        return None

    def get_next_direction(self) -> Direction:
        """
        Return next direction.
        return: Direction
        """
        nextDir = None
        if self.target is not None:
            shortestPath = self.shortest_path_tutor(self.start[0], self.target[0])
            if shortestPath is not None:
                if shortestPath != []:
                    # self.debug.bprint(f"shortestPath: {shortestPath}")
                    return shortestPath[0][1]
                else:
                    return shortestPath
            else:
                # self.debug.bprint("shortestPath is None")
                pass
        if nextDir is None:
            # self.debug.bprint("nextDir =",self.DFS(), "stack =", self.stack)
            # return self.DFS()
            nextDir = self.get_direction_djikstra_list()
            # self.debug.bprint("nextDir =", nextDir)
        return nextDir
