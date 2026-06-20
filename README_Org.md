# 🚀 Oracle AI DBA Agent

An intelligent, AI-powered assistant for **Oracle Database monitoring, diagnostics, and insights**.
Built with **Python, Streamlit, and AI integration**, this project helps DBAs quickly analyze database health and performance using natural language queries.

---

## 📌 Features

* 🔍 **Natural Language Querying**
  Ask questions like *“Top wait events”* or *“Active sessions”*

* 📊 **Real-Time Database Monitoring**

  * Top Wait Events
  * Active Sessions
  * Tablespace Usage
  * Top SQL Queries

* 🧠 **AI-Powered Explanations**
  Converts raw database output into meaningful insights

* 🖥️ **Interactive Dashboard (Streamlit)**

  * Tab-based UI (OEM-style)
  * Data tables + charts
  * Clean and responsive layout

* ⚡ **Hybrid Mode**

  * Dashboard view (default)
  * AI chat mode (on query input)

---

## 🏗️ Project Structure

```
OracleAIAgent/
│
├── app.py               # Streamlit UI
├── db_tools.py          # Database query functions
├── ai_agent.py          # AI explanation logic
├── tool_router.py       # Query routing logic
├── requirements.txt     # Dependencies
├── README.md            # Project documentation
└── .gitignore           # Ignored files
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```
git clone https://github.com/YOUR_USERNAME/oracle-ai-dba-agent.git
cd oracle-ai-dba-agent
```

---

### 2️⃣ Create virtual environment (recommended)

```
python -m venv venv
venv\Scripts\activate   # Windows
```

---

### 3️⃣ Install dependencies

```
pip install -r requirements.txt
```

---

### 4️⃣ Configure Environment Variables

Create a `.env` file:

```
DB_USER=your_username
DB_PASSWORD=your_password
DB_DSN=your_oracle_connection_string
```

---

### 5️⃣ Run the application

```
streamlit run app.py
```

---

## 📊 Usage

### 🟢 Dashboard Mode (default)

* Automatically loads database summary
* Displays:

  * Wait Events
  * Sessions
  * Tablespace
  * SQL performance

---

### 🔵 AI Query Mode

Enter queries like:

* `top wait events`
* `active sessions`
* `tablespace usage`
* `top sql`

---

### 🔴 Exit Commands

```
exit
quit
shutdown
```

---

## 🧠 Example Workflow

1. Open the dashboard
2. View real-time database metrics
3. Ask a question
4. Get:

   * Query results
   * AI-generated explanation

---

## 🛠️ Tech Stack

* **Python**
* **Streamlit**
* **Pandas**
* **Oracle Database (cx_Oracle / oracledb)**
* **AI/LLM Integration (LangChain / Ollama / OpenAI)**

---

## 🔐 Security Notes

* Do NOT commit `.env` file
* Keep database credentials secure
* Use `.gitignore` to exclude sensitive files

---

## 🚀 Future Enhancements

* ✅ Auto-refresh dashboard
* 🚨 Alert system (High CPU, waits)
* 📈 DB Health Score
* 🤖 Smarter AI recommendations
* 🌐 Deployment (Cloud / Docker)

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repo
2. Create a new branch
3. Submit a pull request

---

## 📄 License

This project is licensed under the Apache2.0 License.

---

## 🙌 Acknowledgements

Inspired by real-world Oracle DBA monitoring tools and modern AI-powered workflows.

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub!
