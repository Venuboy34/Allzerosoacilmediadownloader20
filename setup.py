from setuptools import setup

setup(
    name="social-media-downloader-api",
    version="1.0.0",
    packages=["api"],
    include_package_data=True,
    install_requires=[
        "fastapi>=0.103.1",
        "uvicorn>=0.23.2",
        "httpx>=0.24.1",
        "pydantic>=2.3.0",
        "python-dotenv>=1.0.0",
        "slowapi>=0.1.8",
        "yt-dlp>=2023.7.6",
        "instaloader>=4.10.0",
        "mangum>=0.17.0",
    ],
    python_requires=">=3.9",
)
