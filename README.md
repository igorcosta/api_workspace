# API Workspace

## Project Description

API Workspace is a RESTful API demonstration designed to showcase a GitHub Workspace integration. This project aims to provide a simple yet powerful interface for managing workspaces, tasks, and user profiles. Key features include user authentication, task management, and workspace customization.

## Requirements

- Python 3.8 or higher
- FastAPI 0.75.0
- Uvicorn 0.18.2
- SQLAlchemy 1.4.37
- Pydantic 1.9.1

Please refer to `requirements.txt` for specific version requirements.

## Local Development

To set up the project locally, follow these steps:

1. Clone the repository:
   ```
   git clone https://github.com/igorcosta/api_workspace.git
   ```
2. Navigate to the project directory:
   ```
   cd api_workspace
   ```
3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Start the Uvicorn server:
   ```
   uvicorn main:app --reload
   ```

This will start the API server, making it accessible on `http://localhost:8000`. You can now use the API endpoints as defined in the project documentation.

