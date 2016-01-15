#!/usr/bin/env python
from socket import gethostname

import rospy
import tf
import math
from geometry_msgs.msg import PoseStamped, Vector3
from swarming_turtles_msgs.msg import Turtles, CommunicationProtocol
from swarming_turtles_shepherd.srv import *
from std_msgs.msg import Bool
from stage_ros.msg import Stall
#from swarming_turtles_navigation.move_random import dist_vec
import swarming_turtles_navigation.move_random as utils

turtles = []
own_name = 'mitro' # gethostname()  # hostname used for communication
robot_in_collision = False

tf_listener = None
comm_pub = None

HIVE_FRAME = rospy.get_param('hive_frame', '/hive')
BASE_FRAME = rospy.get_param('shepherd_base_frame', '/robot_0/base_link')
food = None
#bark_time = 0
#bark_counter = 0
#time_now = 0
#time_past = 0


active = False

SIMULATION = True
SEEN_DIST = rospy.get_param('seen_dist_shepherd', 1)
SEEN_ANG = rospy.get_param('seen_ang_shepherd', math.pi/4.0)


def rob_debug():
    global own_name
    global robot_in_collision
    pos = utils.get_own_pose()
    x = format(pos.pose.position.x,'.3f')
    y = format(pos.pose.position.y,'.3f')
    z = format(pos.pose.orientation.z,'.3f')
    w = format(pos.pose.orientation.w,'.3f')
    return own_name, x, y, z, w, False, 0, False, robot_in_collision

def transform_pose(pose_in, frame=HIVE_FRAME):
    if tf_listener.frameExists(pose_in.header.frame_id) and tf_listener.frameExists(frame):
        tf_listener.waitForTransform(pose_in.header.frame_id, frame, pose_in.header.stamp, rospy.Duration(0.5))
        pose = tf_listener.transformPose(frame, pose_in)
        return pose
    return None


def seen_loc(pos, name):
    if not SIMULATION:
        return True
    res = transform_pose(pos, BASE_FRAME)
    if res is not None:
        if abs(utils.dist_vec(res.pose.position, Vector3())) < SEEN_DIST:
            rospy.logdebug("Turtle is in ViewDistance!")
            if abs(math.atan2(res.pose.position.y, res.pose.position.x)) < SEEN_ANG:
                rospy.logdebug("%s -> %s is in ViewAngle!", own_name, name)
                return True
    return False


def cb_set_status(request):
    global active
    #global time_now
    #global time_past
    #global bark_time 

    result = SetShepherdingStatusResponse()
    if request.target_status is False:
        active = False
	#time_past = rospy.get_time() - time_now
	#bark_time += time_past
	#rospy.loginfo("Elapsed time %i %i", time_past, bark_time)
        result.result = "Shepherding disabled"
    else:
        if food is None:
            active = False
            result.result = "Shepherding not enabled, no food found"
        else:
            active = True
            result.result = "Shepherding enabled!"
	    #time_now = rospy.get_time()
	    #rospy.loginfo("Current time %i", time_now)
    rospy.loginfo("%s -> %s ", rob_debug(), result.result)
    return result


def cb_found_turtles(msg):
    global turtles
    current_turtles = []
    # rospy.loginfo("Previous turtles: %s"%str(turtles))

    for turtle in msg.turtles:
        if seen_loc(turtle.position, turtle.name):
            current_turtles.append(turtle.name)
            if active and turtle.name not in turtles:
                bark_at(turtle)

    if active:
        turtles = current_turtles
        # rospy.loginfo("Barked at: %s"%str(turtles))


def cb_found_food(msg):
    global food
    food = transform_pose(msg)
    rospy.loginfo("%s -> Found food!", rob_debug())


def bark_at(turtle):
    msg = CommunicationProtocol()
    msg.sender = own_name
    msg.receiver = turtle.name
    msg.request = "mitro_message"
    msg.food_location = food
    msg.food_location.header.stamp = rospy.Time.now()
    turtle_pose = transform_pose(turtle.position)
    if turtle_pose is not None:
        msg.robot_location = turtle_pose
        comm_pub.publish(msg)
        #rospy.loginfo("%s -> Barked at %s", own_name, turtle.name)
	rospy.loginfo("%s -> Barked at %s ", rob_debug(), turtle.name)

def cb_stall(msg):
    global robot_in_collision
    robot_in_collision = msg.stall

def main():
    global tf_listener, comm_pub
    rospy.init_node('shepherding')
    utils.init_globals()
    rospy.Subscriber('stall', Stall, cb_stall)  # turtle in collision?

    tf_listener = tf.TransformListener()

    comm_pub = rospy.Publisher('/communication', CommunicationProtocol, queue_size=10)
    shep_pub = rospy.Publisher('/mitro_shepherd/status', Bool, queue_size=1)
    rospy.Subscriber('found_turtles', Turtles, cb_found_turtles)
    rospy.Subscriber('found_food', PoseStamped, cb_found_food)
    rospy.Service('/shepherd/set_shepherding_status', SetShepherdingStatus, cb_set_status)

    r = rospy.Rate(10)
    while not rospy.is_shutdown():
        shep_pub.publish(active)
	rospy.loginfo("%s -> Position", rob_debug())
        r.sleep()


if __name__ == "__main__":
    main()