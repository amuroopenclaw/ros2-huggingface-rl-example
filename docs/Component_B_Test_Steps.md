# Component B Test Steps: RL Environment Bridge

## Objective
Verify that the `gymnasium` environment (`AMREnv`) correctly interfaces with the ROS 2 simulation. We need to ensure that the environment can read LiDAR data, publish velocity commands, and calculate rewards *before* we introduce the complexity of a neural network.

## Prerequisites
1. Ensure your `colcon` workspace is built: `colcon build --symlink-install`
2. Source the workspace: `source install/setup.bash`

## Test Procedure

### Step 1: Start the Simulation (Terminal 1)
Boot up the Gazebo arena and the AMR robot model.
```bash
ros2 launch amr_rl_navigation amr_sim.launch.py
```
*Wait for Gazebo to open and the robot to spawn in the center of the walls.*

### Step 2: Run the Environment Test Script (Terminal 2)
In a fresh terminal, source your workspace and run the test script. This script bypasses the AI and manually forces the environment to take 10 steps forward.
```bash
source install/setup.bash
ros2 run amr_rl_navigation test_env
```

### Expected Output
In Terminal 2, you should see the following sequence:
1. **Reset Output:** The script will call `env.reset()`. It will print an array of 24 floating-point numbers. This is the downsampled, normalized LiDAR scan (values between 0.0 and 1.0).
2. **Step Output:** You will see 10 lines printing the current step, the calculated reward, and the minimum distance to an obstacle.
    *   *Example:* `Step 0: Reward: 1.00, Min Distance: 2.50`
3. **Visual Verification:** In Gazebo (Terminal 1), the robot should physically drive forward a short distance as the 10 steps are executed.

### Troubleshooting
*   **Robot doesn't move:** Ensure the `/cmd_vel` topic is correctly mapped in the URDF plugin.
*   **LiDAR array is all zeros/NaNs:** Ensure the robot is spawned correctly and the `/scan` topic is publishing data (verify with `ros2 topic echo /scan`).
*   **Script hangs on Reset:** Ensure the Gazebo reset service (`/reset_simulation`) is available.
