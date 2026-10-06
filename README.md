Travian Automation Engine 

A robust, background-running automation service designed to manage building and resource upgrade queues for the browser-based strategy game, Travian. Built with a Python backend and a lightweight HTML/JS frontend, this tool provides a seamless dashboard for managing multiple villages, queuing upgrades, and bypassing basic anti-bot mechanisms.

✨ Key Technical Features

Intelligent Web Scraping & DOM Parsing: Utilizes BeautifulSoup4 to parse complex, dynamic HTML structures, extracting real-time resource data, building levels, and active queues directly from the server.

Concurrency & Threading: Implements background worker threads alongside a Flask web server, ensuring continuous automation cycles without blocking the user interface.

Advanced State & Session Management: Maintains persistent HTTP sessions using requests.Session(). Features an auto-recovery mechanism that silently re-authenticates if the active session expires or drops.

Anti-Bot Evasion Mechanics: Employs randomized, human-like execution delays (configurable intervals) and mimics standard browser headers to prevent detection by server security measures.

Multi-Village Architecture: Automatically maps and stores states for all associated villages, allowing independent configurations, active queues, and upgrade rules for each.

Batch Operations: Features optimized endpoints for bulk actions, such as one-click queuing of all resource fields to their maximum permissible levels (differentiated by Capital status).

🛠️ Tech Stack

Backend: Python 3, Flask, Requests, BeautifulSoup4

Frontend: HTML5, CSS3 (Glassmorphism UI design), Vanilla JavaScript (Fetch API)

Data Storage: Lightweight JSON-based local caching

🚀 Installation & Setup

Prerequisites

Ensure you have Python 3.8+ installed on your environment.

1. Clone the repository

git clone https://github.com/KluseWayne1/Travian-Builder.git
cd Travian-Auto-Builder


2. Install Dependencies

Install the required Python packages using pip:

pip install flask requests beautifulsoup4


3. Project Structure

Ensure your directory is structured as follows before running:

/Travian-Auto-Builder
│── app.py
└── templates/
    └── index.html


4. Run the Application

Start the Flask server:

python app.py


Access the web dashboard in your browser at: http://localhost:5001

🕹️ Usage Guide

Authentication: Enter your target server URL, username, and password in the portal. The backend handles the handshake and session storage.

Dashboard Navigation: Select your active village from the top dropdown. The UI will asynchronously fetch and render your current resources, real server queues, and available buildings.

Queue Management:

Click on any resource slot or building.

Set your target level in the modal and hit "Enqueue".

Toggle the "Auto-Build" switch in the settings panel to activate the background worker for that specific village.

Customizing Evasion: Adjust the fixed interval settings and toggle "Randomized Build Delays" to adjust the bot's execution footprint.

⚠️ Disclaimer

This project was developed strictly as a proof-of-concept for web scraping, session persistence, and HTTP automation workflows. Automating gameplay violates the Terms of Service of the game provider and may result in account suspension. Use responsibly and at your own risk.
