from backend.db.neo4j import GraphDatabase

from backend.core.config import settings

_driver = None


def connect() -> None:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )


def close() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def get_driver():
    if _driver is None:
        connect()
    return _driver


def get_session():
    driver = get_driver()
    return driver.session()
