import rclpy
from amr_rl_navigation.env_bridge import AMREnv
import time

def main():
    print("Testing AMR Environment Bridge (Component B)...")
    
    # Initialize Environment
    env = AMREnv()
    
    try:
        print("Testing Reset...")
        obs, info = env.reset()
        print(f"Initial Observation (Downsampled LiDAR): {obs}")
        
        print("Testing Steps (Driving Forward)...")
        for i in range(10):
            # Action: [0.5 linear, 0.0 angular] -> Normalized to [1.0, 0.0]
            obs, reward, done, truncated, info = env.step([1.0, 0.0])
            print(f"Step {i}: Reward: {reward:.2f}, Min Distance: {info['min_distance']:.2f}")
            if done:
                print("Collision Detected!")
                break
        
        print("Test Complete. Check if the robot moved in Gazebo.")

    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        env.close()

if __name__ == '__main__':
    main()
