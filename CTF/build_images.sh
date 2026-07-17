#!/bin/bash
# Build all CTF Docker challenge images.
# Run from /root/www.cylsec.com/CTF/
# Usage: bash build_images.sh

set -e
INSTANCES_DIR="$(dirname "$0")/CTF_Instances"

echo "=== Building CTF Docker images ==="

find "$INSTANCES_DIR" -name "Dockerfile" | while read dockerfile; do
    dir=$(dirname "$dockerfile")
    # Derive image name from folder: CTF_Instances/<Type>/<name>/Dockerfile -> cylvern/<name>
    name=$(basename "$dir")
    image="cylvern/$name"
    echo ""
    echo ">>> Building $image from $dir"
    docker build -t "$image" "$dir" && echo "    OK: $image" || echo "    FAILED: $image"
done

echo ""
echo "=== Done. Built images ==="
docker images | grep cylvern || echo "(no cylvern images found)"
