from db.migrations.add_shared_flags import add_flags
from db.migrations.add_new_features import add_features


def run_all_migrations() -> None:
    """
    Executes all database schema migration steps in the correct order.

    Returns:
        None
    """
    add_flags()
    add_features()


if __name__ == "__main__":
    run_all_migrations()
