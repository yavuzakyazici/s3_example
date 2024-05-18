from fastapi import FastAPI, Depends
from sqlalchemy import (
    Column,
    Integer,
    create_engine,
) 
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from fastapi_storages import S3Storage
from fastapi_storages.integrations.sqlalchemy import FileType
from sqladmin import Admin, ModelView
import boto3
from botocore.exceptions import ClientError
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi_storages.utils import secure_filename


"""
All of these params below should be in a .env file loaded with load_dotenv()

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
AWS_DEFAULT_ACL = os.getenv("AWS_DEFAULT_ACL")
AWS_S3_USE_SSL = os.getenv("AWS_S3_USE_SSL")
REGION_NAME = os.getenv("REGION_NAME")
ENDPOINT_URL_DEFAULT = os.getenv("ENDPOINT_URL_DEFAULT")
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
REGION_NAME = "MY_REGION_NAME"

MY_DB_NAME = "s3_example_db"
SQLALCHEMY_DATABASE_URL = 'sqlite:///' + MY_DB_NAME


# Create SqlAlchemy Engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
Base.metadata.create_all(bind=engine)


# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# create FastAPI
app = FastAPI()


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

"""
create your boto3 client
"""
s3 = boto3.client(
    service_name ="s3",
    endpoint_url = AWS_S3_ENDPOINT_URL,
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME, # Must be one of: wnam, enam, weur, eeur, apac, auto
)

def create_presigned_url(bucket_name, object_name):
    # Generate a presigned URL for the S3 object
    expiration=15
    try:
        response = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_name,
                },
            ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None
    return response

@app.get("/")
async def root():
    return {"message": "Welcome to S3 example"}

@app.get("/get_videos/")
def get_videos(db: Session = Depends(get_db)):
    videos = db.query(Video).all()
    for video in videos:
        """
        We are changing the VideoUrl since it gives us the full path pf the file inside the bucket
        This will work only if the bucket is public.
        Then you don't need to create a presigned url
        You can just return the videos
        
        videos = db.query(Video).all()
        return videos
        """
        obj_name = video.VideoUrl[str(video.VideoUrl).rfind("/")+1: len(str(video.VideoUrl))]
        # print(obj_name)
        video.VideoUrl = create_presigned_url(AWS_S3_BUCKET_NAME, obj_name)
    return videos
