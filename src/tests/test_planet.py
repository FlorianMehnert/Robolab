#!/usr/bin/env python3

import unittest
from pprint import pprint
from planet import Direction, Planet
from typing import List, Tuple, Dict, Union


class ExampleTestPlanet(unittest.TestCase):
    def setUp(self):
        """
        Instantiates the planet data structure and fills it with paths

        +--+
        |  |
        +-0,3------+
           |       |
          0,2-----2,2 (target)
           |      /
        +-0,1    /
        |  |    /
        +-0,0-1,0
           |
        (start)

        """
        # Initialize your data structure here
        self.planet = Planet()
        self.planet.add_path(((0, 0), Direction.NORTH), ((0, 1), Direction.SOUTH), 1)
        self.planet.add_path(((0, 1), Direction.WEST), ((0, 0), Direction.WEST), 1)

    @unittest.skip('Example test, should not count in final test results')
    def test_target_not_reachable_with_loop(self):
        """
        This test should check that the shortest-path algorithm does not get stuck in a loop between two points while
        searching for a target not reachable nearby

        Result: Target is not reachable
        """
        self.assertIsNone(self.planet.shortest_path((0, 0), (1, 2)))


class TestRoboLabPlanet(unittest.TestCase):
    def setUp(self):
        """
        Instantiates the planet data structure and fills it with paths

        MODEL YOUR TEST PLANET HERE (if you'd like):
        """
        # Initialize your data structure here
        self.planet = Planet()
        self.planet.paths = {}
        self.planet.add_path(((0, 0), Direction.NORTH), ((0, 1), Direction.SOUTH), 1)
        self.planet.add_path(((0, 0), Direction.EAST), ((0, 0), Direction.EAST), -1)
        self.planet.add_path(((0, 0), Direction.SOUTH), ((0, 0), Direction.SOUTH), -3)
        self.planet.add_path(((0, 1), Direction.WEST), ((0, 0), Direction.WEST), 2)
        self.planet.add_path(((0, 1), Direction.NORTH), ((1, 1), Direction.SOUTH), 3)
        self.planet.add_path(((1, 1), Direction.WEST), ((0, 1), Direction.EAST), 4)
        self.planet.add_path(((1, 1), Direction.NORTH), ((2, 1), Direction.EAST), 4)
        self.planet.add_path(((1, 1), Direction.EAST), ((2, 1), Direction.WEST), 4)
        self.planet.add_path(((2, 1), Direction.NORTH), ((2, 1), Direction.NORTH), -3)
        self.planet.add_path(((2, 1), Direction.SOUTH), ((2, 1), Direction.SOUTH), 0)
        self.planet.add_path(((3, 3), Direction.EAST), ((3, 4), Direction.WEST), 3)
        # self.planet.add_path(...)

    def test_integrity(self):
        """
        This test should check that the dictionary returned by "planet.getPaths()" matches the expected structure
        """
        print(self.planet.paths[(0, 0)])
        self.assertEqual(self.planet.paths[(0, 0)], {
                Direction.NORTH: ((0, 1), Direction.SOUTH, 1),
                Direction.EAST: ((0, 0), 90, -1),
                Direction.SOUTH: ((0, 0), 180, -3),
                Direction.WEST: ((0, 1), Direction.WEST, 2)
                }, "Failed integrity of Node (0, 0)")
        self.assertEqual(self.planet.paths[(0, 1)], {
                Direction.NORTH: ((1, 1), Direction.SOUTH, 3),
                Direction.EAST: ((1, 1), Direction.WEST, 4),
                Direction.SOUTH: ((0, 0), Direction.NORTH, 1),
                Direction.WEST: ((0, 0), Direction.WEST, 2)
            }, "Failed integrity of Node (0, 1)")
        self.assertEqual(self.planet.paths[(1, 1)], {
                Direction.NORTH: ((2, 1), Direction.EAST, 4),
                Direction.EAST: ((2, 1), Direction.WEST, 4),
                Direction.SOUTH: ((0, 1), Direction.NORTH, 3),
                Direction.WEST: ((0, 1), Direction.EAST, 4)
            }, "Failed integrity of Node (1, 1)")
        self.assertEqual(self.planet.paths[(2, 1)], {
                Direction.NORTH: ((2, 1), Direction.NORTH, -3),
                Direction.EAST: ((1, 1), Direction.NORTH, 4),
                Direction.SOUTH: ((2, 1), Direction.SOUTH, 0),
                Direction.WEST: ((1, 1), Direction.EAST, 4)
            }, "Failed integrity of Node (2, 1)")
        self.assertEqual(self.planet.paths[(3, 3)], {
                Direction.NORTH: ((), 0, -2),
                Direction.EAST: ((3, 4), Direction.WEST, 3),
                Direction.SOUTH: ((), 0, -2),
                Direction.WEST: ((), 0, -2)
            }, "Failed integrity of Node (3, 3)")
        self.assertEqual(self.planet.paths[(3, 4)], {
                Direction.NORTH: ((), 0, -2),
                Direction.EAST: ((), 0, -2),
                Direction.SOUTH: ((), 0, -2),
                Direction.WEST: ((3, 3), Direction.EAST, 3)
            }, "Failed integrity of Node (3, 4)")

        self.assertEqual(self.planet.get_paths(), {
            (0, 0): {
                Direction.NORTH: ((0, 1), Direction.SOUTH, 1),
                Direction.WEST: ((0, 1), Direction.WEST, 2)
                },
            (0, 1): {
                Direction.NORTH: ((1, 1), Direction.SOUTH, 3),
                Direction.EAST: ((1, 1), Direction.WEST, 4),
                Direction.SOUTH: ((0, 0), Direction.NORTH, 1),
                Direction.WEST: ((0, 0), Direction.WEST, 2)
            },
            (1, 1): {
                Direction.NORTH: ((2, 1), Direction.EAST, 4),
                Direction.EAST: ((2, 1), Direction.WEST, 4),
                Direction.SOUTH: ((0, 1), Direction.NORTH, 3),
                Direction.WEST: ((0, 1), Direction.EAST, 4)
            },
            (2, 1): {
                Direction.EAST: ((1, 1), Direction.NORTH, 4),
                Direction.WEST: ((1, 1), Direction.EAST, 4)
            },
            (3, 3): {
                Direction.EAST: ((3, 4), Direction.WEST, 3)
            },
            (3, 4): {
                Direction.WEST: ((3, 3), Direction.EAST, 3)
            }
        }, "Failed integrity of getPaths()")

    def test_emptyPlanet(self):
        """
        This test should check that an empty planet really is empty
        """
        newPlanet = Planet()
        emptyDict = {}
        self.assertEqual(newPlanet.get_paths(), emptyDict, "empty planet not empty")

    def test_target(self):
        """
        This test should check that the shortest-path algorithm implemented works.

        Requirement: Minimum distance is three nodes (two paths in list returned)
        """
        assert (self.planet.shortest_path([0, 0], [1, 1]) == [None, [((0, 0), Direction.NORTH), ((0, 1), Direction.NORTH)]]), "s.p.a. doesnt work"

    def test_target_not_reachable(self):
        """
        This test should check that a target outside the map or at an unexplored node is not reachable
        """
        self.assertIsNone(self.planet.shortest_path_tutor((0, 0), (3, 3)), "target_not_reachable_test failed")

    def test_same_length(self):
        """
        This test should check that the shortest-path algorithm implemented returns a shortest path even if there
        are multiple shortest paths with the same length.

        Requirement: Minimum of two paths with same cost exists, only one is returned by the logic implemented
        """
        assert self.planet.shortest_path([1, 1], [2, 1]) == ([None, ((1, 1), Direction.NORTH)] or [None, ((1, 1), Direction.EAST)]), "same length fail"

    def test_target_with_loop(self):
        """
        This test should check that the shortest-path algorithm does not get stuck in a loop between two points while
        searching for a target nearby

        Result: Target is reachable
        """
        assert self.planet.shortest_path([0, 0], [0, 1]) == [None, ((0, 0), Direction.NORTH)], "s.p.a. got stuck between 2 points"

    def test_target_not_reachable_with_loop(self):
        """
        This test should check that the shortest-path algorithm does not get stuck in a loop between two points while
        searching for a target not reachable nearby

        Result: Target is not reachable
        """
        assert self.planet.shortest_path([0, 0], [5, 5]) == 0, "s.p.a.: target is unreachable"

    def test_exploration_completed_unreached_node(self):
        """

        """
        self.planet.start = ((0, 0), 0)

        self.planet.add_path(((0, 0), 90), ((0, 0), 90), -1)
        self.planet.add_path(((0, 0), 180), ((0, 0), 180), -1)
        self.planet.add_path(((2, 1), 180), ((2, 1), 180), -1)
        self.planet.add_path(((2, 1), 180), ((2, 1), 180), -1)
        # pprint(self.planet.paths)
        self.assertIsNone(self.planet.get_direction_djikstra_list(), "Fail!")

if __name__ == "__main__":
    unittest.main()