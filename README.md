# Robolab

The idea of Robolab is to program a LEGO MINDSTORMS EV3 robot that is able to follow high contrast lines on a plain map. The main job is to explore the whole map. To reduce errors a server is able to send correction mesages to the robot which the robot should be able to process. Furthermore the robot should send its position to the server at each intersection of lines.

## important files

communication.py: Contains the communcation between server and robot. The communication consists of json messages.

follow.py: Contains the PID-Line Follower to enable safe driving of the robot.

main.py: Coordinates all procedures.

odometrie.py: calculates momentary position using wheel rotationary sensors in the wheels of the robot.

planet.py: Saves data about the current map. Adds new paths between knots. Contains djikstra algorithm to calculate the shortest path to a given location

