import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_srvs.srv import Empty
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import time
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

class AMREnv(gym.Env):
    """
    Gymnasium Environment that bridges ROS 2 and Hugging Face RL.
    Controls a differential drive robot using 2D LiDAR data.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self):
        super(AMREnv, self).__init__()

        # ROS 2 Setup
        if not rclpy.ok():
            rclpy.init()
        
        self.node = Node('amr_env_bridge')
        self.callback_group = ReentrantCallbackGroup()
        
        # Publishers and Subscribers
        self.vel_pub = self.node.create_publisher(Twist, '/cmd_vel', 10)
        self.scan_sub = self.node.create_subscription(
            LaserScan, 
            '/scan', 
            self._scan_callback, 
            10,
            callback_group=self.callback_group
        )
        
        # Clients for Resetting Simulation
        self.reset_client = self.node.create_client(Empty, '/reset_simulation')
        
        # Internal State
        self.latest_scan = None
        self.collision_threshold = 0.25  # Meters
        self.max_linear_vel = 0.5        # m/s
        self.max_angular_vel = 1.0       # rad/s
        self.num_lidar_rays = 24         # Downsampled for the AI
        
        # Gymnasium Spaces
        # Action: [Linear Velocity, Angular Velocity] normalized between -1 and 1
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
        
        # Observation: Normalized LiDAR ray distances (0 to 1)
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(self.num_lidar_rays,), dtype=np.float32)

        # Start ROS 2 executor in background thread logic handled externally or via spin_once
        self.executor = MultiThreadedExecutor()
        self.executor.add_node(self.node)

    def _scan_callback(self, msg):
        self.latest_scan = msg

    def _get_obs(self):
        """Downsample and normalize LiDAR data."""
        if self.latest_scan is None:
            return np.zeros(self.num_lidar_rays, dtype=np.float32)
        
        # Get raw ranges and handle inf/nan
        ranges = np.array(self.latest_scan.ranges)
        ranges = np.nan_to_num(ranges, posinf=self.latest_scan.range_max, neginf=self.latest_scan.range_min)
        
        # Downsample rays
        indices = np.linspace(0, len(ranges) - 1, self.num_lidar_rays, dtype=int)
        sampled_ranges = ranges[indices]
        
        # Normalize by max range (10m)
        normalized_ranges = sampled_ranges / 10.0
        return normalized_ranges.astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Stop the robot
        stop_msg = Twist()
        self.vel_pub.publish(stop_msg)
        
        # Call ROS 2 Reset Service
        while not self.reset_client.wait_for_service(timeout_sec=1.0):
            self.node.get_logger().info('Reset service not available, waiting...')
        
        self.reset_client.call_async(Empty.Request())
        
        # Wait for fresh scan data
        self.latest_scan = None
        while self.latest_scan is None:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            
        observation = self._get_obs()
        info = {}
        return observation, info

    def step(self, action):
        # 1. Map action [-1, 1] to velocity limits
        # We constrain linear velocity to be positive (only drive forward for now)
        linear_x = float((action[0] + 1.0) / 2.0 * self.max_linear_vel)
        angular_z = float(action[1] * self.max_angular_vel)
        
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.vel_pub.publish(msg)
        
        # 2. Let the simulation run for a bit (acting as our 'dt')
        # In a real setup, we might wait for the next scan instead of sleep
        time.sleep(0.1)
        rclpy.spin_once(self.node, timeout_sec=0.01)
        
        # 3. Calculate Reward and Check Done
        obs = self._get_obs()
        min_distance = np.min(self.latest_scan.ranges) if self.latest_scan else 10.0
        
        terminated = False
        reward = 0.0
        
        if min_distance < self.collision_threshold:
            terminated = True
            reward = -100.0  # Crash penalty
        else:
            # Reward moving forward and staying away from obstacles
            reward = linear_x * 2.0  # Encourage speed
            reward -= abs(angular_z) * 0.1  # Discourage excessive spinning
            reward += min_distance * 0.1  # Reward distance from walls
            
        truncated = False # Not used here but required by Gymnasium
        info = {"min_distance": min_distance}
        
        return obs, reward, terminated, truncated, info

    def close(self):
        self.node.destroy_node()
        rclpy.shutdown()
