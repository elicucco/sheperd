from geometry_msgs.msg import PoseStamped
import tf
__author__ = 'danielclaes'
import rospy
from swarming_turtles_msgs.msg import Turtles, Turtle

RATE = 20
MAX_NUM_TURTLES = 10  # TODO Make param

TARGET_FRAME = '/hive'

def quat_msg_to_array(quat):
    return [quat.x, quat.y, quat.z, quat.w]


class FakeTurtlesDetect(object):
    def __init__(self):
        self.tf = tf.TransformListener()
        self.turtles_pub = rospy.Publisher('/found_turtles', Turtles, queue_size=1)

    def publish_turtles(self):
        turtles_msg = Turtles()
        time = rospy.Time.now()
        for i in xrange(MAX_NUM_TURTLES):
            frame = "/robot_%d/base_footprint" % i
            if not self.tf.frameExists(frame):
                # rospy.logwarn("turtle frame not found %s", frame)
                break
            turtle = Turtle()
            turtle.name = 'robot_%d' % i
            turtle.position = self.get_turtle_pose(frame, time)
            if turtle.position is not None:
                turtles_msg.turtles.append(turtle)
        self.turtles_pub.publish(turtles_msg)

    # helpers
    def transform_pose(self, pose_in, frame, time_in=None):
        if self.tf.frameExists(pose_in.header.frame_id) and self.tf.frameExists(frame):
            #
            if time_in is None:
                pose_in.header.stamp = rospy.Time.now()
            else:
                pose_in.header.stamp = time_in
                # print pose_in.header.stamp
            self.tf.waitForTransform(pose_in.header.frame_id, frame, pose_in.header.stamp, rospy.Duration(0.2))
            pose = self.tf.transformPose(frame, pose_in)
            return pose
        return None

    def get_turtle_pose(self, frame, time=None):
        pose_stamped = PoseStamped()
        if time is not None:
            pose_stamped.header.stamp = time
        else:
            pose_stamped.header.stamp = rospy.Time.now()
        pose_stamped.header.frame_id = frame
        pose_stamped.pose.orientation.w = 1.0
        return self.transform_pose(pose_stamped, TARGET_FRAME, time)


def main():
    rospy.init_node('fake_food_hive_detection')
    fake_turtles_detect = FakeTurtlesDetect()
    r = rospy.Rate(RATE)
    while not rospy.is_shutdown():
        fake_turtles_detect.publish_turtles()
        r.sleep()


if __name__ == '__main__':
    main()
