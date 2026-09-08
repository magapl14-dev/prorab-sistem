import os
import uuid
import shutil
from collections.abc import AsyncIterable
from pathlib import Path
from io import BytesIO
from ..core.config import settings

_LOCAL_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/heic": "heic",
    "image/heif": "heif",
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mp4": "m4a",
    "audio/mpeg": "mp3",
    "audio/aac": "aac",
    "audio/wav": "wav",
    "audio/x-m4a": "m4a",
}


def _local_dir() -> Path:
    p = Path(settings.upload_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / "photos").mkdir(exist_ok=True)
    (p / "thumbs").mkdir(exist_ok=True)
    return p


def generate_presigned_put(filename: str, mime_type: str, size: int) -> tuple[str, str]:
    if settings.storage_type == "local":
        base_mime = mime_type.split(";", 1)[0].strip().lower()
        try:
            ext = _LOCAL_EXTENSIONS[base_mime]
        except KeyError as exc:
            raise ValueError("unsupported MIME type") from exc
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


def _open_local_root() -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    root = Path(settings.upload_dir)
    if root.is_absolute():
        fd = os.open("/", flags)
        parts = root.parts[1:]
    else:
        fd = os.open(".", flags)
        parts = root.parts

    try:
        for part in parts:
            if part in ("", "."):
                continue
            try:
                os.mkdir(part, dir_fd=fd)
            except FileExistsError:
                pass
            next_fd = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


async def save_local_stream(key: str, chunks: AsyncIterable[bytes], *, expected_size: int, max_size: int) -> str:
    key_parts = key.split("/") if isinstance(key, str) else []
    if (
        len(key_parts) != 2
        or key_parts[0] != "photos"
        or key_parts[1] in ("", ".", "..")
        or "\\" in key
        or "\x00" in key
    ):
        raise ValueError("invalid key")
    if (
        not isinstance(expected_size, int)
        or isinstance(expected_size, bool)
        or not isinstance(max_size, int)
        or isinstance(max_size, bool)
        or expected_size <= 0
        or max_size <= 0
        or expected_size > max_size
    ):
        raise ValueError("invalid size")

    root_fd = _open_local_root()
    photos_fd: int | None = None
    temp_fd: int | None = None
    temp_name: str | None = None
    try:
        try:
            os.mkdir("photos", dir_fd=root_fd)
        except FileExistsError:
            pass
        photos_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        photos_fd = os.open("photos", photos_flags, dir_fd=root_fd)

        temp_flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
        )
        while True:
            candidate = f".upload-{uuid.uuid4().hex}.tmp"
            try:
                temp_fd = os.open(candidate, temp_flags, 0o600, dir_fd=photos_fd)
                temp_name = candidate
                break
            except FileExistsError:
                continue

        total = 0
        async for chunk in chunks:
            if not isinstance(chunk, bytes):
                raise TypeError("upload chunks must be bytes")
            next_total = total + len(chunk)
            if next_total > expected_size or next_total > max_size:
                raise ValueError("upload size exceeded")
            view = memoryview(chunk)
            while view:
                written = os.write(temp_fd, view)
                if written == 0:
                    raise OSError("failed to write upload")
                view = view[written:]
            total = next_total

        if total != expected_size:
            raise ValueError("upload size mismatch")

        os.fsync(temp_fd)
        os.close(temp_fd)
        temp_fd = None
        os.link(
            temp_name,
            key_parts[1],
            src_dir_fd=photos_fd,
            dst_dir_fd=photos_fd,
            follow_symlinks=False,
        )
        os.unlink(temp_name, dir_fd=photos_fd)
        temp_name = None
        return key
    finally:
        if temp_fd is not None:
            os.close(temp_fd)
        if temp_name is not None and photos_fd is not None:
            try:
                os.unlink(temp_name, dir_fd=photos_fd)
            except FileNotFoundError:
                pass
        if photos_fd is not None:
            os.close(photos_fd)
        os.close(root_fd)


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
