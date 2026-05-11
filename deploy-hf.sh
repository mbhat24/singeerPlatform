#!/bin/bash
# Deploy Singer Platform to Hugging Face Spaces with free GPU
# Run this script from the singer-platform repo root

set -e

HF_USERNAME="mbhat24"
SPACE_NAME="singer-platform-api"

echo "=== Step 1: Create Space on Hugging Face ==="
echo "Open this URL in your browser:"
echo "https://huggingface.co/new-space?name=${SPACE_NAME}&sdk=docker&hardware=t4-small"
echo ""
echo "After creating the Space, press Enter to continue..."
read -r

echo ""
echo "=== Step 2: Clone the Space repo ==="
HF_SPACE_REPO="https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"
TMP_DIR="/tmp/hf-space-${SPACE_NAME}"

rm -rf "$TMP_DIR"
git clone "$HF_SPACE_REPO" "$TMP_DIR"

echo ""
echo "=== Step 3: Copy HF Space files ==="
cp -r huggingface-space/* "$TMP_DIR/"
cp -r huggingface-space/.[!.]* "$TMP_DIR/" 2>/dev/null || true

echo ""
echo "=== Step 4: Commit and push ==="
cd "$TMP_DIR"
git add -A
git commit -m "Deploy Singer Platform API with GPU voice cloning"
git push

echo ""
echo "=== Done! ==="
echo "Your API is live at: https://${HF_USERNAME}-${SPACE_NAME}.hf.space"
echo "Health check: https://${HF_USERNAME}-${SPACE_NAME}.hf.space/api/health"
echo "API docs: https://${HF_USERNAME}-${SPACE_NAME}.hf.space/docs"
echo ""
echo "Update your frontend .env:"
echo "NEXT_PUBLIC_API_URL=https://${HF_USERNAME}-${SPACE_NAME}.hf.space"
