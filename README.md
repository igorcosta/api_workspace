# API Workspace

## Project Description

API Workspace is a RESTful API demonstration designed to showcase a GitHub Workspace integration. This project aims to provide a simple yet powerful interface for managing workspaces, tasks, user profiles, and work information. Key features include user authentication, task management, workspace customization, and work information management.

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

## Work Endpoints

The API supports the following endpoints for managing work information:

- **Create a new work**: `POST /works`
  - Request: Includes details about the work such as title and description.
  - Response: Returns the created work information.

- **Retrieve work information**: `GET /works/{work_id}`
  - Request: Requires the `work_id` parameter.
  - Response: Returns the details of the specified work.

- **Update work information**: `PUT /works/{work_id}`
  - Request: Includes updated details for the work.
  - Response: Returns the updated work information.

- **Delete a work**: `DELETE /works/{work_id}`
  - Request: Requires the `work_id` parameter.
  - Response: Confirms the deletion of the specified work.

These endpoints allow for the creation, retrieval, updating, and deletion of work information, providing a comprehensive management system for work-related data.
