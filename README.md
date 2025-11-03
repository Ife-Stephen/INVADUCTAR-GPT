# INVADUCTAR-GPT

# 🩺 Breast Cancer Diagnostic Assistant (AI-Powered RAG + Vision Analysis)

An AI-driven assistant that helps analyze breast cancer–related data and medical images.
This project combines **computer vision**, **retrieval-augmented generation (RAG)**, and **large language models** to provide helpful, medically cautious explanations — powered by **DeepSeek**, **Hugging Face**, and **Supabase**.

---

## 🚀 Features

* 🧠 **RAG (Retrieval-Augmented Generation)** — retrieves relevant knowledge from uploaded PDFs using **LangChain**, **pgvector**, and **Supabase**.
* 🖼️ **Image Analysis (CLIP Model)** — classifies medical images into categories like *normal*, *suspicious*, or *malignant*.
* 💬 **Conversational AI (DeepSeek)** — responds to user queries about breast cancer with friendly, cautious explanations.
* ☁️ **Supabase Cloud Storage** — stores PDF embeddings and vector indexes.
* 🔒 **Secure Environment Variables** — uses `.env` for tokens and API keys.
* 🌐 **Flask API** — deployable backend server (compatible with Render, Fly.io, or Cloud Run).

---

## 🧩 Tech Stack

| Category         | Tools / Libraries                                                          |
| ---------------- | -------------------------------------------------------------------------- |
| **Language**     | Python 3.10+                                                               |
| **Framework**    | Flask + Flask-CORS                                                         |
| **AI Models**    | DeepSeek-R1 (via Hugging Face Router), CLIP (openai/clip-vit-base-patch32) |
| **Vector Store** | Supabase pgvector                                                          |
| **Embeddings**   | `sentence-transformers/all-MiniLM-L6-v2`                                   |
| **Utilities**    | LangChain, LangGraph, FAISS, PyPDF, Pillow, Torch, Transformers            |                                           


## 🏗️ Project Structure
.
├── api_server.py           # Flask API entry point
├── agent.py                # Defines agent and tools orchestration
├── tools.py                # Vision, chat, and RAG functions
├── ingest_pdfs.py          # PDF ingestion and embedding builder
├── requirements.txt        # Dependencies
├── .env                    # Environment variables (not committed)
└── README.md

## ⚙️ Environment Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yourusername/breast-cancer-assistant.git
cd breast-cancer-assistant
```

### 2️⃣ Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in your project root:

```bash
TOKEN=your_huggingface_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_key
SUPABASE_BUCKET=rag-data
SUPABASE_TABLE=embeddings
```

---

## 🧠 Building the RAG Index

Put your medical PDFs into a `pdfs/` folder and run:

```bash
python ingest_pdfs.py
```

This will:

* Split text into semantic chunks.
* Generate embeddings.
* Upload them to your Supabase `embeddings` table.

---

## 🔍 Starting the API

```bash
python api_server.py
```

or for production (e.g. on Render):

```bash
gunicorn api_server:app --bind 0.0.0.0:$PORT
```

---

## ☁️ Deployment Notes

* **Render:** Use the “Web Service” type and add `gunicorn api_server:app` as the start command.
* **Supabase:** Enable the `vector` extension (`pgvector`) and create your `embeddings` table.
* To reduce Render memory usage, offload heavy embeddings to Supabase only.

---

## 🧪 Example API Endpoints

| Endpoint          | Method | Description                         |
| ----------------- | ------ | ----------------------------------- |
| `/analyze_image`  | POST   | Analyze uploaded image using CLIP   |
| `/rag_query`      | POST   | Ask questions from ingested PDFs    |
| `/general_chat`   | POST   | General chat about breast cancer    |
| `/explain_result` | POST   | Explain model result in human terms |

Example request:

```bash
curl -X POST http://localhost:5000/rag_query \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the symptoms of invasive ductal carcinoma?"}'
```

---

## 📦 Requirements

See [`requirements.txt`](requirements.txt), includes:

```
python-dotenv
openai
transformers
torch
torchvision
pillow
numpy
gdown
langgraph
langchain
langchain-core
langchain-community
langchain-text-splitters
flask
flask_cors
pypdf
tqdm
beautifulsoup4
lxml
accelerate
sentence-transformers
faiss-cpu
supabase
gunicorn
```

---

## 🧑‍⚕️ Disclaimer

> This tool is for **educational and research purposes only**.
> It does **not provide medical advice or diagnosis**.
> Always consult a qualified healthcare professional for medical concerns.

---

## 💡 Future Improvements

* Add **user authentication** via Supabase Auth
* Optimize inference with **quantized models** (to reduce memory)
* Deploy using **Google Cloud Run** for scalable inference



## ⭐ Acknowledgments

* [Hugging Face](https://huggingface.co) for DeepSeek & CLIP models
* [LangChain](https://www.langchain.com) for RAG pipeline
* [Supabase](https://supabase.com) for database & vector store

