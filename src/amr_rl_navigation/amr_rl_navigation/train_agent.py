import rclpy
from amr_rl_navigation.env_bridge import AMREnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback
import os

def main():
    print("Starting AMR RL Training Loop (Component C)...")
    
    # 1. Initialize ROS 2
    if not rclpy.ok():
        rclpy.init()

    # 2. Create the RL Environment
    # We wrap our custom AMREnv in a DummyVecEnv, which is required by Stable-Baselines3
    # even if we are only training a single robot in one environment.
    env = DummyVecEnv([lambda: AMREnv()])

    # 3. Setup Checkpointing
    # Save the Neural Network weights every 10,000 steps so we don't lose progress
    # if the simulation crashes or we stop training early.
    checkpoint_dir = './ppo_amr_models/'
    os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint_callback = CheckpointCallback(
        save_freq=10000, 
        save_path=checkpoint_dir,
        name_prefix='ppo_amr'
    )

    # 4. Initialize the PPO Agent (The Brain)
    # MlpPolicy: A standard feedforward Neural Network.
    # tensorboard_log: Where we save the training metrics so you can watch it learn live.
    print("Initializing PPO Neural Network...")
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1, 
        tensorboard_log="./ppo_amr_tensorboard/"
    )

    # 5. Start the Training Loop!
    # total_timesteps: How many total actions the robot will take before training stops.
    # For a simple arena, 50,000 to 100,000 is a good starting point to see learning.
    total_timesteps = 100000
    print(f"Beginning Training for {total_timesteps} timesteps...")
    
    try:
        model.learn(
            total_timesteps=total_timesteps, 
            callback=checkpoint_callback,
            progress_bar=True
        )
        
        # 6. Save the final model
        final_model_path = os.path.join(checkpoint_dir, "ppo_amr_final")
        model.save(final_model_path)
        print(f"Training Complete! Final model saved to: {final_model_path}.zip")

    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving current model state...")
        model.save(os.path.join(checkpoint_dir, "ppo_amr_interrupted"))
    finally:
        env.close()

if __name__ == '__main__':
    main()
