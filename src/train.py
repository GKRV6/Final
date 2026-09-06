from torch.utils.data import DataLoader, Subset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import torch
from torchvision import datasets, transforms
# Dataset path
dataset_path = r"C:\Users\NATHISH KRISHNA\Downloads\wafer_images_defects\wafer_images_defects"

# Image preprocessing
transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=3),
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# Load dataset
dataset = datasets.ImageFolder(
    root=dataset_path,
    transform=transform
)

print("Classes:", dataset.classes)
print("Number of images:", len(dataset))
from torchvision import models

# Load pretrained ResNet50
model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)

for param in model.parameters():
    param.requires_grad = False

# Unfreeze the final ResNet block
for param in model.layer4.parameters():
    param.requires_grad = True

# Replace final classification layer
model.fc = torch.nn.Linear(model.fc.in_features, 8)

# Use GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = model.to(device)

print("Model: ResNet50")
print("Device:", device)
print("Output classes:", 8)
# Split dataset into train, validation and test sets

indices = list(range(len(dataset)))
labels = dataset.targets

# 80% training, 20% temporary
train_indices, temp_indices = train_test_split(
    indices,
    test_size=0.20,
    stratify=labels,
    random_state=42
)

# Split remaining 20% into validation and test
temp_labels = [labels[i] for i in temp_indices]

val_indices, test_indices = train_test_split(
    temp_indices,
    test_size=0.50,
    stratify=temp_labels,
    random_state=42
)

train_dataset = Subset(dataset, train_indices)
val_dataset = Subset(dataset, val_indices)
test_dataset = Subset(dataset, test_indices)

print("Training images:", len(train_dataset))
print("Validation images:", len(val_dataset))
print("Test images:", len(test_dataset))
# Create DataLoaders

train_loader = DataLoader(
    train_dataset,
    batch_size=32,
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    val_dataset,
    batch_size=32,
    shuffle=False,
    num_workers=0
)

test_loader = DataLoader(
    test_dataset,
    batch_size=32,
    shuffle=False,
    num_workers=0
)

print("DataLoaders created successfully")
print("Training batches:", len(train_loader))
print("Validation batches:", len(val_loader))
print("Test batches:", len(test_loader))
# Loss function and optimizer

# Loss function and optimizer

# Calculate class weights for imbalanced dataset
class_counts = torch.bincount(
    torch.tensor([labels[i] for i in train_indices])
)

class_weights = 1.0 / class_counts.float()

# Normalize weights
class_weights = class_weights / class_weights.sum() * len(class_counts)

# Move weights to GPU
class_weights = class_weights.to(device)

criterion = torch.nn.CrossEntropyLoss(
    weight=class_weights
)

optimizer = torch.optim.Adam(
    filter(lambda p: p.requires_grad, model.parameters()),
    lr=0.0001
)

print("Loss function: CrossEntropyLoss")
print("Optimizer: Adam")

print("Loss function: CrossEntropyLoss")
print("Optimizer: Adam")
# Training

num_epochs = 5

for epoch in range(num_epochs):

    model.train()

    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in train_loader:

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        running_loss += loss.item()

        _, predicted = torch.max(outputs, 1)

        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    train_accuracy = 100 * correct / total

    print(
        "Epoch [{}/{}], Loss: {:.4f}, Training Accuracy: {:.2f}%".format(
            epoch + 1,
            num_epochs,
            running_loss / len(train_loader),
            train_accuracy
        )
    )
    # Validation and Test Evaluation

model.eval()

all_predictions = []
all_labels = []

with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(device)

        outputs = model(images)

        _, predicted = torch.max(outputs, 1)

        all_predictions.extend(predicted.cpu().numpy())
        all_labels.extend(labels.numpy())


# Test accuracy

test_accuracy = accuracy_score(all_labels, all_predictions)

print()
print("Test Accuracy: {:.2f}%".format(test_accuracy * 100))


# Classification report

print()
print("Classification Report:")

print(
    classification_report(
        all_labels,
        all_predictions,
        target_names=dataset.classes
    )
)


# Confusion matrix

print()
print("Confusion Matrix:")

print(
    confusion_matrix(
        all_labels,
        all_predictions
    )
)


# Save trained model

torch.save(
    model.state_dict(),
    "models/resnet50_wafer.pth"
)

print()
print("Model saved successfully!")
print("Saved to: models/resnet50_wafer.pth")