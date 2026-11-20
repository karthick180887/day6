# Day 6 Docker + JupyterLab Setup Guide

This guide gets every participant running the exact same Python 3.11 + JupyterLab environment in under 3 minutes — with zero `"it works on my laptop"` dependency conflicts.

---

## 1. Prerequisites

| Operating System | Requirement | Notes |
| --- | --- | --- |
| **Windows 10 / 11** | [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) | Enable **WSL 2 backend** during installation. Restart once if prompted. |
| **macOS (Intel & Apple Silicon M1–M4)** | [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) | The `python:3.11-slim` base image supports both `amd64` and `arm64` natively. |
| **Linux (Ubuntu/Debian/Fedora)** | Docker Engine + Docker Compose v2 plugin | Verify with `docker --version` and `docker compose version`. Add your user to the `docker` group (`sudo usermod -aG docker $USER`) to avoid `sudo`. |

Verify Docker is running before proceeding:

```bash
docker --version
docker compose version
```

---

## 2. Quick Start (1-Command Launch)

Run the commands below from the root of the cloned repository (`day6/`).

### macOS & Linux

```bash
cd docker-jupyterlab
chmod +x start.sh
./start.sh
```

### Windows (PowerShell or Command Prompt)

Double-click `start.bat` inside `docker-jupyterlab\`, **or** run in PowerShell:

```powershell
cd docker-jupyterlab
.\start.bat
```

### Manual Docker Compose (Any OS)

```bash
cd docker-jupyterlab
cp .env.example .env          # Windows: copy .env.example .env
docker compose up -d --build
```

Then open your browser to:

```text
http://localhost:8888/lab?token=day6-training
```

Open **[`00_environment_check.ipynb`](../notebooks/00_environment_check.ipynb)** and click **Run -> Run All Cells**. All checks should print `PASS`.

---

## 3. How Volume Mounting Works (Your Work Is Safe!)

Look at the volume mount in [`docker-compose.yml`](docker-compose.yml):

```yaml
volumes:
  - ../notebooks:/workspace/notebooks
```

- Every notebook inside [`notebooks/`](../notebooks/) appears directly inside JupyterLab's left sidebar.
- Any code you write, models you save in `artifacts/`, or experiment logs you generate are saved **directly onto your host laptop** inside `notebooks/`.
- Stopping the container (`docker compose down`) **does NOT delete** your notebooks or saved artifacts.

---

## 4. Stopping, Restarting, and Checking Logs

Run these commands from inside `docker-jupyterlab/`:

| Action | Command |
| --- | --- |
| Check container status | `docker compose ps` |
| Stream JupyterLab logs | `docker compose logs -f` |
| Stop JupyterLab (keeps your work) | `docker compose down` |
| Restart JupyterLab without rebuilding | `docker compose up -d` |
| Rebuild after changing `requirements.txt` | `docker compose up -d --build` |
| Open a shell inside the container | `docker compose exec jupyterlab bash` |

---

## 5. Classroom Wi-Fi & Pre-Build Tips (For Trainers)

If 30+ freshers build Docker images simultaneously over corporate or classroom Wi-Fi, downloads can throttle. Use one of these two strategies:

### Option A: Pre-Build Day Before (Recommended)
Ask participants to run `docker compose build` the evening before Day 6 while on home/office broadband. It takes ~60–90 seconds and downloads ~250 MB total.

### Option B: Offline USB / LAN Image Transfer (Zero Internet Needed!)
1. On the trainer laptop, build and export the image once:
   ```bash
   cd docker-jupyterlab
   docker compose build
   docker save -o day6-jupyterlab-image.tar day6-ml-engineering-jupyterlab:latest
   ```
   *(Note: build separate `.tar` archives if your classroom mixes Intel/AMD Windows laptops and Apple Silicon Macs, using `docker buildx build --platform linux/amd64` and `linux/arm64`.)*
2. Share the `.tar` file over USB or local network share.
3. On each participant's laptop:
   ```bash
   docker load -i day6-jupyterlab-image.tar
   docker compose up -d --no-build
   ```

### Option C: Local Python Fallback (If a Laptop Cannot Install Docker)
If a fresher has a locked-down corporate laptop without Docker admin rights, they can run the exact same environment locally:

```bash
cd docker-jupyterlab
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ../notebooks
jupyter lab
```

---

## 6. Troubleshooting Guide

### Problem 1: `Bind for 0.0.0.0:8888 failed: port is already allocated`
Another Jupyter server or local app is already using port `8888`.
- **Fix**: Open `docker-jupyterlab/.env` and change `JUPYTER_PORT=8888` to `JUPYTER_PORT=8889`, then run `docker compose up -d`. Open `http://localhost:8889/lab?token=day6-training`.

### Problem 2: Permission Denied Writing Files on Linux
The container runs as user `jovyan` (UID `1000`, GID `1000`). If your Linux host user has a different UID (check with `id -u`), container writes to `../notebooks` may fail.
- **Fix**: Rebuild with your host UID/GID:
  ```bash
  docker compose build --build-arg USER_UID=$(id -u) --build-arg USER_GID=$(id -g)
  docker compose up -d
  ```

### Problem 3: Windows CRLF Line Endings in `start.sh`
Not needed on Windows (use `start.bat`), and inside WSL2 if you see `\r: command not found`, run:
```bash
sed -i 's/\r$//' start.sh
```

### Problem 4: JupyterLab Asks for a Password or Token
Use the full URL with the token query parameter: `http://localhost:8888/lab?token=day6-training`, or paste `day6-training` into the token box.

### Problem 5: Accidentally Broke a Starter Notebook
Because the `notebooks/` folder is mounted directly from your laptop, download/copy a fresh copy of the starter `.ipynb` file from the shared training repository or ask the trainer for the clean copy.

### Problem 6: Corporate Proxy / SSL Certificate Errors During `pip install`
If behind a corporate proxy, pass proxy variables during build:
```bash
docker compose build --build-arg HTTP_PROXY=$HTTP_PROXY --build-arg HTTPS_PROXY=$HTTPS_PROXY
```
