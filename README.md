FastBnB: A Resilient FastAPI Microservices Project
FastBnB is a backend system for an Airbnb-like rental platform, built using an event-driven microservices architecture. It demonstrates modern backend practices including asynchronous communication, caching, and containerization.

The project is divided into two core services:

Backend Service (/backend): Manages user authentication, authorization, and property (listing) management.

Booking Service (/booking-service): Manages all booking-related logic and communicates property status changes asynchronously.

Core Features
Microservices Architecture: Two distinct FastAPI services, fully containerized with Docker.

Event-Driven Communication: Apache Kafka is used to decouple services. When a booking is made, the booking-service produces a message to a Kafka topic. The backend service consumes from this topic to update the property's availability, ensuring high resilience.

Asynchronous Task Handling: The Kafka consumer in the backend service runs as a background asyncio task, managed by FastAPI's startup event.

JWT Authentication: Secure user registration and login using JWT access tokens and HTTPOnly refresh tokens.

Role-Based Access Control (RBAC): Admin-only endpoints for property management (Create, Delete).

Caching with Redis: The GET /properties endpoint is cached with Redis to reduce database load and improve response times.

Database Migrations: The backend service uses Alembic to manage database schema changes in a safe, version-controlled manner.

Conflict Handling: The booking-service includes logic to check for date conflicts, preventing double-bookings.

Tech Stack
Framework: FastAPI

Databases: PostgreSQL (x2), Redis

Message Broker: Apache Kafka

Containerization: Docker & Docker Compose

Data Validation: Pydantic

Database ORM: SQLAlchemy

Migrations: Alembic

Auth: passlib[bcrypt], python-jose[cryptography]

Async Kafka Client: aiokafka

System Architecture
The entire system runs within a Docker network defined in docker-compose.yml.

A user registers/logins via the Backend Service (port 8000) and gets a JWT.

The user fetches properties from GET /properties. This request hits the Redis cache first. If the data isn't in the cache, it queries the PostgreSQL FastBnB DB.

The user books a property by sending a request to the Booking Service (port 8001) with their JWT.

The Booking Service validates the token and the dates, then saves the booking to the separate PostgreSQL booking_db.

Immediately after, the Booking Service produces a message (e.g., {"property_id": 1, "status": "UNAVAILABLE"}) to the property_updates Kafka topic.

The Backend Service's background consumer, which is always listening, receives this message. It then updates the properties table in the FastBnB DB to mark the property as unavailable and clears the Redis cache.

This decoupled design ensures that the booking can be confirmed instantly, even if the backend service is temporarily down.

Getting Started
Prerequisites
Docker


API Documentation (Swagger UI)
You can interact with both services via their automatically generated Swagger documentation:

Backend (Users & Properties): http://localhost:8000/docs

Booking (Bookings): http://localhost:8001/docs

Future Improvements
Testing: Implement unit and integration tests using pytest and TestClient.

CI/CD: Build a GitHub Actions pipeline to automatically run tests, lint code, build images, and push to a Docker registry.

Resilience: Implement the Transactional Outbox Pattern for the booking-service to guarantee message delivery to Kafka, even if Kafka is down.

Deployment: Write Kubernetes manifest files for production deployment.

Monitoring: Add Prometheus and Grafana to the Docker Compose setup for service monitoring.
