import os
import uuid
import aiofiles
from fastapi import UploadFile, Request, HTTPException
from app.config import settings
from PIL import Image
from io import BytesIO
import asyncio

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
DEFAULT_MAX_FILE_SIZE_MB = 10  # 10 MB


def compress_image_sync(content: bytes, size=(800, 800), quality=50) -> bytes:
    """Compress image (runs in executor to avoid blocking event loop)."""
    img = Image.open(BytesIO(content))
    img = img.convert("RGB")
    img.thumbnail(size)
    img_io = BytesIO()
    img.save(img_io, format="WEBP", quality=quality)
    return img_io.getvalue()


async def save_file(
    request: Request,
    file: UploadFile,
    folder: str,
    max_size: int = DEFAULT_MAX_FILE_SIZE_MB,
    allowed_extensions=ALLOWED_EXTENSIONS,
    compress: bool = True,
    quality: int = 50,
    size=(800, 800),
) -> str:
    # Check extension
    ext = file.filename.split(".")[-1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Create folder
    folder_path = os.path.join(settings.MEDIA_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)

    # Read file in chunks
    content = b""
    chunk_size = 1024 * 1024  # 1 MB
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content += chunk
        if len(content) > max_size * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")

    # Compress image if requested
    if compress and ext in {"jpg", "jpeg", "png", "gif"}:
        loop = asyncio.get_running_loop()
        try:
            content = await loop.run_in_executor(None, compress_image_sync, content, size, quality)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        # Save as .webp
        filename = f"{uuid.uuid4().hex}.webp"
    else:
        filename = f"{uuid.uuid4().hex}.{ext}"

    file_path = os.path.join(folder_path, filename)

    # Save file async
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Return public URL
    return str(request.base_url) + f"media/{folder}/{filename}"





# import boto3

# s3 = boto3.client(
#     "s3",
#     aws_access_key_id="YOUR_KEY",
#     aws_secret_access_key="YOUR_SECRET",
#     region_name="YOUR_REGION"
# )

# async def upload_to_s3(file_bytes: bytes, bucket: str, key: str):
#     loop = asyncio.get_running_loop()
#     await loop.run_in_executor(
#         None,
#         lambda: s3.put_object(Bucket=bucket, Key=key, Body=file_bytes)
#     )
#     return f"https://{bucket}.s3.amazonaws.com/{key}"