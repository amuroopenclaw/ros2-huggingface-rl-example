# Deep Dive: The PPO Training Loop (Component C)

## How Does a Reinforcement Learning Agent Actually Learn?

If you are new to Reinforcement Learning (RL), this document breaks down exactly what happens when you run the training loop in Component C.

Instead of writing "if/else" rules for driving (like *if wall is close, turn right*), we use RL to let the robot discover the best way to drive through **trial and error**.

### The Core Loop
The training process happens in a continuous loop:
1.  **Observation ($S_t$):** The robot looks at its sensors (the 24 downsampled LiDAR rays). This is its "State."
2.  **Action ($A_t$):** The robot's "Brain" (a Neural Network) decides what to do. It spits out two numbers: linear velocity (speed) and angular velocity (steering).
3.  **Environment Step:** We send those velocity commands to Gazebo. The robot moves physically.
4.  **Reward ($R_t$):** We calculate how good that action was.
    *   *Did you move forward?* +2 Points!
    *   *Did you crash?* -100 Points! (And the simulation resets).
5.  **Update:** The algorithm (PPO) looks at the Reward and mathematically tweaks the Neural Network to make good actions more likely and bad actions less likely next time.

---

## Why Proximal Policy Optimization (PPO)?

We use an algorithm called **PPO** from the `stable-baselines3` library. 

### 1. It's the Industry Standard
PPO is the exact same algorithm OpenAI used to train ChatGPT (RLHF) and the OpenAI Five bots that beat world champions at Dota 2. It is incredibly stable for continuous control tasks like steering a robot.

### 2. How PPO works (in plain English)
Imagine the robot finds a trick that gets a high reward (like driving perfectly straight). A naive algorithm might immediately change its entire brain to *only* drive straight forever, forgetting how to turn. 

PPO uses something called a **"Proximal" (close) constraint**. It limits how much the Neural Network is allowed to change after each batch of experiences. This prevents the robot from catastrophic forgetting and ensures the learning curve goes up smoothly instead of wildly spiking and crashing.

---

## What Happens When You Run `train_agent.py`?

When you execute Component C, the script follows this sequence:

### 1. The Environment is Wrapped
Stable-Baselines3 needs the environment to be vectorized (even if it's just one robot). We wrap our `AMREnv` in a `DummyVecEnv`.

### 2. The Neural Network is Created
We initialize the PPO agent with a **Multi-Layer Perceptron (MLP)** policy. This is the brain. It's a standard deep neural network that takes 24 inputs (LiDAR rays) and outputs 2 continuous values (steering and speed).

### 3. The "Rollout" Phase (Exploration)
The robot starts driving randomly. It has no idea what a wall is. It will crash *a lot*.
During this phase, it collects a batch of experiences: `(State, Action, Reward)`. This batch is called a "Rollout."

### 4. The "Update" Phase (Learning)
Once the rollout buffer is full (e.g., 2048 steps), the robot stops exploring. PPO takes all those experiences, calculates the "Advantage" (how much better an action was compared to what the network predicted), and updates the Neural Network weights.

### 5. TensorBoard Logging
While this happens, the script continuously writes metrics to a local folder. You can open TensorBoard in your browser and watch the `ep_rew_mean` (Average Reward per Episode) chart.
*   **Generation 1:** Reward is -100 (Crashing immediately).
*   **Generation 50:** Reward is +10 (Driving forward a bit, then crashing).
*   **Generation 500:** Reward is +500 (Navigating the arena perfectly).

### 6. Checkpointing
Every 10,000 steps, the script saves a `.zip` file of the Neural Network's brain to your hard drive. Once training is done, we use `evaluate_agent.py` to load the best `.zip` file and watch the robot drive flawlessly.
