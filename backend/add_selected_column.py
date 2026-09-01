from sqlalchemy import text

from app.database import engine


print("Updating database...")

try:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE assets
                ADD COLUMN IF NOT EXISTS
                is_selected BOOLEAN
                NOT NULL
                DEFAULT FALSE;
                """
            )
        )

    print("SUCCESS!")
    print(
        "Column 'is_selected' now exists "
        "in the assets table."
    )

except Exception as error:
    print("DATABASE UPDATE FAILED!")
    print(repr(error))