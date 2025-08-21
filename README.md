# PastisBackend

PastisBakcend is a FastAPI application built with Python. It focuses on a clean architecture and reusable services. This document provides detailed information about the project's structure, technologies, setup instructions, and development practices.

---

## **Table of Contents**

1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Project Structure](#project-structure)
4. [Setup Instructions](#setup-instructions)
5. [Development Guidelines](#development-guidelines)
6. [Code Quality and Testing](#code-quality-and-testing)
7. [Deployment](#deployment)
8. [Code Logic](#code-logic-specifics)

---

## **Project Overview**

PastisBackend is designed to manage projects and tasks effectively using FastAPI's powerful framework. The application is structured to ensure maintainability, scalability, and developer efficiency.
This is a complement focusing on the backend of the more complete description of the Pastis project that can be found [here](https://gitlab.sudouest.sii.fr/airbus/tools/pastis/pastis-frontend/-/blob/main/README.md?ref_type=heads).

**Technologies Used**:

- **Framework**: FastAPI 0.115.12
- **Code**: Python 3.8
- **Database Hosting**: [MongoDB](hub.docker.com/_/mongo)
- **Database Maintenance**: [Mongo Express](hub.docker.com/_/mongo-express)
- **Database Management**: ODMantic engines

---

## **Key Features**

- **Dynamic Task Management**: Add, edit, and delete tasks and more with real-time updates.
- **Environment Configurations**: Separate configurations for development and production stages.
- **Middleware-protected Engine**: Ensure users are logged in properly and can be remembered through disconnections.
- **Error Handling**: Global error handling using interceptors and message services.
- **Code Coverage Reports**: In-depth test coverage analysis for the entire application.

---

## **Project Structure**

The application is modularized for maintainability and scalability.\
Note: The project is currently being rebuilt, so this may change soon or already be partly modified.

```
app/
├── api/
│   ├── v1/
│   │   └── endpoints/      # API-related object interactions
│   └── deps.py             # Dependencies for object service engines
├── core/                   # Database and engine setup
├── models/                 # Backend/Database-specific object definitions
├── schemas/                # Interface object definitions for routes with frontend
├── services/               # Backend logic for database interactions
├── tests/
│   ├── test_api/           # API tests 
│   ├── test_database/      # Engine and setup unit tests
│   ├── test_domain/        # Backend services unit tests
│   └── test_utilities/     # Utility methods unit tests
├── utils/                  # Utility functions for backend
├── app1/                   # Old PASTIS API (for drafts)
├── Dockerfile              # Docker image constructor
├── docker-compose.yml      # Dockerfile instructions
├── requirements.txt        # Automatically installed technical requirements
├── main.py
└── pastis.log
```

### **Key Folders and Files**

1. **`api/`**  
   For any routes to transmit requests from the frontend and back.
2. **`core/`**  
   For the inner workings of the ODMantic engine.
3. **`models/`**  
   For backend-specific object definitions. Those fit the objects in the database.
4. **`schemas/`**  
   For interface object definitions. Those are used to communicate with the frontend.
5. **`services/`**  
   For backend-specific database interactions and logic.
6. **`utils/`**  
   For various utility functions.

---

## **Setup Instructions**

### **Prerequisites**

- Python (3.8 or later)
- Docker Desktop (includes Docker Compose)

### **Installation**

1. Clone the repository:

   ```bash
   git clone https://github.com/your-repo/pastis-backend.git
   cd pastis-backend
   ```
   
2. Run the development server:

   ```bash
   (sudo) docker compose up --build
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:8001/docs/
   ```
   This will grant you access to the SwaggerUI of FastAPI and let you test all the routes that exist. This will write into a local MongoDB database that you can find at the address:
   ```
   http://localhost:8005/
   ```

---

## **Development Guidelines**

### **Code Style**

- Follow the conventions already used in the code: e.g. <code>PascalCase</code> for class names, <code>snake_case</code> for variable and function names. Some older attributes are written in <code>camelCase</code>. You can turn those to snake case if you feel courageous enough to fix the front end as well.
- Structure each module for clear separation of concerns.

## **Branching Strategy**

- Use `main` for production-ready code only.
- Always create a branch from the current main.
- Check the tutorial in .gitlab for merge requests.
- Name your branch <issue_number>-<issue_name_in_snake_case>

---

## **Code Quality and Testing**

### **Unit Testing**

- Run tests:

  ```bash
  pip install pytest-cov
  pytest -v --cov=app/ --cov-report=term-missing app/tests
  ```
---

## **Deployment**

1. Build the project for development:

   The gitlab pipeline will deploy any commit merged to main to the development server.

2. Build the project for production:

   If the dev deployment is successful, you can add a new Tag on the most recent commit to launch deployment to the production server.

3. Rebuild the project when it's down:

   Go to GitLab -> Build -> Pipelines. Check the "Stages" column and find the latest "deploy_dev" or "deploy_prod", then re-run it using the retry icon.
   This also applies for other branches of PASTIS, a.k.a. Pastis-frontend or Pastis-auth.

4. Use Prometheus to check which services are down:

   Go to <code>10.9.0.11:9093</code> or <code>pastis-dev.sii.fr:9093</code> to check Prometheus' alert manager. If the page doesn't exist, rebuild the backend. For now, Prometheus is only available for development and *not* for production. 

---
