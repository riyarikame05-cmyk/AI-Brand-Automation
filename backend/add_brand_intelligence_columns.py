from sqlalchemy import text

from app.database import engine


print("Updating BrandKit database table...")


sql = """
ALTER TABLE brand_kits
ADD COLUMN IF NOT EXISTS slogan TEXT;

ALTER TABLE brand_kits
ADD COLUMN IF NOT EXISTS personality TEXT;

ALTER TABLE brand_kits
ADD COLUMN IF NOT EXISTS tone TEXT;

ALTER TABLE brand_kits
ADD COLUMN IF NOT EXISTS target_audience TEXT;

ALTER TABLE brand_kits
ADD COLUMN IF NOT EXISTS marketing_message TEXT;

ALTER TABLE brand_kits
ADD COLUMN IF NOT EXISTS heading_font VARCHAR;

ALTER TABLE brand_kits
ADD COLUMN IF NOT EXISTS body_font VARCHAR;
"""


try:

    with engine.begin() as connection:

        connection.execute(
            text(sql)
        )


    print("")
    print("SUCCESS!")
    print(
        "Brand intelligence columns "
        "were added successfully."
    )


except Exception as error:

    print("")
    print("DATABASE UPDATE FAILED")
    print(repr(error))