# MIRAAT - A Generative AI Mental Health Assessment Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-05998b?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-purple?style=for-the-badge)](https://www.langchain.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

<!-- **Action Required:** Add a screenshot of your main page to the root of your project and name it `miraat-home.png` for the image below to work. -->
<p align="center">
 <img src="miraat-home.png" alt="Miraat Application Screenshot" width="800"/>
</p>


## 📖 About The Project

**Miraat** is a secure, web-based platform designed to address the challenge of scattered and unsystematic mental health assessments. It consolidates standardized psychological tests and advanced AI-driven analysis into a single, structured platform. By leveraging Generative AI (Google Gemini) through the LangChain framework, Miraat provides users with a private, data-driven path toward mental health evaluation and guidance.

The core mission is to offer an accessible preliminary assessment tool that empowers individuals to understand their mental well-being and connect with verified support resources.

---

## ✨ Key Features

*   **AI-Powered Mental Health Assessment:** Utilizes zero-shot classification and LLMs to analyze user input and identify potential mental health conditions across 13 distinct categories.
*   **Standardized Psychological Tests:** Integrates over 20 validated tests (e.g., PHQ-9, GAD-7, PCL-5) and intelligently guides the user to the relevant assessment.
*   **Personalized Conversational AI:** A context-aware chatbot, powered by Gemini, offers empathetic support and guidance based on user assessments.
*   **Secure Authentication & Data Privacy:** Implements a robust **OAuth 2.0 and JWT-based** authentication flow to ensure all user data and interactions are encrypted and private.
*   **Verified Helpline Directory:** Aggregates a directory of government and NGO mental health support contacts for immediate access to help.
*   **Assessment History Tracking:** Allows users to privately review their past assessments and interactions.
*   **Community Support:** *(In Development)* A planned feature to facilitate peer support and shared experiences.

---

## 🏗️ Architecture & Technology Stack

Miraat is built on a modern, scalable **Client-Server architecture**.

<p align="center">
  <!-- **Action Required:** Add the state diagram image to your repo and name it `miraat-state-diagram.png` -->
  <img src="miraat-state-diagram.png" alt="System State Diagram" width="600"/>
</p>

### Technology Stack

| Category         | Technology                                         |
| ---------------- | -------------------------------------------------- |
| **Backend**      | `Python`, `FastAPI`                                |
| **Frontend**     | `HTML5`, `Tailwind CSS`, `JavaScript`              |
| **AI & LLM**     | `LangChain`, `Google Gemini`, `Hugging Face`       |
| **Database**     | `PostgreSQL`                                       |
| **Security**     | `OAuth 2.0`, `JWT`                                 |

---

## 🎯 Challenges & Solutions

This project addressed several key technical challenges:

1.  **Mental Health Classification Complexity:**
    *   **Challenge:** Symptoms of different mental health conditions often overlap, making classification difficult.
    *   **Solution:** Implemented **zero-shot classification** models to provide nuanced assessments without being explicitly trained on every label, allowing for more flexible and accurate initial categorization.

2.  **Handling a Large Library of Tests:**
    *   **Challenge:** Managing the logic, rendering, and scoring for 24+ different psychological tests is complex.
    *   **Solution:** Adopted a **modular architectural approach**, where each test is an independent module. This simplifies maintenance, scoring calculations, and the addition of new tests.

---

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

*   Python 3.8+
*   PostgreSQL 12+
*   Git

### Installation & Setup

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/yourusername/miraat.git
    cd miraat
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    # For Windows
    python -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up the PostgreSQL database:**
    Connect to your PostgreSQL instance and create the database.
    ```sql
    CREATE DATABASE miraat_db;
    ```

5.  **Configure Environment Variables:**
    Create a `.env` file in the project root and populate it with your credentials. **Do not commit this file to Git.**
    ```env
    # .env file

    # Database Configuration
    DATABASE_URL=postgresql://USERNAME:PASSWORD@localhost:5432/miraat_db

    # JWT Configuration
    SECRET_KEY=your_generated_32_byte_secret_key
    ACCESS_TOKEN_EXPIRE_MINUTES=30

    # Google Gemini API Configuration
    GOOGLE_API_KEY=your_google_api_key
    ```

6.  **Run the application:**
    The server will start on `http://localhost:8000`.
    ```sh
    uvicorn main:app --reload
    ```
    You can now access the FastAPI documentation at `http://localhost:8000/docs`.

---

## 🔮 Future Enhancements

*   **Community Interaction:** Complete the development of the peer-to-peer community features.
*   **Enhanced AI Models:** Fine-tune classification models for higher accuracy and explore more complex AI-driven interactions.
*   **Scalability:** Implement load balancing and further database optimizations to handle a larger volume of users.

---
