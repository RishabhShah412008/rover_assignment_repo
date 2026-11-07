import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
from rclpy.qos import QoSProfile, DurabilityPolicy, HistoryPolicy, ReliabilityPolicy

class MonitorNode(Node):
    def __init__(self):
        super().__init__('monitor_node')

        latch_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )

        self.sub1 = self.create_subscription(Float32MultiArray, 'rover/power', self.monitor_power, 10)
        self.sub2 = self.create_subscription(String, 'rover/health', self.monitor_health, latch_qos)
        self.timer = self.create_timer(0.5, self.print_status)
        self.battery = 0
        self.temperature = 0
        self.health = ""
        self.last_power_time = None
        self.last_health_time = None

    def monitor_power(self, msg):
        self.battery, self.temperature = msg.data[0], msg.data[1]
        self.get_logger().info(f"battery={self.battery:.1f}% temp={self.temperature:.1f} C")
        self.last_power_time = self.get_clock().now()

    def monitor_health(self, msg):
        self.health = msg.data
        self.get_logger().info(f" health: {self.health}")
        self.last_health_time = self.get_clock().now()

    def print_status(self):
        now = self.get_clock().now()
        if self.temperature is not None and self.battery is not None and self.health is not None:
            print(f"[ROVER] battery {self.battery:.1f}% | temp {self.temperature:.1f} C | health {self.health}")
        if self.last_power_time is None or (now - self.last_power_time).nanoseconds / 1e9 > 1.5:
            print("POWER: STALE")
            self.get_logger().warn("POWER: STALE")
        if self.last_health_time is None or (now - self.last_health_time).nanoseconds / 1e9 > 1.5:
            print("HEALTH: STALE")
            self.get_logger().warn("HEALTH: STALE")



def main():
    rclpy.init()
    node = MonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()