from os import environ

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from contextlib import contextmanager


engine = create_engine(
    "postgresql://{}:{}@{}:5432/{}".format(
        environ.get('DB_USER'),
        environ.get('DB_PASSWORD'),
        environ.get('DB_HOST'),
        environ.get('DB_NAME'),
    ),
    pool_pre_ping=True
)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def session_scope():
    session = Session()

    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()