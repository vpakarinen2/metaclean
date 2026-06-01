# MetaClean 🧹

View and remove metadata from images and videos.

## Requirements

- Python 3.11+
- `ffmpeg` installed and available on `PATH`
- `exiftool` dir in the project root (https://exiftool.org)

## Install FFmpeg (Windows)

```powershell
winget install Gyan.FFmpeg
ffmpeg -version
```

## Setup

```powershell
py -m ensurepip --upgrade
py -m pip install -e .
```

Add `metaclean` in the current session:

```powershell
$env:Path = $env:Path + ";" + (Resolve-Path .\Scripts)
```

## Usage

```powershell
metaclean view "image.jpg"
metaclean clean "image.jpg"
```

Put all the images you want to convert in the ``--input`` directory.

## Troubleshooting
If you get an error 'ffmpeg not found', use `where.exe` to find it on `PATH`:

```powershell
where.exe ffmpeg
```

## Support
If you find this project valuable, consider supporting my work:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/vpakarinen)
[![Ko-Fi](https://img.shields.io/badge/Ko--fi-F16061?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/vpakarinen)

## Author

Ville Pakarinen (@vpakarinen2)
