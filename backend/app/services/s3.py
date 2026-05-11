import uuid
import shutil
from pathlib import Path
from io import BytesIO
from ..core.config import settings


def _local_dir() -> Path:
    p = Path(settings.upload_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / "photos").mkdir(exist_ok=True)
    (p / "thumbs").mkdir(exist_ok=True)
    return p


def generate_presigned_put(filename: str, mime_type: str, size: int) -> tuple[str, str]:
    if settings.storage_type == "local":
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        key = f"photos/{uuid.uuid4()}.{ext}"
        # For local storage the "upload URL" points to our own API
        url = f"{settings.public_url}/api/v1/photos/local-upload/{key}"
        return key, url
    else:
        import boto3
        from botocore.config import Config
        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4"),
        )
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        key = f"photos/{uuid.uuid4()}.{ext}"
        url = client.generate_presigned_url(
            "put_object",
            Params={"Bucket": settings.s3_bucket, "Key": key, "ContentType": mime_type},
            ExpiresIn=300,
        )
        return key, url


def public_url(key: str) -> str:
    if not key:
        return ""
    if settings.storage_type == "local":
        return f"{settings.public_url}/uploads/{key}"
    return f"{settings.s3_endpoint}/{settings.s3_bucket}/{key}"


def save_local(key: str, data: bytes) -> str:
    path = _local_dir() / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return key


def create_thumbnail(s3_key: str) -> str | None:
    try:
        from PIL import Image
        if settings.storage_type == "local":
            src = _local_dir() / s3_key
            if not src.exists():
                return None
            data = src.read_bytes()
        else:
            import boto3
            client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region,
            )
            data = client.get_object(Bucket=settings.s3_bucket, Key=s3_key)["Body"].read()

        img = Image.open(BytesIO(data))
        img.thumbnail((400, 400), Image.LANCZOS)
        thumb_key = s3_key.replace("photos/", "thumbs/", 1)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)

        if settings.storage_type == "local":
            dst = _local_dir() / thumb_key
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(buf.read())
        else:
            client.put_object(
                Bucket=settings.s3_bucket, Key=thumb_key,
                Body=buf, ContentType="image/jpeg",
            )
        return thumb_key
    except Exception:
        return None


def delete_object(key: str):
    try:
        if settings.storage_type == "local":
            p = _local_dir() / key
            if p.exists():
                p.unlink()
        else:
            import boto3
            boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
            ).delete_object(Bucket=settings.s3_bucket, Key=key)
    except Exception:
        pass
