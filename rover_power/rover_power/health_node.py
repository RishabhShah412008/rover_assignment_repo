import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
from rclpy.qos import QoSProfile, DurabilityPolicy, HistoryPolicy, ReliabilityPolicy

class HealthNode(Node):
    def __init__(self):
        super().__init__('health_node')

        latch_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )
        
        self.sub = self.create_subscription(Float32MultiArray, 'rover/power', self.on_power, 10)
        self.pub = self.create_publisher(String, 'rover/health', latch_qos)
        self.last_message_sent = None

    def on_power(self, msg):
        battery, temperature = msg.data[0], msg.data[1]
        # TODO: decide the health string and publish it
        msg_out = String()
        if temperature>70:
            msg_out.data = "OVERHEAT"
        else:
            if self.last_message_sent == "WARNING":
                if battery>43:
                    msg_out.data = "HEALTHY"
                elif 15<=battery<=43:
                    msg_out.data = "WARNING"
                elif battery<15:
                    msg_out.data = "CRITICAL"
            else:
                if battery>40:
                    msg_out.data = "HEALTHY"
                elif 15<=battery<=40:
                    msg_out.data = "WARNING"
                elif battery<15:
                    msg_out.data = "CRITICAL"

        if msg_out.data != self.last_message_sent:
            self.last_message_sent = msg_out.data
            self.pub.publish(msg_out)
            self.get_logger().info(f"battery = {battery:.1f}% temp = {temperature:.1f}C")


def main():
    rclpy.init()
    node = HealthNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()