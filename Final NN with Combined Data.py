# This code will train a nerual network to identify an ingrdient based off of its picture
# The first section trains the neural network
# The second section identifies a recipe with these ingredients
# References:
        # We utilized Chat.gpt to help troubleshoot our code and interpret error messages

# importing tools/functions
import torch
from torch import nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import kagglehub
import os
import pandas as pd
import random
import ast

# Transform function
transform = transforms.Compose([
    transforms.Resize((128, 128)),  # Resize images to 128x128
    transforms.ToTensor()  # Converts images to PyTorch tensors
])

# Transforms data to 128x128 sized images
training_data = datasets.ImageFolder(root="Ingredients/Training", transform=transform)
test_data = datasets.ImageFolder(root="Ingredients/Testing", transform=transform)

# Loads data
train_loader = DataLoader(training_data, batch_size=4184, shuffle=True)
test_loader = DataLoader(test_data, batch_size=587, shuffle=False)

#Defines all of the categories of fruits, vegetables, and proteins
categories = ["Amaranth", "Apple", "Banana", "beans", "Beetroot", "Bell pepper", "Bitter Gourd", 
    "Blueberry", "Bottle Gourd", "Broccoli", "Cabbage", "Cantaloupe", "Capsicum", 
    "Carrot", "Cauliflower", "chicken", "chickpea", "Chilli pepper", "Coconut", "Corn", "Cucumber", 
    "Dragon_fruit", "Eggplant", "eggs", "Fig", "fish", "Garlic", "Ginger", "Grapes", "ground beef", "Jalepeno", 
    "Kiwi", "lamb", "Lemon", "Mango", "Okra", "Onion", "Orange", "Paprika", "Pear", 
    "Peas", "Pineapple", "Pomegranate", "Potato", "Pumpkin", "Raddish", "Raspberry", 
    "Ridge Gourd", "Soy beans", "Spinach", "Spiny Gourd", "Sponge Gourd", 
    "Strawberry", "Sweetcorn", "Sweetpotato", "Tomato", "Turnip", "Watermelon"]


# select a random sample from the training set
sample_num = 2
print('Inputs sample - image size:', training_data[sample_num][0].shape)
print('Label:', training_data[sample_num][1], '\n')

import matplotlib.pyplot as plt

ima = training_data[sample_num][0]
print('Inputs sample - min,max,mean,std:', ima.min().item(), ima.max().item(), ima.mean().item(), ima.std().item())
ima = (ima - ima.mean())/ ima.std()
ima = torch.clamp(ima, 0, 1)
print('Inputs sample normalized - min,max,mean,std:', ima.min().item(), ima.max().item(), ima.mean().item(), ima.std().item())
iman = ima.permute(1, 2, 0) # needed to be able to plot
plt.imshow(iman)
plt.show()

# Definition of Convolution Neural Network
class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        # first convolution layer: 3 input channels (RGB), 32 output channels, 3x3 kernel, stride=1, padding=1
        self.conv1 = nn.Conv2d(3, 32, 3, stride=1, padding=1) # image remains same size 128x128
        
        # second convolution layer: 32 input channels, 64 output channels, 3x3 kernel, stride=1, padding=1
        self.conv2 = nn.Conv2d(32, 64, 3, stride=1, padding=1) # image is 64x64 
        
        
        # halves the height and width of input image
        self.pool = nn.MaxPool2d(2, 2)
        
        # 25% of neurons dropout to prevent overfitting
        self.dropout = nn.Dropout(0.25)
        
        # fully connected layers
        self.fc1 = nn.Linear(64 * 32 * 32, 512) # input: 65536, output: 512
        self.fc2 = nn.Linear(512, len(categories)) # input: 512, output: 58
        
    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))  # (32, 128, 128) -> (32, 64, 64)
        x = self.pool(F.relu(self.conv2(x)))  # (64, 64, 64) -> (64, 32, 32)
        
        x = x.view(x.size(0), -1)             # Flattens to (batch_size, 65536) -> 64*32*32 = 65536
        x = self.dropout(F.relu(self.fc1(x)))
        x = self.fc2(x)
        return x
    
