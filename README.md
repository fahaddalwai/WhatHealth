<h1 align="center" id="title">WhatHealth</h1>

<p align="center">
    <img src="https://socialify.git.ci/fahaddalwai/WhatHealth/image?language=1&logo=https%3A%2F%2Fencrypted-tbn0.gstatic.com%2Fimages%3Fq%3Dtbn%3AANd9GcQfhUhFzRsGczCSLgSEFpvjpkiCjvKminPxqA%26s&name=1&owner=1&stargazers=1&theme=Light)" alt="project-image">
</p>

<p id="description">
    WhatHealth is a health analytics platform that allows users to upload health data, query insights using AI, and visualize trends dynamically with interactive charts. Built with Django, Cohere AI, and Chart.js, it provides a seamless experience for users looking to extract valuable insights from their health records.
</p>

<h2>🧐 Features</h2>

Here are some of the best features of WhatHealth:

*   **AI-powered Chatbot:** Uses Cohere AI to analyze health-related queries.
*   **Dynamic Chart Generation:** Converts queries into interactive charts using Chart.js.
*   **File Upload & Processing:** Users can upload health data files for analysis.
*   **Hybrid Search RAG:** Uses BM25 and ChromaDB embeddings for optimized retrieval.
*   **Secure & Scalable Backend:** Built using Django and REST API principles.

<h2>🛠️ Installation Steps:</h2>

<p>1. Clone the repository</p>

```
git clone https://github.com/yourusername/WhatHealth.git cd WhatHealth
```



<p>2. Set up a virtual environment</p>

```
python -m venv env source env/bin/activate # On Windows use env\Scripts\activate
```

<p>3. Install dependencies</p>

```
pip install -r requirements.txt
```


<p>4. Set up environment variables</p>

Create a `.env` file in the root directory and add:

```
COHERE_API_KEY=your_api_key_here
```


<p>5. Run database migrations</p>

```
python manage.py migrate
```


<p>6. Start the server</p>

```
python manage.py runserver
```


<h2>🍰 Contribution Guidelines:</h2>

We welcome contributions to improve WhatHealth! Please ensure:

*   Clear, short, and descriptive PRs.
*   The changes add value to the project.
*   Follow best coding practices and maintain readability.

<h2>💻 Built with</h2>

Technologies used in the project:

*   Django (Backend)
*   Cohere AI (LLM for chatbot and search queries)
*   ChromaDB (Vector Database for retrieval)
*   Chart.js (For dynamic charts)
*   Tailwind CSS (Frontend styling)

<h2>🛡️ License:</h2>

Distributed under the MIT License.

---
