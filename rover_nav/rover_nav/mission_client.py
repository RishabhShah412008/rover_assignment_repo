import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from action_msgs.msg import GoalStatus
from mars_msgs.action import DriveTo
from mars_msgs.srv import SetMode


class MissionClient(Node):
    def __init__(self):
        super().__init__('mission_client')
        self.srv_client = self.create_client(SetMode, 'rover/set_mode')
        self._action_client = ActionClient(self, DriveTo, 'rover/drive_to')
        self.declare_parameter('shelter_xy', [4.0, -1.0])
        shelter_xy = self.get_parameter('shelter_xy').value
        self.shelter_x = float(shelter_xy[0])
        self.shelter_y = float(shelter_xy[1])
        self.active_goal_handle = None

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(
            f"Feedback: {feedback.distance_remaining:.2f}m left, {feedback.battery_pct:.1f}% battery"
        )

    def run_mission(self):
        self.get_logger().info('Waiting for service...')
        self.srv_client.wait_for_service()
        req = SetMode.Request()
        req.mode = "MISSION"
        srv_future = self.srv_client.call_async(req)
        rclpy.spin_until_future_complete(self, srv_future)
        if not srv_future.result().accepted:
            self.get_logger().error(f"{srv_future.result().reason}")
            return
        
        self.get_logger().info('Mode accepted. Sending goal...')
        self._action_client.wait_for_server()
        
        goal_msg = DriveTo.Goal()
        goal_msg.x = self.shelter_x
        goal_msg.y = self.shelter_y
        goal_msg.tolerance = 0.3

        send_goal_future = self._action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_callback)
            
        rclpy.spin_until_future_complete(self, send_goal_future)
        self.active_goal_handle = send_goal_future.result()

        if not self.active_goal_handle.accepted:
            self.get_logger().error('Goal rejected :(')
            return

        self.get_logger().info('Goal accepted :)')

        get_result_future = self.active_goal_handle.get_result_async()
        try:
            rclpy.spin_until_future_complete(self, get_result_future)
            status = get_result_future.result().status
            result = get_result_future.result().result

            if status == GoalStatus.STATUS_SUCCEEDED:
                self.get_logger().info(f"Mission Complete! Reached shelter. Final Error: {result.final_error:.2f}m. Battery used: {result.battery_used:.2f}")
            elif status == GoalStatus.STATUS_ABORTED:
                self.get_logger().error(f"Mission ABORTED by server! Distance remaining: {result.final_error:.2f}m. Battery used: {result.battery_used:.2f}")
            
        except KeyboardInterrupt:
            self.get_logger().warn("Ctrl+C pressed! Canceling goal...")
            cancel_future = self.active_goal_handle.cancel_goal_async()
            rclpy.spin_until_future_complete(self, cancel_future)
            self.get_logger().info("Goal canceled successfully.")


def main(args=None):
    rclpy.init(args=args)

    action_client = MissionClient()
    action_client.run_mission()
    action_client.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()