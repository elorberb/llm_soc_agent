# 🛡️ SOC Agent — LLM-Powered Security Case Assistant

This project implements a Security Operations Center (SOC) agent that helps analysts manage incident cases using natural
language. It is powered by **Azure OpenAI**, **LangGraph**, and **Chainlit**, and backed by a custom JSON-based incident
database.

## 📦 Features

- 🔍 **Query and manage security incidents**
- 📝 **Add, edit, and remove analyst notes**
- 🚦 **Update case status and severity**
- 📁 **Create and view structured incident reports**
- 🧠 **LLM-powered interactions via natural language**
- 🌐 **Interactive UI with Chainlit**

---

## 🧠 How It Works

The system is composed of:

### 1. `DBManager` (core/db_manager.py)

A lightweight database interface for managing incident cases stored in `db.json`. Supports:

- Listing, adding, editing, and deleting notes
- Changing status/severity
- Creating and querying cases

### 2. `SocAgent` (core/agent/soc_agent.py)

An LLM agent built with:

- **Azure OpenAI** as the language model
- **LangGraph** to define a reasoning loop and tool execution
- Tool functions are automatically loaded from the `DBManager`

### 3. `Chainlit` App (app.py)

Interactive frontend using Chainlit where users can chat with the SOC agent.

---

## 📁 Folder Structure

```

.
├── app.py                  # Chainlit app for interaction
├── core/
│   ├── db_manager.py       # JSON-based incident case manager
│   ├── agent/
│   │   ├── soc_agent.py    # SOC agent logic
│   │   └── state.py        # LangGraph state definition
├── db.json                 # Database of SOC incidents
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Optional project config
└── README.md

````

---

## 🚀 Running Locally

### 1. Clone the Repository

```bash
git clone https://github.com/elorberb/llm_soc_agent.git
cd llm_soc_agent
````

### 2. Setup Environment

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your `.env` file:

```env
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
OPENAI_API_VERSION=2024-04-15-preview
```

### 3. Run the App

```bash
chainlit run app.py
```

---

## 🧪 Example Interactions

> 💬 *"Add a note to incident INC-20241129-001 saying that credentials were rotated."*

> 💬 *"What is the status of incident INC-20241129-002?"*

> 💬 *"Change the severity of INC-20241129-002 to High."*

---

## 🧰 Tech Stack

* [Azure OpenAI](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
* [LangGraph](https://github.com/langchain-ai/langgraph)
* [LangChain](https://www.langchain.com/)
* [Chainlit](https://www.chainlit.io/)

---
