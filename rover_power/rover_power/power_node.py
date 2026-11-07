import random
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist

class PowerNode(Node):
    def __init__(self):
        super().__init__('power_node')
        self.declare_parameter('publish_hz', 2.0)
        self.declare_parameter('drain_coeff', 1.1)
        timer_period = 1.0 / (self.get_parameter('publish_hz').value)
        self.pub = self.create_publisher(Float32MultiArray, 'rover/power', 10)
        self.sub = self.create_subscription(Twist, 'cmd_vel', self.calc_battery_drain, 10)
        self.timer = self.create_timer(timer_period, self.tick) # 2 Hz for now
        self.clock = self.get_clock()
        self.last_tick_time = self.clock.now()
        self.battery = 100.0
        self.temperature = 20.0
        self.linear_x = 0
        self.angular_z = 0
        self.drain_coeff = self.get_parameter('drain_coeff').value
        self.time_elapsed = 0
        self.battery_drain = 0

    def calc_battery_drain(self, msg):
        self.linear_x = msg.linear.x
        self.angular_z = msg.angular.z
        

    def tick(self):
        current_time = self.clock.now()
        time_diff = current_time - self.last_tick_time
        self.time_elapsed = time_diff.nanoseconds / 1e9
        self.last_tick_time = current_time
        if 0 <= self.temperature <= 60:
            self.battery_drain = (0.05 + (abs(self.linear_x) * self.drain_coeff)) * (self.time_elapsed)
        else:
            self.battery_drain = 1.5 * (0.05 + (abs(self.linear_x) * self.drain_coeff)) * (self.time_elapsed)
        self.battery -= self.battery_drain
        self.battery = max(self.battery, 0.0)
        # TODO: change temperature by a random step of at most 0.5,
        # and keep it between -20 and 80
        self.temperature += random.uniform(-0.5, 0.5)
        if self.temperature < -20.0:
            self.temperature = -20.0
        elif self.temperature > 80.0:
            self.temperature = 80.0
        msg = Float32MultiArray()
        msg.data = [self.battery, self.temperature, self.battery_drain]
        self.pub.publish(msg)
        self.get_logger().info(f'battery = {self.battery:.1f}% temp = {self.temperature:.1f}C battery_drain = {self.battery_drain:.2f}%')

def main():
    rclpy.init()
    node = PowerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()