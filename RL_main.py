import csv
from heuristics.solver2_withSpaceDefrag import Solver2
from utils.inputGetter import getPackages, getULD
from utils.metrics import metrics, uldPlot, metrics_test,metrics_test_print,metrics_cost
from RL.PointerNet import PointerNet
import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn.utils.rnn import pad_sequence
import os

k=5000

def load_model(model, optimizer, path="pointer_net_checkpoint.pth"):
    if os.path.exists(path):
        checkpoint = torch.load(path)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        baseline = checkpoint['baseline']  # Load the baseline
        step = checkpoint['step']
        print(f"Model loaded from step {step}")
        return model, optimizer, baseline, step
    else:
        print("No checkpoint found, starting from scratch.")
        return model, optimizer, torch.zeros(1), 0  # Return a zero baseline if no checkpoint is found


def save_model(model, optimizer, baseline, step, path="pointer_net_checkpoint.pth"):
    # Save the model's state_dict, optimizer's state_dict, and the baseline
    torch.save({
        'step': step,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'baseline': baseline,  # Add baseline here
    }, path)
    print(f"Model saved at step {step}")


def pad_and_create_mask(sequences, padding_value=0):
    """
    Pads a batch of sequences to the maximum length in the batch and creates a mask.

    :param sequences: List of tensors representing variable-length sequences in the batch.
    :param padding_value: The value used for padding (default is 0).
    :return: padded_sequences (Tensor), mask (ByteTensor)
    """
    padded_sequences = pad_sequence(sequences, batch_first=True, padding_value=padding_value)
    
    
    # Create mask (1 for valid tokens, 0 for padded tokens)
    mask = (padded_sequences != padding_value).float()

    return padded_sequences, mask


# Example heuristic algorithm for baseline initialization
def heuristic_algorithm(packages):
    ulds = []    
    getULD(ulds)

    solver2 = Solver2(packages,ulds,True)
    solver2.solve()
    cost = metrics_cost(packages,ulds,k)
    # print(cost)
    return cost


all_rewards = []

# Dummy Reward Function (replace with your task-specific function)
def reward_function(solution, mask):
    # Example: negative distance to minimize
    # print(solution)
    
    rewards = []
    with open("solution.csv", mode="w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Sample Index", "Package Index"])
        for i, sample in enumerate(solution):
            for idx in sample:
                writer.writerow([i, idx])
        
    for i,sample in enumerate(solution):
        packages = []
        getPackages(packages,True,i+1)
        sorted_pack = []
        for idx in sample:
            idx = int(idx.item())
            if(mask[i,idx] == 0):
                continue
            sorted_pack.append(packages[idx])
        rewards.append(heuristic_algorithm(sorted_pack))
    
    # print(rewards)
    all_rewards.append(rewards)
    with open("all_rewards.csv", mode="w", newline='') as file:
        writer = csv.writer(file)
        for step, reward_list in enumerate(all_rewards):
            for reward in reward_list:
                writer.writerow([step, reward])
    # print(reward)
    ten = torch.tensor(rewards,dtype=torch.float64)
    ten = torch.log2(ten)
    ten*=100
    # print(ten)
    # ten*=-1
    # print(ten)
    return ten



def getInput():
    data = []

    for i in range(1,2):
        pacData = []
        packagest = []
        
        getPackages(packagest,test=True,idx=i)
        for ii,pck in enumerate(packagest):
            pacData.append([pck.getVolume(),pck.weight,pck.cost,int(pck.priority=="Priority")])
        features = torch.tensor(pacData)
        max_vals = features.max(axis=0).values 
        min_vals = features.min(axis=0).values 
        normalized_features = (features - min_vals) / (max_vals - min_vals)
        data.append(normalized_features) 

    data, mask = pad_and_create_mask(data)
    data = data.float()  # Convert to torch.float32
    mask = mask[:,:,0]
    # print(mask)
    
    with open("mask_initial.csv", mode="w", newline='') as file:
        writer = csv.writer(file)
        for row in mask:
            writer.writerow(row.tolist())
    
    return data,mask






# RL Training Function
def train_pointer_net(pointer_net, num_steps, batch_size, learning_rate=0.005, beta=0.1):
    optimizer = optim.Adam(pointer_net.parameters(), lr=learning_rate)

    # Initialize baseline
    baseline = torch.zeros(batch_size)

     # Load model and baseline if checkpoint exists
    pointer_net, optimizer, baseline, start_step = load_model(pointer_net, optimizer)
    
    

    for step in range(num_steps):
        
        inputs,mask = getInput()

        # Forward pass through PointerNet
        outputs, pointers = pointer_net(inputs,mask,temp=1.5)
        # print(step,"STEEPPP")


        # Calculate rewards
        rewards = reward_function(pointers, mask)

        # Calculate advantages
        advantages = rewards - baseline

        # Log probabilities of selected actions
        torch.set_printoptions(precision=8)
        probs = torch.gather(outputs, 2, pointers.unsqueeze(-1)).squeeze(-1)
        print(probs)
        probs = torch.clamp(probs, min=1e-25) 
        log_probs = torch.log(probs)
        # print(f"Shape of advantages: {advantages}")
        # print(f"Shape of log_probs: {log_probs}")
        policy_loss = (advantages.unsqueeze(-1) * log_probs).mean()
        
        # print(policy_loss)

        # Backpropagation
        optimizer.zero_grad()
        policy_loss.backward()

        # for name, param in pointer_net.named_parameters():
        #     if param.grad is not None:
        #         print(f"Gradient for {name}: {param.grad.norm()}")
        # # Gradient Clipping: Clip gradients to avoid exploding gradients
        # torch.nn.utils.clip_grad_norm_(pointer_net.parameters(), 1.0)
        # for name, param in pointer_net.named_parameters():
        #     if param.grad is not None:
        #         print(f"Clipped Gradient for {name}: {param.grad.norm()}")
        optimizer.step()

        for name, param in pointer_net.named_parameters():
            if param.requires_grad:  # We only want to print the parameters that require gradients
                # Compute the average of the parameters
                avg_value = param.data.mean().item()  # .item() to get the scalar value from a tensor
                
                print(f"Layer: {name}")
                print(f"Average Value: {avg_value}")
                print(f"Gradient for {name}: {param.grad.norm()}")
                print(f"difference: { avg_value/(param.grad.norm()*learning_rate)}")
                print("-" * 40)
                

       

        # Update baseline using moving average
        baseline = baseline + beta * (rewards - baseline)
        
        # Print progress
        if (step+1) % 10 == 0:
            print(f"Step {step}, Avg Reward: {rewards.float().mean().item()}")
            print(baseline)
            save_model(pointer_net, optimizer, baseline, step)
            print()


    print("Training complete!")

# Initialize PointerNet

hidden_dim = 450
lstm_layers = 1
dropout = 0.0
bidir = False


pointer_net = PointerNet(hidden_dim, lstm_layers, dropout, bidir)

# Training
train_pointer_net(pointer_net, num_steps=10000, batch_size=1)