# SmartCabAlloc_MoveInSync: A Smart Cab Allocation System 

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Flask](https://img.shields.io/badge/Framework-Flask-orange)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

SmartCabAlloc_MoveInSync is a full-stack web application designed to simulate and manage a smart cab allocation system for corporate employee transport. It features real-time cab tracking, intelligent trip planning using real-world road networks, and a clear, interactive map-based interface for both administrators and employees.


---

### 📋 Project Presentation: [View on Canva](https://www.canva.com/design/DAGxvbPfauc/lrE7TNV_2ko1KorM0_RuSw/edit?utm_content=DAGxvbPfauc&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton) ---

## ✨ Core Features

* **Real-Time Map Dashboard:** A live dashboard for administrators to monitor the entire fleet of cabs on an interactive map.
* **Intelligent Routing:** Uses real-world road network data from OpenStreetMap to calculate the shortest travel path for trips.
* **Smart Cab Allocation:** Automatically assigns the nearest available cab to an employee's trip request.
* **Live Trip Tracking:** Employees can see their assigned cab moving towards them and then towards their destination in real-time.
* **Separate User Roles:** Distinct interfaces and functionalities for Administrators (fleet overview) and Employees (trip requests).
* **Secure Authentication:** Employs JSON Web Tokens (JWT) stored in secure `HttpOnly` cookies for authentication.
* **Realistic Cab Simulation:** A backend script simulates cab movements, either randomly when idle or along a calculated route when on a trip.
* **System Monitoring:** Integrated with `Flask-MonitoringDashboard` to track application performance and errors.

---

## 🛠️ Technical Concepts

This project leverages several key technologies and concepts to achieve its functionality:

* **Geospatial Analysis with OSMnx:** The road network of Jodhpur, Rajasthan, is downloaded from OpenStreetMap and modeled as a directed graph using the `OSMnx` library. This graph is the foundation for all routing logic.
* **Shortest Path Algorithm:** The `NetworkX` library is used to find the shortest path between two points on the graph (under the hood, this uses an algorithm like Dijkstra's), ensuring optimal routing for cabs.
* **Real-Time Communication with WebSockets:** `Flask-Socket.IO` enables bidirectional, real-time communication between the server and clients. This is how location updates are pushed instantly to the browser without needing to refresh the page.
* **Application Factory Pattern:** The Flask application is structured using the factory pattern (`create_app` function). This enhances modularity, simplifies configuration management, and makes the application more scalable and testable.
* **Database Migrations with Flask-Migrate:** `Flask-Migrate` (using Alembic) manages changes to the database schema. This allows the database structure to evolve alongside the application's models without losing data.

---

## 🚀 Setup and Installation

Follow these steps to get the project running on your local machine.

### Prerequisites

* Python 3.10+
* A Python virtual environment tool (like `venv`)

### Installation Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/shreekar2005/SmartCabAlloc_MoveInSync.git
    cd SmartCabAlloc_MoveInSync/
    ```

2.  **Set Up and Activate Virtual Environment**
    ```bash
    # Create the virtual environment
    python -m venv .venv

    # Activate it on Linux/macOS
    source .venv/bin/activate

    # Or on Windows
    # .\.venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Flask Environment**
    ```bash
    # On Linux/macOS
    export FLASK_APP=run.py

    # On Windows
    # set FLASK_APP=run.py
    ```

5.  **Initialize and Upgrade the Database**
    ```bash
    # Run 'init' ONLY if the 'migrations' directory does not exist
    flask db init

    # Create the initial migration script based on models.py
    flask db migrate -m "Initial database schema"

    # Apply the migration to create the database file (app.db)
    flask db upgrade
    ```

6.  **Generate the Road Network Graph**
    This script downloads map data from OpenStreetMap and saves it locally. It only needs to be run **once**.
    ```bash
    python generate_graph.py
    ```

---

## ▶️ How to Run the System

The system consists of two main processes that should be run in **separate terminal windows** (with the virtual environment activated in both).

#### 🖥️ Terminal 1: Start the Flask Web Server
This server handles API requests, user authentication, and serves the web pages.
```bash
python run.py
```
#### 🖥️ Terminal 2: Start the simulation for moving cabs
This should be run after server is started in first terminal (as simulation will connect with server with websockets)
```bash
python simulate_cabs.py
```
#### Now do following steps for using webapp : 
1. Signup and login as Admin in your browser
2. Signup and login as Employee in private window (incognito mode) as browser cache should not conflict
3. Split screen and monitor both Admin and Employee dashboard
4. Play with buttons like "request trip at my location", "update my location", etc
5. Enjoy my project :) 
