from types import SimpleNamespace

from app.operations import predeploy


class FakeConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def exec_driver_sql(
        self,
        statement: str,
        _parameters: tuple[int] | None = None,
    ) -> None:
        self.statements.append(statement)


class FakeEngine:
    dialect = SimpleNamespace(name="postgresql")

    def __init__(self) -> None:
        self.connection = FakeConnection()

    def connect(self) -> FakeConnection:
        return self.connection


def test_postgres_migrations_reuse_advisory_locked_connection(
    monkeypatch,
) -> None:
    engine = FakeEngine()
    captured = {}

    def upgrade(config, revision: str) -> None:
        captured["connection"] = config.attributes.get("connection")
        captured["revision"] = revision

    monkeypatch.setattr(predeploy, "engine", engine)
    monkeypatch.setattr(predeploy.command, "upgrade", upgrade)

    predeploy.run_migrations()

    assert captured == {
        "connection": engine.connection,
        "revision": "head",
    }
    assert engine.connection.statements == [
        "SELECT pg_advisory_lock(%s)",
        "SELECT pg_advisory_unlock(%s)",
    ]
