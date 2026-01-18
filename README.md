#  Event-Driven User Activity Tracker

An **event-driven microservices system** that tracks user activity events using **FastAPI, RabbitMQ, MySQL, Docker, and Nginx**.
The system demonstrates **asynchronous processing**, **loose coupling**, and **reliable message handling**.

---

##  Project Overview

This project captures user activity events (such as login, signup, page views) through a REST API, publishes them to a message queue, processes them asynchronously, and stores them in a database.

### Why Event-Driven?

* Producer is **not blocked** by database operations
* System is **scalable and fault-tolerant**
* Consumer failures do **not affect API availability**
* Easy to add more consumers later

---

## Architecture

```
Frontend (Nginx :3000)
        |
        v
Producer Service (FastAPI :8000)
        |
        v
RabbitMQ (Durable Queue)
        |
        v
Consumer Service (FastAPI)
        |
        v
MySQL Database
```

---

##  Tech Stack

| Layer            | Technology                   |
| ---------------- | ---------------------------- |
| Frontend         | HTML, CSS, JavaScript, Nginx |
| API              | FastAPI (Python)             |
| Messaging        | RabbitMQ                     |
| Database         | MySQL 8                      |
| ORM              | SQLAlchemy                   |
| Containerization | Docker, Docker Compose       |

---

##  Project Structure

```
event-driven-user-activity-tracker/
│
├── producer-service/
│   ├── src/main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── consumer-service/
│   ├── src/consumer.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   └── Dockerfile
│
├── db/
│   └── init.sql
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

##  API Specification (Producer)

### Endpoint

```
POST /api/v1/events/track
```

### Request Body

```json
{
  "user_id": 101,
  "event_type": "login",
  "timestamp": "2025-01-03T08:30:00Z",
  "metadata": {
    "source": "web"
  }
}
```

### Response

* `202 Accepted` → Event queued successfully
* `500` → Internal error

---

##  Design Decisions

### Producer Service

* Publishes events to RabbitMQ
* No direct DB access
* Uses durable queues
* CORS enabled for frontend access

### Consumer Service

* Consumes messages asynchronously
* Acknowledges messages **only after DB commit**
* Retries on failure
* Handles DB startup race conditions

### RabbitMQ

* Durable queue (`user_activity_events`)
* Persistent messages
* Prefetch count = 1 for safe processing

---

## Database Schema

```sql
CREATE TABLE user_activities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  event_type VARCHAR(50) NOT NULL,
  timestamp DATETIME NOT NULL,
  metadata JSON
);
```

---

## How to Run the Project

### Prerequisites

* Docker
* Docker Compose

### Start All Services

```bash
docker-compose up -d
```

---

## Access URLs

| Service         | URL                                                          |
| --------------- | ------------------------------------------------------------ |
| Frontend        | [http://localhost:3000](http://localhost:3000)               |
| Producer API    | [http://localhost:8000](http://localhost:8000)               |
| Producer Health | [http://localhost:8000/health](http://localhost:8000/health) |
| RabbitMQ UI     | [http://localhost:15672](http://localhost:15672)             |
| MySQL           | localhost:3306                                               |

---

## Testing the System

### 1. Using Frontend

1. Open `http://localhost:3000`
2. Fill form and click **Send Event**
3. See success message

### 2. Verify Database

```bash
docker exec -it event-driven-user-activity-tracker-mysql-1 mysql -u root -p
```

```sql
USE user_activity_db;
SELECT * FROM user_activities;
```

---

## Error Handling & Reliability

* Messages acknowledged **only after DB success**
* Failed DB writes → message requeued
* Consumer auto-retries on startup failures
* Health endpoints for monitoring

---
