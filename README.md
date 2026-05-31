# Manish Shrestha's Portfolio AI Assistant

An intelligent, Retrieval-Augmented Generation (RAG) powered AI assistant designed for Manish Shrestha's portfolio website. This assistant provides a conversational interface for visitors to learn about Manish's background, skills, work experience, and projects.

## 🚀 Features

- **Conversational AI**: Powered by Google's Gemini models for natural and accurate responses.
- **RAG Pipeline**: Built with LlamaIndex to retrieve relevant information from Manish's resume and GitHub profile.
- **Multi-source Ingestion**:
  - **Resume Data**: Structured ingestion from `manish_details.json`.
  - **GitHub Integration**: Fetches repository details, languages, and README snippets directly from GitHub.
- **Persistent Memory**: Supports session-based chat memory, allowing for follow-up questions.
- **Vector Search**: Efficient similarity search using FAISS (Facebook AI Similarity Search).
- **Rate Limiting**: Built-in protection against API abuse.
- **FastAPI Backend**: Modern, high-performance web API with CORS support.

## 🛠️ Tech Stack

- **Framework**: [LlamaIndex](https://www.llamaindex.ai/)
- **LLM & Embeddings**: [Google Gemini](https://ai.google.dev/) (`gemini-3.1-flash-lite`, `gemini-embedding-001`)
- **API Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Vector Store**: [FAISS](https://github.com/facebookresearch/faiss)
- **Data Ingestion**: Python `requests`, `json`
- **Configuration**: `python-dotenv`

## ⚙️ Setup & Installation

### 1. Prerequisites

- Python 3.9+
- A Google AI (Gemini) API Key. Get one [here](https://aistudio.google.com/app/apikey).
- (Optional) A GitHub Personal Access Token for repository ingestion.

### 2. Installation

Clone the repository and install the dependencies:

```bash
git clone <repository-url>
cd ai-assistant
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory and add the following:

```env
GOOGLE_API_KEY=your_google_api_key_here
GITHUB_ACCESS_TOKEN=your_github_token_here (optional)
ALLOWED_ORIGIN=http://localhost:3000 (or your frontend URL)
```

### 4. Data Ingestion

Before running the API, you need to ingest the data and build the vector index:

```bash
python ingestion.py
```
This will process the local resume data and GitHub repositories, then save the index to the `./storage` directory.

## 🖥️ Usage

### Start the API Server

```bash
fastapi dev main.py
```

The server will be available at `http://127.0.0.1:8000`.

### API Endpoints

- **GET `/`**: Welcome message.
- **GET `/health`**: Health check.
- **POST `/chat`**: Chat with the assistant.
  - **Request Body**:
    ```json
    {
      "message": "What are Manish's core technical skills?",
      "session_id": "optional-unique-session-id"
    }
    ```
  - **Response**:
    ```json
    {
      "response": "Manish has extensive experience in AI/ML, full-stack development, and cloud architecture...",
      "session_id": "optional-unique-session-id"
    }
    ```

## 📂 Project Structure

- `main.py`: FastAPI application and API routes.
- `ingestion.py`: Script to load data and build/update the FAISS index.
- `retriever.py`: Manages index loading, chat engine initialization, and session memory.
- `config.py`: Configuration management and environment variable validation.
- `rate_limiter.py`: Simple in-memory rate limiting logic.
- `prompt_templates.py`: System and chat prompts for the LLM.
- `data_source/`: Scripts for fetching data from different sources (GitHub, JSON).
- `data/`: Local data files (e.g., `manish_details.json`).
- `storage/`: Local directory where the FAISS index is persisted.

## 📝 License

This project is private and intended for use with Manish Shrestha's portfolio.