# function for training (will be called for each epoch of training)
def train_loop(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    total_loss = 0
    correct = 0
    for batch, (X, y) in enumerate(dataloader):
        # Compute prediction and loss
        pred = model(X)
        loss = loss_fn(pred, y)

        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # tracks the total loss
        total_loss += loss.item()
        
        correct += (pred.argmax(1) == y).type(torch.float).sum().item()
        

        if batch % 100 == 0:
            loss, current = loss.item(), (batch + 1) * len(X)
            
    avg_loss = total_loss / len(dataloader)
    correct /= size
    print(f"Train Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {avg_loss:>8f} \n")
    return avg_loss

# function to evaluate testing dataset
def test_loop(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    test_loss, correct = 0, 0
    
    # Calculates the test loss
    with torch.no_grad():
        for X, y in dataloader:
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()

    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")
    return test_loss

#TRAIN THE NETWORK using functions defined above
model = CNN()

# Batch size set; note: not entire dataset size
batch_size = 128
train_dataloader = DataLoader(training_data, batch_size=batch_size)
test_dataloader = DataLoader(test_data, batch_size=batch_size)

loss_fn = nn.CrossEntropyLoss() # used for categorization
learning_rate = 1e-3
optimizer = optim.Adam(model.parameters(), lr=learning_rate) # optimizes

#Initializes arrays to store loss data
train_losses = []
test_losses = []

#Trains over 50 Epochs
epochs = 50
for t in range(epochs):
    print(f"Epoch {t+1}\n-------------------------------")
    # Trains and Tests once per epoch and saves the loss data in arrays 
    avg_training_loss = train_loop(train_dataloader, model, loss_fn, optimizer)
    avg_testing_loss = test_loop(test_dataloader, model, loss_fn)
    
    train_losses.append(avg_training_loss)
    test_losses.append(avg_testing_loss)
print("Done!")

# Plots the training and testing loss data from each epoch
plt.figure(figsize=(10, 5))
plt.plot(range(1, epochs + 1), train_losses, marker='o', color='blue', label='train loss')
plt.plot(range(1, epochs + 1), test_losses, marker='o', color='red', label='test loss')
plt.title("Loss Over Epochs")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.legend()
plt.grid(True)
plt.show()

# Identify Ingredients based on Image
sample_numbers = [90, 422]  # put any sample indices the correspond to ingredient images
predicted_classes = []
images_to_plot = []

for sample_num in sample_numbers:
    image = training_data[sample_num][0]

    # Normalize the images
    ima = (image - image.mean()) / image.std()
    ima = torch.clamp(ima, 0, 1) # clamps values to help visualize
    iman = ima.permute(1, 2, 0) # formats for Matlib plotting

    # perpares the images for plotting
    image = image.unsqueeze(0)
    with torch.no_grad():
        r = model(image)
    
    # Predicted classes
    class_index = torch.argmax(r).item()
    predicted_class = categories[class_index]

    # adds data to arrays for plotting
    predicted_classes.append(predicted_class)
    images_to_plot.append(iman)
    
# Plotting
fig, axs = plt.subplots(1, len(sample_numbers), figsize=(10, 5))
if len(sample_numbers) == 1:
    axs = [axs]  # Make sure axs is iterable

# plots each ingredient with it's specific title
for i, ax in enumerate(axs):
    ax.imshow(images_to_plot[i])
    ax.set_title(f"Ingredient: {predicted_classes[i]}")
    ax.axis('off')

print(predicted_classes)

# Print recipes with chosen ingredients

# Download latest version
path = kagglehub.dataset_download("shuyangli94/food-com-recipes-and-user-interactions")
 
print("Path to dataset files:", path)
 
files = os.listdir(path)
print(files)
 
Raw_recipes = os.path.join(path, "RAW_recipes.csv")
print(Raw_recipes)
 
Raw_recipes_file = pd.read_csv(Raw_recipes)

search_words = predicted_classes # Array of ingredients from data set
search_words = [word.lower() for word in predicted_classes]  # Normalize to lowercase
matching_indexes_30 = []
matching_indexes_60 = []

# search for ingredients in dataset
for i, row in Raw_recipes_file.iterrows():
    if all(word in row['ingredients'] for word in search_words):
        tags = ast.literal_eval(row['tags'])
        cooking_time = None

        for tag in tags:
            if tag.endswith("-minutes-or-less"):
                cooking_time = int(tag.split('-')[0])
                break

        if cooking_time and cooking_time <= 30:
            matching_indexes_30.append(i)
        elif cooking_time and cooking_time <= 60:
            matching_indexes_60.append(i)

# Select and print recipes separately for each time category
def print_recipe(matching_indexes, time_category):
    if matching_indexes:
        random_index = random.choice(matching_indexes)
        recipe_name = Raw_recipes_file.name[random_index]
        ingredients_string = Raw_recipes_file.ingredients[random_index]
        ingredients_list = ast.literal_eval(ingredients_string)
        steps_string = Raw_recipes_file.steps[random_index]
        steps_list = ast.literal_eval(steps_string)

        print(f"Chosen ingredient: {search_words}\n")
        print(f"Recipe for {time_category}:\n") # Indicate time category
        print(f"Recipe Name: {recipe_name}\n")
        print(f"Ingredients:\n")
        for ingredient_num, ingredients in enumerate(ingredients_list,1):
            print(f"{ingredient_num}. {ingredients}\n")

        print(f"Steps:\n")
        for step_num, steps in enumerate(steps_list, 1):
            print(f" Step {step_num}: {steps}\n")

        print("\n\n")

    else:
        print(f"No recipes found for {time_category} with '{search_words}'\n")

# Call the function for each time category
print_recipe(matching_indexes_30, "30 minutes or less")
print_recipe(matching_indexes_60, "60 minutes or less")