#!/bin/bash

# Script kiểm tra môi trường cho RTDB Labs

echo "======================================================================"
echo "KIỂM TRA MÔI TRƯỜNG - RTDB LABS"
echo "======================================================================"

# Check Python
echo ""
echo "1. Kiểm tra Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ $PYTHON_VERSION"
else
    echo "✗ Python 3 chưa được cài đặt!"
    echo "  Cài đặt: https://www.python.org/downloads/"
fi

# Check pip
echo ""
echo "2. Kiểm tra pip..."
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version)
    echo "✓ $PIP_VERSION"
else
    echo "✗ pip chưa được cài đặt!"
fi

# Check Docker
echo ""
echo "3. Kiểm tra Docker (cần cho Lab 1)..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "✓ $DOCKER_VERSION"
    
    # Check if Docker is running
    if docker ps &> /dev/null; then
        echo "✓ Docker đang chạy"
    else
        echo "⚠ Docker đã cài nhưng chưa chạy!"
        echo "  Khởi động Docker Desktop hoặc Docker daemon"
    fi
else
    echo "✗ Docker chưa được cài đặt (cần cho Lab 1)!"
    echo "  Tải tại: https://www.docker.com/products/docker-desktop"
fi

# Check Docker Compose
echo ""
echo "4. Kiểm tra Docker Compose (cần cho Lab 1)..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo "✓ $COMPOSE_VERSION"
else
    echo "⚠ docker-compose chưa được cài đặt"
    echo "  Thường đi kèm với Docker Desktop"
fi

# Check installed Python packages
echo ""
echo "5. Kiểm tra Python packages..."

packages=(
    "matplotlib:matplotlib"
    "numpy:numpy"
    "psycopg2:psycopg2-binary"
    "redis:redis"
    "supabase:supabase"
    "dotenv:python-dotenv"
)

missing_packages=()

for package_info in "${packages[@]}"; do
    IFS=':' read -r import_name install_name <<< "$package_info"
    
    if python3 -c "import $import_name" 2>/dev/null; then
        echo "  ✓ $install_name"
    else
        echo "  ✗ $install_name"
        missing_packages+=("$install_name")
    fi
done

# Summary
echo ""
echo "======================================================================"
echo "TÓM TẮT"
echo "======================================================================"

if [ ${#missing_packages[@]} -eq 0 ]; then
    echo "✓ Tất cả dependencies đã được cài đặt!"
else
    echo "⚠ Cần cài đặt thêm:"
    echo ""
    echo "Chạy lệnh sau để cài đặt:"
    echo "pip3 install ${missing_packages[*]}"
    echo ""
    echo "Hoặc cài đặt từng lab:"
    echo "  cd Lab1 && pip3 install -r requirements.txt"
    echo "  cd Lab2 && pip3 install -r requirements.txt"
    echo "  cd Lab3 && pip3 install -r requirements.txt"
    echo "  cd Lab4 && pip3 install -r requirements.txt"
fi

echo ""
echo "======================================================================"
echo "HƯỚNG DẪN TIẾP THEO"
echo "======================================================================"
echo ""
echo "Đọc file QUICKSTART.md để bắt đầu thực hành:"
echo "  cat QUICKSTART.md"
echo ""
echo "Hoặc bắt đầu với Lab 1:"
echo "  cd Lab1"
echo "  cat README.md"
echo ""
