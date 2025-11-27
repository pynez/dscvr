
# dscvr
DSCVR - Music Recommendation

## Key Features & Benefits

DSCVR is a music recommendation system designed to discover new music tailored to your preferences. Key features include:

-   **Personalized Recommendations:** Leverages machine learning techniques to provide relevant music suggestions.
-   **Genre-Based Exploration:** Explore music based on predefined genres such as Alt-R&B, R&B, and Soul.
-   **User-Friendly Interface:** A React-based frontend provides an intuitive platform for interacting with the recommendation system.
-   **Data-Driven Approach:** Utilizes processed music data to refine and enhance recommendation accuracy.

## Prerequisites & Dependencies

Before you begin, ensure you have the following installed:

-   **Node.js:**  (Required for the frontend)
    -   Download from: [https://nodejs.org/](https://nodejs.org/)

-   **Python:** (Required for the backend)
    -   Download from: [https://www.python.org/](https://www.python.org/)

-   **npm:** (Node Package Manager, usually installed with Node.js)

The following dependencies are required:

**Python:**

-   Specific Python libraries are detailed in the `src/recsys` files.  You may need to install them using `pip install -r requirements.txt` (if a `requirements.txt` file exists. If not, consult the code and install manually)

**JavaScript:**

-   React
-   Vite
-   ESLint
-   Tailwind CSS

You can install the JavaScript dependencies using npm:
```bash
cd frontend
npm install
```

## Installation & Setup Instructions

Follow these steps to set up and run the DSCVR project:

1.  **Clone the Repository:**

    ```bash
    git clone <repository_url>
    cd dscvr
    ```

2.  **Set up the Python Backend:**

    -   Navigate to the backend directory (e.g., `src/recsys`).
    -   Install the required Python packages:
        ```bash
        # If a requirements.txt exists in src/recsys:
        pip install -r requirements.txt
        # Otherwise, install dependencies according to the code in etl_lastfm.py, preprocess.py and service/api.py
        ```

3.  **Set up the React Frontend:**

    -   Navigate to the frontend directory:
        ```bash
        cd frontend
        ```
    -   Install the required JavaScript packages:
        ```bash
        npm install
        ```

4.  **Configure Environment Variables (if applicable):**

    -   If the project requires environment variables, create a `.env` file in the appropriate directory (e.g., `frontend/` or the root directory).
    -   Define the necessary variables in the `.env` file.

## Usage Examples & API Documentation

### Backend Usage:

-   The main logic resides in `src/recsys`.  See the `etl_lastfm.py`, `preprocess.py`, and `recommenders/` subdirectories for the ETL process, data preprocessing and different recommendation algorithms.
-   The API can be started via `service/api.py`.  The API is defined using `schemas.py`

### Frontend Usage:

1.  **Start the Development Server:**

    ```bash
    cd frontend
    npm run dev
    ```

    This will start the React development server, usually on `http://localhost:5173/`.

2.  **Access the Application:**

    -   Open your web browser and navigate to the address provided by the development server.

## Project Structure

```
├── .DS_Store
├── .cache
├── .gitignore
├── README.md
└── data/
└── artifacts/
    ├── features.npy
    ├── id_map.json
    ├── text_svd.pkl
└── processed/
    ├── tracks_lastfm.parquet
└── seeds/
    ├── alt_rnb.json
    ├── rnb.json
    ├── soul.json
└── frontend/
    ├── .gitignore
    ├── README.md
    ├── eslint.config.js
    ├── index.html

```

### Important Files:

-   **`README.md`:**  (This file) Provides an overview of the project and instructions for setup and usage.
-   **`frontend/README.md`:**  Frontend-specific instructions and information.
-   **`frontend/index.html`:** The main HTML file for the React application.
-   **`frontend/eslint.config.js`:** ESLint configuration for code linting in the frontend.

**Backend Files**

- `src/recsys/etl_lastfm.py`: ETL process to load data from LastFM.
- `src/recsys/preprocess.py`: Preprocesses music data for the recommendation system.
- `src/recsys/recommenders/base.py`: Base class for recommendation algorithms.
- `src/recsys/recommenders/cosine.py`: Implements the cosine similarity based recommender
- `src/recsys/io.py`: Input/Output utilities.
- `src/recsys/service/schemas.py`: Schemas for the API.
- `src/recsys/service/api.py`: Defines the API endpoints using the schemas

## Configuration Options

-   The React frontend can be configured by modifying the `frontend/src/main.jsx` file.
-   The backend can be configured by modifying the files in `src/recsys`, primarily `etl_lastfm.py`, `preprocess.py` and `api.py`.

## Contributing Guidelines

We welcome contributions to DSCVR! To contribute, please follow these guidelines:

1.  **Fork the Repository:**

    -   Create your own fork of the DSCVR repository on GitHub.

2.  **Create a Branch:**

    -   Create a new branch in your fork for your feature or bug fix:
        ```bash
        git checkout -b feature/your-feature-name
        ```

3.  **Make Changes:**

    -   Implement your changes, ensuring that the code is well-documented and follows the project's coding standards.

4.  **Test Your Changes:**

    -   Test your changes thoroughly to ensure they work as expected and do not introduce any new issues.

5.  **Commit Your Changes:**

    -   Commit your changes with a clear and descriptive commit message:
        ```bash
        git commit -m "Add: Your descriptive commit message"
        ```

6.  **Push to Your Fork:**

    -   Push your changes to your fork on GitHub:
        ```bash
        git push origin feature/your-feature-name
        ```

7.  **Create a Pull Request:**

    -   Create a pull request from your branch to the main branch of the DSCVR repository.
    -   Provide a detailed description of your changes and the problem they solve.

## License Information

This project does not have a specified license.  All rights are reserved unless otherwise specified.

## Acknowledgments

-   This project utilizes data from Last.fm.
-   The React frontend is built using the Vite build tool.
-   Tailwind CSS is used for styling.
