from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
APP_VERSION = os.environ["APP_VERSION"]
SQLALCHEMY_DATABASE_URL = os.environ["SQLALCHEMY_DATABASE_URL"]

engine = (
    create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"ssl": {"ssl_ca": "DigiCertGlobalRootCA.crt.pem"}},
    )
    if APP_VERSION == "PRODUCTION"
    else create_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=True,
    )
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


async def test_db_connection():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
    finally:
        db.close()


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
