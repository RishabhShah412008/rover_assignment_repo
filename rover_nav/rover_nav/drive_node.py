import random
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from mars_msgs.srv import SetMode
from rclpy.qos import QoSProfile, DurabilityPolicy, HistoryPolicy, ReliabilityPolicy

class DriveNode(Node):
    def __init__(self):
        super().__init__('drive_node')
        latch_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.sub = self.create_subscription(String, 'rover/health', self.scale_speed, latch_qos)
        self.nav_sub = self.create_subscription(Twist, 'cmd_vel_nav', self.nav_callback, 10)
        self.srv = self.create_service(SetMode, 'rover/set_mode', self.set_mode)
        self.linear_x = 0
        self.angular_z = 0
        self.timer1 = self.create_timer(3, self.velocity) # every 3 s
        self.timer2 = self.create_timer(0.1, self.tick) # 10 Hz
        self.declare_parameter('max_speed', 3.0)
        self.health = ""
        self.should_publish = 0

    def set_mode(self, request, response):
        response.accepted = True
        if request.mode == "AUTO":
            response.reason = "AUTO mode"
            self.should_publish = 0
        elif request.mode == "HOLD":
            response.reason = "HOLD mode(zero velocity)"
            self.should_publish = 1
        elif request.mode == "MISSION":
            if self.health == "OVERHEAT" or self.health == "CRITICAL":
                response.reason = f"Mission rejected because health is {self.health}"
                response.accepted = False
            else:
                response.reason = "Mission mode"
                self.should_publish = 2
        return response

    def scale_speed(self, msg):
        self.health = msg.data

    def velocity(self):
        self.linear_x = float(random.uniform(0.0, self.get_parameter('max_speed').value))
        self.angular_z = float(random.uniform(-0.5, 0.5))

    def tick(self):
        if self.should_publish == 0:
            output_linear_x = self.linear_x
            if self.health == "WARNING":
                output_linear_x = self.linear_x / 2
            elif self.health == "CRITICAL" or self.health == "OVERHEAT":
                output_linear_x = 0.0
            msg = Twist()
            msg.linear.x = float(output_linear_x)
            msg.angular.z = float(self.angular_z)
            self.pub.publish(msg)
        elif self.should_publish == 1:
            msg = Twist()
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            self.pub.publish(msg)
        elif self.should_publish == 2:
            pass

    def nav_callback(self, msg):
        if self.should_publish == 2:
            self.pub.publish(msg)
        
def main():
    rclpy.init()
    node = DriveNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()