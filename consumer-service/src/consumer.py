import json
import os
import threading
import time
from datetime import datetime

import pika
from fastapi import FastAPI
from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    MetaData,
    JSON,
    text,
)
from sqlalchemy.orm import sessionmaker

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
QUEUE_NAME = "user_activity_events"

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root_password")
MYSQL_DB = os.getenv("MYSQL_DB", "user_activity_db")

DATABASE_URL = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

engine = None
SessionLocal = None

metadata = MetaData()

user_activities = Table(
    "user_activities",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("event_type", String(50), nullable=False),
    Column("timestamp", DateTime, nullable=False),
    Column("metadata", JSON),
)


app = FastAPI(title="User Activity Consumer Service")


@app.get("/health")
def health_check():
    return {"status": "ok"}


def init_db():
    global engine, SessionLocal

    while True:
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            SessionLocal = sessionmaker(bind=engine)

            # Test DB connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            print("Connected to MySQL successfully")
            break

        except Exception as exc:
            print(f"MySQL not ready: {exc}. Retrying in 5 seconds...")
            time.sleep(5)


def process_message(body: bytes):
    data = json.loads(body)

    session = SessionLocal()
    try:
        session.execute(
            user_activities.insert().values(
                user_id=data["user_id"],
                event_type=data["event_type"],
                timestamp=datetime.fromisoformat(
                    data["timestamp"].replace("Z", "+00:00")
                ),
                metadata=data.get("metadata"),
            )
        )
        session.commit()
    finally:
        session.close()


def on_message(channel, method, properties, body):
    try:
        process_message(body)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        print(f"Error processing message: {exc}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_consumer():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=on_message,
            )

            print("Consumer started. Waiting for messages...")
            channel.start_consuming()

        except Exception as exc:
            print(f"Consumer error: {exc}. Retrying in 5 seconds...")
            time.sleep(5)


@app.on_event("startup")
def startup_event():
    init_db()
    thread = threading.Thread(target=start_consumer, daemon=True)
    thread.start()
