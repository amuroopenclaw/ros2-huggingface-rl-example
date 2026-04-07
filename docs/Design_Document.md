# Project Design Document: Autonomous Mobile Robot (AMR) Navigation via Reinforcement Learning

## 1. High-Level Architecture
This project trains an Autonomous Mobile Robot (AMR) to navigate a simulated 2D environment (Gazebo) while avoiding obstacles using only a 2D LiDAR scanner. The brain of the robot is trained using Proximal Policy Optimization (PPO) via Hugging Face's integration with Stable-Baselines3.

### Core Stack
*   **Simulator:** Gazebo Classic or Ignition/Gazebo Harmonic (ROS 2 Humble/Iron compatible).
*   **Middleware:** ROS 2 (topics: `/scan` for LiDAR, `/cmd_vel` for velocity).
*   **Robot Platform:** TurtleBot3 (Waffle Pi) or generic differential drive base.
*   **Reinforcement Learning:** `stable-baselines3` (PPO) wrapped in a custom `gymnasium.Env` (Hugging Face `RLEnv` structure).

---

## 2. Component Breakdown & Test Steps

The system is decoupled into three primary testable components: the Simulator, the RL Environment Bridge, and the Training Loop.

### Component A: Simulation & ROS 2 Middleware (The World)
**Responsibility:** Spawn the robot in a walled arena with obstacles, simulate physics, and correctly publish sensor data (`/scan`) while responding to motor commands (`/cmd_vel`).

*   **Design Details:**
    *   A ROS 2 Launch file (`amr_sim.launch.py`) that boots Gazebo.
    *   Loads a custom `.world` file featuring a static walled boundary and 3-4 internal static/dynamic obstacles.
    *   Spawns a URDF/SDF model of the differential-drive robot equipped with a 360-degree LiDAR sensor.

*   **Test Steps (Component A):**
    1.  *Boot:* Run `ros2 launch amr_rl_navigation amr_sim.launch.py`. Verify Gazebo opens and the robot spawns inside the walls.
    2.  *Sensor Test:* In a new terminal, run `ros2 topic echo /scan`. Verify an array of float distance values is actively publishing at ~10Hz.
    3.  *Actuator Test:* Run `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.5}}"`. Verify the robot drives in a circle in the Gazebo UI.

### Component B: The RL Environment Bridge (`AMREnv`)
**Responsibility:** Translate ROS 2 topics into a structured `gymnasium` (Gym) environment that Stable-Baselines3 can understand.

*   **Design Details:**
    *   Inherits from `gymnasium.Env`.
    *   **Observation Space:** A normalized NumPy array representing the LiDAR scan (e.g., downsampled to 24 ray buckets, normalized between 0.0 and 1.0).
    *   **Action Space:** A continuous vector `[linear_velocity, angular_velocity]` bounded between `[-1, 1]`, mapped internally to physical limits (e.g., `max_vel = 0.5 m/s`).
    *   **Reward Function:** 
        *   `+1.0` for moving forward at max speed.
        *   `-0.5` penalty for turning too sharply (encourages smooth driving).
        *   `-100.0` catastrophic penalty for crashing (LiDAR distance < collision threshold), which triggers a `done = True`.
    *   **Reset Function:** Resets the robot's physical position in Gazebo using the `/reset_simulation` service when it crashes.

*   **Test Steps (Component B):**
    1.  *Initialization:* Run a standalone Python test script `test_env.py` that instantiates `env = AMREnv()`. Verify it connects to the ROS 2 node without crashing.
    2.  *Step Function:* Call `obs, reward, done, _, info = env.step([0.5, 0.0])` (drive straight). Verify the robot moves forward in Gazebo, `reward` is positive, and `obs` returns a valid LiDAR array.
    3.  *Reset Function:* Teleoperate the robot into a wall until it crashes. Call `env.reset()`. Verify the robot teleports back to the center of the Gazebo arena instantly.

### Component C: The PPO Training Loop (The Brain)
**Responsibility:** Utilize Hugging Face / Stable-Baselines3 to train the neural network over thousands of episodes, maximizing the reward defined in Component B.

*   **Design Details:**
    *   Initializes the `AMREnv`.
    *   Instantiates a `PPO` model with a Multi-Layer Perceptron (MLP) policy.
    *   Uses TensorBoard logging to track cumulative reward and episode length.
    *   Periodically saves the `.zip` model checkpoints to disk.

*   **Test Steps (Component C):**
    1.  *Training Boot:* Run `python3 train_agent.py`. Verify that the terminal outputs Stable-Baselines3 logging metrics (e.g., `ep_rew_mean`, `fps`).
    2.  *Learning Verification:* Let the simulation run for 50,000 timesteps. Open TensorBoard (`tensorboard --logdir ./ppo_amr_tensorboard/`). Verify that `ep_rew_mean` (average reward per episode) is trending upwards and `ep_len_mean` (survival time before crashing) is increasing.
    3.  *Inference Test:* Run `python3 evaluate_agent.py`. Verify that the script loads the saved `best_model.zip`, disables exploration noise, and the robot successfully navigates the arena without hitting walls for at least 60 seconds.

---

## 3. Directory Structure
The repository will be structured as a standard `colcon` workspace:
```text
ros2-huggingface-rl-example/
├── docs/
│   ├── proposals.md
│   ├── Design_Document.md
├── src/
│   ├── amr_rl_navigation/          # Core ROS 2 Python package
│   │   ├── launch/                 # Gazebo launch files
│   │   ├── worlds/                 # Gazebo world files (.world)
│   │   ├── amr_rl_navigation/      # Python modules
│   │   │   ├── __init__.py
│   │   │   ├── env_bridge.py       # Component B (RLEnv)
│   │   │   ├── train_agent.py      # Component C (Training Loop)
│   │   │   ├── evaluate_agent.py   # Inference script
│   │   ├── package.xml
│   │   ├── setup.py
```

## A Note on Component A: Driving the Robot
In Component A (The Simulator), the robot does **not** move autonomously yet. Because Component A isolates just the physical simulation and the ROS 2 middleware, the "brain" (the RL Agent from Component C) hasn't been connected.

The robot's wheels are driven by a ROS 2 plugin (like `libgazebo_ros_diff_drive.so`) attached to the simulated robot model. This plugin listens to a specific ROS 2 topic named `/cmd_vel` (Command Velocity). 

To test Component A, we don't use AI. We manually publish messages to `/cmd_vel` to prove the wheels work. This is typically done in two ways:
1. **Command Line (Topic Pub):** Executing `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist ...` to force a constant speed.
2. **Teleoperation:** Running a node like `ros2 run teleop_twist_keyboard teleop_twist_keyboard` to drive the robot manually with your keyboard (WASD keys).

If the robot moves when you press 'W', Component A is successfully verified. It means the simulator is correctly receiving motor commands, clearing the way for Component B and C to take over the steering wheel later.
