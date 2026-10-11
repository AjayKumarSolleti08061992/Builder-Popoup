# The Café Companion ☕✨
> **Google Cloud Builder Pop-Up Challenge**  
> *Design a smarter café experience powered by AI.*

![Café Companion](/static/images/hero_cafe.jpg)

**The Café Companion** is an intelligent web application designed to elevate the café experience for remote workers, casual guests, and barista teams alike. Cafés are vibrant spaces to work, meet, connect, and unwind. This solution leverages **Google Gemini AI**, **Google Cloud SQL**, and **Google Cloud Run** to make every café visit personal, convenient, and connected.

---

## 🌟 Exploration Tracks Addressed

### 1. Smarter Ordering 💬
- **Conversational Barista Agent ("Aura")**: Multi-turn natural language chat powered by Google Gemini (Gemini 2.5/1.5 Flash).
- **Dietary & Sensory Awareness**: Understands nuanced requests like *"I'm lactose intolerant and need an energy boost for afternoon coding"* or *"Recommend a sweet treat with low acidity"*.
- **Direct Cart Injection**: Aura suggests items and provides one-click `+ Add to Order` buttons inside the conversation stream.
- **Customization Engine**: Support for dairy-free milk alternatives (Oat, Almond), temperature adjustments, sweetness levels, and barista notes.

### 2. Better Waits ⏱️
- **Dynamic AI Wait Time Prediction**: Calculates realistic wait times in minutes based on active kitchen load, drink complexity, and time-of-day rush curves.
- **Live 4-Stage Preparation Pipeline**: Visual stepper tracking orders in real-time through:
  `1. Order Placed` ➔ `2. Grinding & Extraction` ➔ `3. Micro-Foam & Artistry` ➔ `4. Ready at Counter`.
- **"Best Time to Visit" Forecast**: Hourly café density chart helping remote workers identify the quietest focus windows (e.g., 2:00 PM – 4:00 PM).

### 3. Discovery (Flavor & Mood Sommelier) 🌟
- **Mood & Cognitive State Matching**: Guests select their vibe (*Deep Focus & Coding*, *Social Buzz*, *Calm & Mindful*, *Cozy Comfort*).
- **Sensory Chemistry**: Generates tailored beverage recommendations, artisanal pastry pairings, and three distinct flavor notes (e.g., *White Peach*, *Jasmine Blossom*, *Bergamot*).
- **Barista Pro-Tips**: Practical sipping guidance to maximize the specialty extraction experience.

### 4. Connect People (The Café Commons) 🤝
- **Communal Table Radar**: Guests can opt-in and publish a lightweight table card sharing what they are working on, their skills, and what they are open for (*Casual Chat*, *Silent Co-working*, *Tech Talk*).
- **AI Social Spark & Icebreakers**: Generates tailored, zero-awkwardness conversational bridges between tables based on complementary projects or mutual curiosity.

### 5. Understand the Room (Live Floor Telemetry) 📊
- **Instant Guest Feedback**: 1-tap table rating covering acoustics/noise, room temperature, ambient vibe, and custom suggestions.
- **Barista Kitchen Operations Screen**:
  - Live satisfaction gauge dial (e.g. 92% happiness).
  - Gemini AI floor synthesis summarizing customer atmosphere and room acoustics.
  - Actionable staff directives (*"Maintain lo-fi acoustic tempo"*, *"Verify oat milk inventory"*, *"Offer water refills to patrons working > 1hr"*).
  - Real-time kitchen ticket management (`Start Brewing` ➔ `Mark Ready` ➔ `Complete / Served`).

---

## ☁️ Google Cloud Technologies

| Google Technology | Role in Architecture |
|---|---|
| **Gemini APIs** (`google-genai` SDK) | Powers conversational ordering, mood discovery, social icebreakers, and room sentiment synthesis. Built-in high-fidelity fallback ensures seamless out-of-the-box evaluation without mandatory API keys. |
| **Cloud SQL** | Relational persistence for menu catalog, active orders, communal patron profiles, and table feedback using SQLAlchemy. Compatible with Cloud SQL PostgreSQL/MySQL and local SQLite. |
| **Cloud Run** | Production-ready containerized deployment using `Dockerfile`, `cloudbuild.yaml`, and one-click deployment scripts (`deploy_cloud_run.ps1` and `deploy_cloud_run.sh`). |

---

## 🚀 Quickstart: Running Locally

### 1. Prerequisites
- Python 3.10+
- Pip

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment (Optional)
Create a `.env` file in the root directory:
```env
HOST=0.0.0.0
PORT=8000
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*(Note: If no API key is provided, the application automatically uses its built-in intelligent café engine so all features work immediately!)*

### 4. Start the Application
```bash
python main.py
```
Open your browser and navigate to:  
👉 **`http://localhost:8000`**

---

## 🚢 Deploying to Google Cloud Run

Deploy directly to Google Cloud Run in minutes:

### Using PowerShell (Windows):
```powershell
.\deploy_cloud_run.ps1 -ProjectId "YOUR_GCP_PROJECT_ID"
```

### Using Bash (Linux / macOS):
```bash
chmod +x deploy_cloud_run.sh
./deploy_cloud_run.sh "YOUR_GCP_PROJECT_ID"
```

### Using Google Cloud Build CLI:
```bash
gcloud builds submit --config cloudbuild.yaml
```

---

## 🎨 Design & Code Standards
- **Vanilla CSS**: Bespoke glassmorphism, warm coffee luxury color scheme (`#0d0b09`, `#e59a38`, `#f8f5ee`), and Google Cloud accents without heavyweight third-party CSS frameworks.
- **Modern Typography**: Google Fonts (*Outfit* and *Inter*).
- **PEP 8 Compliance**: All Python backend modules strictly adhere to PEP 8 formatting standards and include comprehensive docstrings and inline comments.
