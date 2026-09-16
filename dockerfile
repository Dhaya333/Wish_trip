# File path: wishtrip-goa-planner/Dockerfile
#
# Runs the Python app (ML training, FastAPI backend) inside a Linux
# container so Windows-host security policies (e.g. Smart App Control)
# never see or block any compiled package DLLs -- numpy/scipy/
# scikit-learn's native extensions run fine inside this container even
# when they're blocked on the Windows host itself.

FROM python:3.11-slim

WORKDIR /app

# System deps needed to build/run scientific Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]