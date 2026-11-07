import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from mars_msgs.msg import RoverOdometry
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult

class OdomNode(Node):
    def __init__(self):
        super().__init__('odom_node')
        self.sub = self.create_subscription(Twist, 'cmd_vel', self.update_parameters, 10)
        self.pub = self.create_publisher(RoverOdometry, 'rover/odom', 10)
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0
        self.linear_x = 0.0
        self.angular_z = 0.0
        self.timer_period = 1/20.0 # 20 Hz
        self.declare_parameter('speed_limit', 2.0)
        self.declare_parameter('rover_id', 972)
        self.declare_parameter('odom_hz', 1.0)
        self.timer1 = self.create_timer(self.timer_period, self.update_odometry)
        self.timer2 = self.create_timer(1/(self.get_parameter('odom_hz').value), self.publish_status)
        self.add_on_set_parameters_callback(self.parameters_callback)

    def parameters_callback(self, params):
        result = SetParametersResult(successful=True)
        for param in params:
            if param.name == 'speed_limit':
                if param.type_ == Parameter.Type.DOUBLE or param.type_ == Parameter.Type.INTEGER:
                    new_val = float(param.value)
                    if new_val < 0.0:
                        result.successful = False
                        result.reason = "speed_limit must be non-negative"
                        return result

                    self.speed_limit = new_val
                    self.get_logger().info(f"Live updated speed_limit to: {self.speed_limit}")
                else:
                    result.successful = False
                    result.reason = "speed_limit must be a float or integer"
                    return result

        return result

    def update_odometry(self):
        if self.angular_z != 0:
            self.x += (self.linear_x / self.angular_z) * (math.sin(self.heading + (self.angular_z*self.timer_period)) - math.sin(self.heading))
            self.y += (self.linear_x / self.angular_z) * (math.cos(self.heading) - math.cos(self.heading + (self.angular_z*self.timer_period)))
        else:
            self.x += self.linear_x * math.cos(self.heading) * self.timer_period
            self.y += self.linear_x * math.sin(self.heading) * self.timer_period
        self.heading += self.angular_z * self.timer_period
        self.heading = math.atan2(math.sin(self.heading), math.cos(self.heading))

    def update_parameters(self, msg):
        self.linear_x, self.angular_z = msg.linear.x, msg.angular.z

    def publish_status(self):
        speed_limit = self.get_parameter('speed_limit').value
        msg = RoverOdometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.rover_id = self.get_parameter('rover_id').value
        msg.x = self.x
        msg.y = self.y
        msg.heading = self.heading
        msg.velocity.linear.x = self.linear_x
        msg.velocity.angular.z = self.angular_z
        self.pub.publish(msg)
        if self.linear_x > speed_limit:
            self.get_logger().warn("Ay bro watch yo jet watch yo jet")

def main():
    rclpy.init()
    node = OdomNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()