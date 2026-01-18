import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

import pika
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
QUEUE_NAME = "user_activity_events"


app = FastAPI(title="User Activity Producer Service")


class UserActivityEvent(BaseModel):
    user_id: int = Field(..., example=123)
    event_type: str = Field(..., example="login")
    timestamp: datetime = Field(..., example="2025-01-01T10:00:00Z")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@app.get("/health")
def health_check():
    return {"status": "ok"}


def publish_event(event: dict):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
            )
        )
        channel = connection.channel()

        # Ensure queue exists
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=json.dumps(event),
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            ),
        )

        connection.close()

    except Exception as exc:
        raise RuntimeError(f"Failed to publish event: {exc}")


@app.post("/api/v1/events/track", status_code=202)
def track_event(event: UserActivityEvent):
    try:
        publish_event(json.loads(event.json()))
        return {"message": "Event accepted for processing"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
