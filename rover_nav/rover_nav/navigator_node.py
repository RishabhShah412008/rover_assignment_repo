import math
import rclpy
import time
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import Twist
from std_msgs.msg import String, Float32MultiArray
from mars_msgs.msg import RoverOdometry
from mars_msgs.action import DriveTo
from mars_msgs.srv import SetMode
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult
from rclpy.qos import QoSProfile, DurabilityPolicy, HistoryPolicy, ReliabilityPolicy

class NavigatorNode(Node):
    def __init__(self):
        super().__init__('navigator_node')
        latch_qos = QoSProfile(
                    history=HistoryPolicy.KEEP_LAST,
                    depth=1,
                    durability=DurabilityPolicy.TRANSIENT_LOCAL,
                    reliability=ReliabilityPolicy.RELIABLE
        )
        self.cb_group = ReentrantCallbackGroup()
        self._action_server = ActionServer(
            self,
            DriveTo,
            'rover/drive_to',
            execute_callback = self.execute_drive,
            goal_callback = self.goal_callback,
            cancel_callback = self.cancel_callback,
            callback_group = self.cb_group

        )
        self.sub1 = self.create_subscription(RoverOdometry, 'rover/odom', self.odom_callback, 10, callback_group=self.cb_group)            
        self.sub2 = self.create_subscription(String, 'rover/health', self.health_callback, latch_qos, callback_group=self.cb_group)        
        self.sub3 = self.create_subscription(Float32MultiArray, 'rover/power', self.battery_callback, 10, callback_group=self.cb_group)    
        self.pub = self.create_publisher(Twist, 'cmd_vel_nav', 10)
        self.cli = self.create_client(SetMode, 'rover/set_mode', callback_group=self.cb_group)                                             

        self.x = 0.0
        self.y = 0.0
        self.rover_id = 0
        self.heading = 0.0
        self.linear_x = 0.0
        self.angular_z = 0.0
        self.health = ""
        self.active_goal_handle = None
        self.battery = 100.0
        self.temperature = 20.0
        self.battery_drain = 0.0
        self.declare_parameter('shelter_xy', [4.0, -1.0])
        shelter_xy = self.get_parameter('shelter_xy').value
        self.shelter_x = float(shelter_xy[0])
        self.shelter_y = float(shelter_xy[1])
        self.last_odom_time = self.get_clock().now()

    def health_callback(self, msg):
        self.health = msg.data

    def odom_callback(self, msg):
        self.x = msg.x
        self.y = msg.y
        self.heading = msg.heading
        self.rover_id = msg.rover_id
        self.linear_x = msg.velocity.linear.x
        self.angular_z = msg.velocity.angular.z
        self.last_odom_time = self.get_clock().now()

    def battery_callback(self, msg):
        if len(msg.data) >= 3:
            self.battery, self.temperature, self.battery_drain = msg.data

    def goal_callback(self, goal_request):
        self.get_logger().info(f"Received goal request: x={goal_request.x:.2f}, y={goal_request.y:.2f}")
        if self.active_goal_handle is not None:
            self.get_logger().warn("Goal rejected: another goal is already running")
            return GoalResponse.REJECT
        if self.health == "CRITICAL" or self.health == "OVERHEAT":
            self.get_logger().warn(f"Goal rejected due to health status: {self.health}")
            return GoalResponse.REJECT
        if not self.cli.wait_for_service(timeout_sec = 1.0):
            self.get_logger().warn("SetMode service unavailable! Rejecting goal.")
            return GoalResponse.REJECT
        req = SetMode.Request()
        req.mode = "MISSION"
        future = self.cli.call_async(req)
        deadline = time.time() + 1.0
        while not future.done() and time.time() < deadline:
            time.sleep(0.01)
        if not future.done():
            self.get_logger().warn("Goal rejected: SetMode service timed out.")
            return GoalResponse.REJECT
        if future.result() is None or not future.result().accepted:
            reason = future.result().reason if future.result() else "Timeout"
            self.get_logger().warn(f"Goal rejected by DriveNode: {reason}")
            return GoalResponse.REJECT

        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info("Cancellation requested by client.")
        return CancelResponse.ACCEPT

    def stop_rover(self):
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0
        self.pub.publish(msg)

    def execute_drive(self, goal_handle):
        self.active_goal_handle = goal_handle
        try:
            return self._run_drive(goal_handle)
        finally:
            self.active_goal_handle = None

    def _run_drive(self, goal_handle):
        self.get_logger().info("Executing mission . . . . ")
        target_x = goal_handle.request.x if goal_handle.request.x != 0.0 else self.shelter_x
        target_y = goal_handle.request.y if goal_handle.request.y != 0.0 else self.shelter_y
        tolerance = goal_handle.request.tolerance if goal_handle.request.tolerance > 0.0 else 0.3
        result = DriveTo.Result()
        feedback_msg = DriveTo.Feedback()
        start_battery = self.battery

        while rclpy.ok():
            time.sleep(0.5)

            distance_x = target_x - self.x
            distance_y = target_y - self.y
            distance = math.sqrt(distance_x**2 + distance_y**2)
            target_heading = math.atan2(distance_y, distance_x)
            heading_error = math.atan2(
                math.sin(target_heading - self.heading),
                math.cos(target_heading - self.heading)
            )

            if self.health == "CRITICAL" or self.health == "OVERHEAT":
                self.get_logger().error(f"Health: {self.health}")
                self.stop_rover()
                result.reached = False
                result.final_error = float(distance)
                result.battery_used = start_battery - self.battery
                goal_handle.abort()
                return result
            
            time_since_odom = (self.get_clock().now() - self.last_odom_time).nanoseconds / 1e9
            if time_since_odom > 1.0:
                self.get_logger().error("Odometry lost (>1s). Aborting goal.")
                self.stop_rover()
                result.reached = False
                result.final_error = float(distance)
                result.battery_used = start_battery - self.battery
                goal_handle.abort()
                return result

            if goal_handle.is_cancel_requested:
                self.get_logger().error("Goal cancelled")
                self.stop_rover()
                result.reached = False
                result.final_error = float(distance)
                result.battery_used = start_battery - self.battery
                goal_handle.canceled()
                return result

            if distance <= tolerance:
                self.stop_rover()
                self.get_logger().info("Target position reached successfully")
                result.reached = True
                result.final_error = float(distance)
                result.battery_used = start_battery - self.battery
                goal_handle.succeed()
                return result

            msg = Twist()
            if abs(heading_error) > 0.05:
                msg.linear.x = 0.0
                msg.angular.z = float(max(min(1.0 * heading_error, 0.5), -0.5))
            else:
                msg.linear.x = float(min(0.5 * distance, 0.5))
                msg.angular.z = float(max(min(1.0 * heading_error, 0.3), -0.3))
            self.pub.publish(msg)
            feedback_msg.distance_remaining = float(distance)
            feedback_msg.battery_pct = self.battery
            goal_handle.publish_feedback(feedback_msg)


def main():
    rclpy.init()
    node = NavigatorNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)           
    try:
        executor.spin()               
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()