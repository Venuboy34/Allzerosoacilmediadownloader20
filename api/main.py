from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import re
import httpx
import os
from typing import Optional, Dict, Any
import asyncio
from urllib.parse import urlparse
import logging
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Social Media Downloader API",
    description="API for downloading media from Instagram, TikTok, Facebook, and YouTube",
    version="1.0.0",
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the domains allowed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input model
class DownloadRequest(BaseModel):
    url: HttpUrl
    format: Optional[str] = "mp4"  # Default to mp4, can be mp3 for audio

# Platform detector patterns
PLATFORM_PATTERNS = {
    "instagram": re.compile(r'(instagram\.com|instagr\.am)'),
    "tiktok": re.compile(r'(tiktok\.com|vm\.tiktok\.com)'),
    "facebook": re.compile(r'(facebook\.com|fb\.com|fb\.watch)'),
    "youtube": re.compile(r'(youtube\.com|youtu\.be)'),
}

# Platform handlers
async def instagram_handler(url: str, format: str) -> Dict[str, Any]:
    """Handle Instagram downloads: reels, posts, and stories"""
    # Implementation would use a library like instaloader or custom scraping
    # This is a simplified placeholder
    logger.info(f"Processing Instagram URL: {url}")
    
    # Determine content type (reel, post, story) from URL
    content_type = "reel" if "reel" in url else "post" if "p/" in url else "story"
    
    # In a real implementation, you would:
    # 1. Fetch the media details
    # 2. Extract the download URL, thumbnail, etc.
    # 3. Process according to requested format
    
    # Placeholder response
    return {
        "status": "success",
        "platform": "Instagram",
        "media_type": "video" if content_type in ["reel", "story"] else "image",
        "download_url": f"https://api.example.com/downloads/instagram/{content_type}_processed.{format}",
        "thumbnail": "https://api.example.com/thumbnails/instagram_thumbnail.jpg",
        "title": f"Instagram {content_type.capitalize()}",
        "duration": "15s" if content_type in ["reel", "story"] else None
    }

async def tiktok_handler(url: str, format: str) -> Dict[str, Any]:
    """Handle TikTok downloads: videos, photos, and audio"""
    logger.info(f"Processing TikTok URL: {url}")
    
    # In a real implementation, you would use a library like TikTokAPI
    # or custom scraping to extract the content
    
    # Placeholder response
    return {
        "status": "success",
        "platform": "TikTok",
        "media_type": "video",
        "download_url": f"https://api.example.com/downloads/tiktok/video_nowatermark.{format}",
        "thumbnail": "https://api.example.com/thumbnails/tiktok_thumbnail.jpg",
        "title": "TikTok Video",
        "duration": "30s",
        "audio_url": f"https://api.example.com/downloads/tiktok/audio.mp3" if format == "mp3" else None
    }

async def facebook_handler(url: str, format: str) -> Dict[str, Any]:
    """Handle Facebook downloads: reels, posts, and stories"""
    logger.info(f"Processing Facebook URL: {url}")
    
    # Determine content type from URL
    content_type = "reel" if "reel" in url else "story" if "story" in url else "post"
    
    # Placeholder response
    return {
        "status": "success",
        "platform": "Facebook",
        "media_type": "video" if content_type in ["reel", "story"] else "image",
        "download_url": f"https://api.example.com/downloads/facebook/{content_type}.{format}",
        "thumbnail": "https://api.example.com/thumbnails/facebook_thumbnail.jpg",
        "title": f"Facebook {content_type.capitalize()}",
        "duration": "60s" if content_type in ["reel", "story"] else None
    }

async def youtube_handler(url: str, format: str) -> Dict[str, Any]:
    """Handle YouTube downloads: Shorts, videos, and posts"""
    logger.info(f"Processing YouTube URL: {url}")
    
    # Determine content type
    content_type = "short" if "shorts" in url else "video"
    
    # In a real implementation, you would use pytube, yt-dlp, or similar
    # libraries to extract the content
    
    # Placeholder response
    return {
        "status": "success",
        "platform": "YouTube",
        "media_type": "video",
        "download_url": f"https://api.example.com/downloads/youtube/{content_type}.{format}",
        "thumbnail": "https://api.example.com/thumbnails/youtube_thumbnail.jpg",
        "title": f"YouTube {content_type.capitalize()}",
        "duration": "30s" if content_type == "short" else "5m",
        "available_formats": ["144p", "240p", "360p", "480p", "720p", "1080p"]
    }

# Platform handler mapping
PLATFORM_HANDLERS = {
    "instagram": instagram_handler,
    "tiktok": tiktok_handler,
    "facebook": facebook_handler,
    "youtube": youtube_handler,
}

async def detect_platform(url: str) -> str:
    """Detect the platform from a given URL"""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    for platform, pattern in PLATFORM_PATTERNS.items():
        if pattern.search(domain):
            return platform
    
    raise ValueError(f"Unsupported platform for URL: {url}")

@app.post("/api/download")
@limiter.limit("60/minute")
async def download_media(request: Request, download_req: DownloadRequest):
    """
    Process a URL to download media from supported platforms
    """
    try:
        url = str(download_req.url)
        format = download_req.format.lower()
        
        # Validate format
        if format not in ["mp4", "mp3"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid format. Supported formats: mp4, mp3"
            )
        
        # Detect platform
        try:
            platform = await detect_platform(url)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        
        # Get appropriate handler
        handler = PLATFORM_HANDLERS.get(platform)
        if not handler:
            raise HTTPException(
                status_code=501,
                detail=f"Handler for platform '{platform}' not implemented"
            )
        
        # Process the URL
        result = await handler(url, format)
        return result
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# For Vercel serverless function
from mangum import Mangum
handler = Mangum(app)
