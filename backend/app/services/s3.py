import uuid
from io import BytesIO
import boto3
from botocore.config import Config
from PIL import Image
from ..core.config import settings


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
    )


def generate_presigned_put(filename: str, mime_type: str, size: int) -> tuple[str, str]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    key = f"photos/{uuid.uuid4()}.{ext}"
    url = _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": key, "ContentType": mime_type},
        ExpiresIn=300,
    )
    return key, url


def public_url(key: str) -> str:
    return f"{settings.s3_public_url}/{settings.s3_bucket}/{key}"


def create_thumbnail(s3_key: str) -> str | None:
    try:
        client = _client()
        data = client.get_object(Bucket=settings.s3_bucket, Key=s3_key)["Body"].read()
        img = Image.open(BytesIO(data))
        img.thumbnail((400, 400), Image.LANCZOS)
        thumb_key = s3_key.replace("photos/", "thumbs/", 1)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        client.put_object(
            Bucket=settings.s3_bucket,
            Key=thumb_key,
            Body=buf,
            ContentType="image/jpeg",
        )
        return thumb_key
    except Exception:
        return None


def delete_object(key: str):
    try:
        _client().delete_object(Bucket=settings.s3_bucket, Key=key)
    except Exception:
        pass
