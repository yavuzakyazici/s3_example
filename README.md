Here is another FastAPI S3 compatible R2 exanple.
This time it shows SqlAdmin integration for images and videos.

```py
from fastapi import FastAPI
import os
from dotenv import load_dotenv

from sqlalchemy import (
    Column,
    Integer,
    create_engine,
) 
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi_storages import S3Storage
from fastapi_storages.integrations.sqlalchemy import FileType

from sqladmin import Admin, ModelView

"""
All of these params below should be in a .env file loaded with load_dotenv()

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
AWS_DEFAULT_ACL = os.getenv("AWS_DEFAULT_ACL")
AWS_S3_USE_SSL = os.getenv("AWS_S3_USE_SSL")
"""


"""
These are dummy place holder params
You should get real params from CloudFlare R2 ( or Amason AWS S3 ) after creating your bucket
and your API Key at CloudFlare Dashboard
This example obivously will NOT work before creating your bucket and getting API key
"""
AWS_ACCESS_KEY_ID = "MY_AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY = "MY_AWS_SECRET_ACCESS_KEY"
AWS_S3_BUCKET_NAME = "MY_AWS_S3_BUCKET_NAME"
AWS_S3_ENDPOINT_URL = "MY_AWS_S3_ENDPOINT_URL"
AWS_DEFAULT_ACL = "AWS_DEFAULT_ACL"
AWS_S3_USE_SSL = "AWS_S3_USE_SSL"

MY_DB_NAME = "s3_example_db"
SQLALCHEMY_DATABASE_URL = 'sqlite:///' + MY_DB_NAME


# Create SqlAlchemy Engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
Base.metadata.create_all(bind=engine)

# create FastAPI
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to S3 example"}

# create
admin_app = FastAPI()
admin = Admin(
    admin_app,
    engine,
    base_url="/",
)

app.mount("/admin", admin_app)

#storage for Image and Video models
class S3ExampleStorage(S3Storage):
    AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
    AWS_S3_BUCKET_NAME = AWS_S3_BUCKET_NAME
    AWS_S3_ENDPOINT_URL = AWS_S3_ENDPOINT_URL
    AWS_DEFAULT_ACL = AWS_DEFAULT_ACL
    AWS_S3_USE_SSL = AWS_S3_USE_SSL

storage = S3ExampleStorage()

#models
class Image(Base):
    __tablename__ = "images"

    Id = Column(Integer, primary_key=True, index=True)
    ImageUrl = Column(FileType(storage=storage))

class Video(Base):
    __tablename__ = "videos"

    Id = Column(Integer, primary_key=True, index=True)
    VideoUrl = Column(FileType(storage=storage))

# adminviews
class ImageAdmin(ModelView, model=Image):
    column_list = [
        Image.Id,
        Image.ImageUrl,
    ]

class VideoAdmin(ModelView, model=Video):
    column_list = [
        Video.Id,
        Video.VideoUrl,
    ]

admin.add_view(ImageAdmin)
admin.add_view(VideoAdmin)



```
