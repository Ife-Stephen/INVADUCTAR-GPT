import os
import json
import streamlit as st
from groq import Groq
import PyPDF2
from pdf2image import convert_from_path  # To convert PDF pages to images
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
import torchvision.transforms as transforms
from PIL import Image
from pdf2image import convert_from_path

# Load configuration from file (API Key)
working_dir = os.path.dirname(os.path.abspath(__file__))
config_data = json.load(open(f"{working_dir}/config.json"))

GROQ_API_KEY = config_data["GROQ_API_KEY"]

# Save the API key to environment variable
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Initialize Groq client for LLaMA model
client = Groq()

# Extract images from PDF files
def extract_images_from_pdf(pdf_path):
    images = convert_from_path(pdf_path, poppler_path=r'C:\Program Files (x86)\poppler-24.07.0\Library\bin')  # Adjust the path
    return images

# Custom dataset class for loading image data
class ImageDataset(Dataset):
    def __init__(self, pdf_dir, transform=None):
        self.pdf_dir = pdf_dir
        self.transform = transform
        self.images = []
        self.labels = []
        self.load_images()

    def load_images(self):
        for filename in os.listdir(self.pdf_dir):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(self.pdf_dir, filename)
                images = extract_images_from_pdf(pdf_path)
                for image in images:
                    image = image.convert('RGB')  # Ensure image is in RGB format
                    if self.transform:
                        image = self.transform(image)
                    self.images.append(image)
                    self.labels.append(0)  # Replace with actual labels if available

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        image = self.images[idx]
        if self.transform:
            image = self.transform(image)  # Apply the transformation here
        return image, self.labels[idx]

# Load your data
transform = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize images to 224x224
    transforms.ToTensor(),            # Convert images to tensor
])


# Define your model
class ImageClassifier(nn.Module):
    def __init__(self):
        super(ImageClassifier, self).__init__()
        self.fc1 = nn.Linear(3 * 224 * 224, 128)  # Adjust input size based on image size
        self.fc2 = nn.Linear(128, 2)  # Assuming binary classification

    def forward(self, x):
        x = x.view(-1, 3 * 224 * 224)  # Flatten the input
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Function to send data to Groq LLaMA API and handle the response correctly
def get_llama_response(message):
    response = client.chat.completions.create(
        messages=message,
        model="llama-3.1-70b-versatile",
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
    )
    
    if hasattr(response, 'choices') and len(response.choices) > 0:
        return response.choices[0].message.content
    else:
        return "No valid response from the LLaMA model."

# Function to evaluate the model
def evaluate_model(test_loader, model):
    model.eval()
    all_preds = []
    all_labels = []
    total_loss = 0.0
    criterion = nn.CrossEntropyLoss()

    with torch.no_grad():
        for images, labels in test_loader:
            outputs = model(images.float())  # Ensure input is float
            loss = criterion(outputs, labels)
            total_loss += loss.item()

            _, predicted = torch.max(outputs.data, 1)
            all_preds.extend(predicted.numpy())
            all_labels.extend(labels.numpy())

    # Calculate metrics
    accuracy = accuracy_score(all_labels, all_preds)
    precision = precision_score(all_labels, all_preds, average='weighted')
    recall = recall_score(all_labels, all_preds, average='weighted')
    f1 = f1_score(all_labels, all_preds, average='weighted')

    print(f'Loss: {total_loss / len(test_loader):.4f}')
    print(f'Accuracy: {accuracy * 100:.2f}%')
    print(f'Precision: {precision:.2f}')
    print(f'Recall: {recall:.2f}')
    print(f'F1 Score: {f1:.2f}')

# Function to train and evaluate the model
def train_and_evaluate(images):
    # Create dataset and dataloaders
    dataset = ImageDataset(images)
    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size])

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    # Define your training and evaluation function
def train_and_evaluate(train_loader, test_loader):
    model = ImageClassifier()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Training loop
    for epoch in range(5):  # Adjust the number of epochs as needed
        model.train()
        for images, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(images.float())  # Ensure input is float
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

        print(f'Epoch [{epoch + 1}/5], Loss: {loss.item():.4f}')

    # Evaluate the model
    evaluate_model(test_loader, model)

# Define your evaluation function
def evaluate_model(test_loader, model):
    model.eval()
    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            outputs = model(images.float())
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        print(f'Accuracy: {100 * correct / total:.2f}%')

# Load your data
transform = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize images to 224x224
])

# Set the path to the texts folder relative to the current script
texts_folder = os.path.join(os.path.dirname(__file__), 'texts')

train_dataset = ImageDataset(texts_folder, transform=transform)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# If you have a test dataset, you can similarly define it
test_dataset = ImageDataset(texts_folder, transform=transform)  # Adjust if you have a separate test folder
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# Call the training and evaluation function
train_and_evaluate(train_loader, test_loader)

    
# Main function to extract images from PDFs and train the model
def main():
    texts_dir = os.path.join(working_dir, 'texts')
    pdf_files = [f for f in os.listdir(texts_dir) if f.endswith('.pdf')]
    
    images = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(texts_dir, pdf_file)
        pdf_images = extract_images_from_pdf(pdf_path)
        images.extend(pdf_images)  # Add images extracted from the PDF

    # Train and evaluate the model
    train_and_evaluate(images)

# Call the main function
if __name__ == "__main__":
    main()

# Streamlit page configuration and other functionalities
st.set_page_config(page_title="INVADUCTAR GPT", page_icon="🩺", layout="centered")

# System message to define how the LLaMA model should behave
system_message = {
    "role": "system",
    "content": (
        "You are a helpful assistant specializing in analyzing Invasive Ductal Carcinoma medical images and answering Breast Cancer medical queries. "
        "You can interpret image analysis results and generate context-aware responses for users' questions. "
        "Always explain complex concepts in simple terms, keep your response messages short, and guide the user through medical issues they ask about."
    )
}

# Initialize message list with the system message
if "message" not in st.session_state:
    st.session_state.message = [system_message]

# Streamlit page title
st.title("🩺 INVADUCTAR GPT")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Text input field for user message
user_text = st.text_input("Enter your text here:", "")

# File uploader for image input
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

# Send button functionality
if st.button("Send"):
    # Initialize message content
    message_content = ""

    if user_text.strip() != "":
        user_message = {"role": "user", "content": user_text}
        st.session_state.chat_history.append(user_message)
        st.session_state.message.append(user_message)  # Add user message to LLaMA message list
        message_content = user_text

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        # Analyze the image
        # st.write("Analyzing the image...")
        # analysis_result = analyze_image(image)  # Uncomment if you implement image analysis
        # st.write("Image analysis complete.")

        # message_content += f"\n\nImage analysis result: {analysis_result}"

        # analysis_message = {"role": "user", "content": f"Image analysis result: {analysis_result}"}
        # st.session_state.chat_history.append(analysis_message)
        # st.session_state.message.append(analysis_message)  # Add image analysis result to LLaMA message list

    if message_content:
        st.write("Generating response using LLaMA...")
        assistant_response_content = get_llama_response(st.session_state.message)

        assistant_response = {"role": "assistant", "content": assistant_response_content}
        
        st.session_state.chat_history.append(assistant_response)
        st.session_state.message.append(assistant_response)  # Add assistant response to LLaMA message list

        for message in st.session_state.chat_history[-2:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    else:
        st.write("Please enter a message or upload an image before clicking Send.")