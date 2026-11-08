import math
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from mars_msgs.msg import RoverOdometry


class SquareTestNode(Node):
    def _init_(self):
        super()._init_('square_test_node')

        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.odom_sub = self.create_subscription(
            RoverOdometry, 'rover/odom', self.odom_callback, 10
        )

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_heading = 0.0
        self.odom_received = False

    def odom_callback(self, msg: RoverOdometry):
        self.current_x = msg.x
        self.current_y = msg.y
        self.current_heading = msg.heading
        self.odom_received = True

    def publish_cmd(self, v: float, w: float):
        cmd = Twist()
        cmd.linear.x = float(v)
        cmd.angular.z = float(w)
        self.cmd_pub.publish(cmd)

    def execute_square(self):
        self.get_logger().info("Waiting for /rover/odom messages...")
        while rclpy.ok() and not self.odom_received:
            rclpy.spin_once(self, timeout_sec=0.1)

        start_x = self.current_x
        start_y = self.current_y
        self.get_logger().info(f"Starting Square Test at initial pose: ({start_x:.3f}, {start_y:.3f})")

        v_speed = 0.5 
        w_speed = 0.5  
        drive_time = 2.0 / v_speed  
        turn_time = (math.pi / 2.0) / w_speed 
        
        for i in range(4):
            self.get_logger().info(f"--- Side {i + 1}/4: Driving Straight ---")
            end_time = time.time() + drive_time
            while time.time() < end_time and rclpy.ok():
                self.publish_cmd(v_speed, 0.0)
                rclpy.spin_once(self, timeout_sec=0.05)  

            self.get_logger().info(f"--- Side {i + 1}/4: Turning 90 degrees ---")
            end_time = time.time() + turn_time
            while time.time() < end_time and rclpy.ok():
                self.publish_cmd(0.0, w_speed)
                rclpy.spin_once(self, timeout_sec=0.05)

        # Stop the rover
        self.publish_cmd(0.0, 0.0)
        time.sleep(0.5)
        rclpy.spin_once(self, timeout_sec=0.1)

        dx = self.current_x - start_x
        dy = self.current_y - start_y
        final_drift = math.sqrt(dx*2 + dy*2)

        print("\n" + "=" * 50)
        print(f"TEST COMPLETE")
        print(f"Final Position (x, y): ({self.current_x:.4f}, {self.current_y:.4f})")
        print(f"Final Heading:        {math.degrees(self.current_heading):.2f} deg")
        print(f"Total Drift Error:     {final_drift:.4f} meters ({final_drift * 100:.2f} cm)")
        print("=" * 50 + "\n")


def main():
    rclpy.init()
    node = SquareTestNode()
    try:
        node.execute_square()
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_cmd(0.0, 0.0)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
