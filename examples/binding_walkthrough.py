"""Exercise Chapter 8's grain/join example on the capstone SQLite fixture."""
from capstone import ContextDemo


def main():
    demo = ContextDemo()
    try:
        bad = demo.db.execute("""
            SELECT t.operator FROM deployments s JOIN deployments t
            ON s.auth_service=t.service_id
            WHERE s.service_id=? AND s.environment=?
        """, ("portal", "production")).fetchall()
        good = demo.db.execute("""
            SELECT t.operator FROM deployments s JOIN deployments t
            ON s.auth_service=t.service_id AND s.environment=t.environment
            WHERE s.service_id=? AND s.environment=?
        """, ("portal", "production")).fetchall()
        assert len(bad) == 2
        assert len(good) == 1
        assert good[0]["operator"] == "identity-operations"
        print("Incomplete join: 2 rows; complete scoped join: 1 row")
        print("Operator: identity-operations")
        print("Three source-fixture assertions passed; no remote source was used.")
    finally:
        demo.close()


if __name__ == "__main__":
    main()
