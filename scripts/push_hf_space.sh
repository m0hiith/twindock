#!/usr/bin/env bash
# Push the current commit to a Hugging Face Space (Docker SDK) as a single fresh commit.
#
#   HF_SPACE=<user>/<space> ./scripts/push_hf_space.sh
#
# Hugging Face stores binary files (the logo PNG) with Git LFS/Xet and rejects them otherwise, and the project's
# history has the PNG as a plain blob. So this exports HEAD (git archive: only committed files, never .env or
# secrets), tracks images with LFS, swaps in the Space's README (deploy/huggingface/README.md, with the front matter
# Spaces need: sdk: docker, app_port: 7860) and force-pushes that one commit to the Space's main branch.
# Git asks for your Hugging Face username and an access token with write rights as the password.
set -euo pipefail
: "${HF_SPACE:?set HF_SPACE=<user>/<space>, e.g. HF_SPACE=mohith/twindock}"
command -v git-lfs >/dev/null || { echo "git-lfs is needed: brew install git-lfs (or apt install git-lfs)"; exit 1; }
root="$(git rev-parse --show-toplevel)"
rev="$(git -C "$root" rev-parse --short HEAD)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
git -C "$root" archive HEAD | tar -x -C "$tmp"
cp "$root/deploy/huggingface/README.md" "$tmp/README.md"
cd "$tmp"
git init -q -b main
git lfs install --local >/dev/null
git lfs track "*.png" "*.jpg" "*.jpeg" "*.pdf" "*.glb" >/dev/null
git add .gitattributes
git add -A
git -c user.name="TwinDock deploy" -c user.email="deploy@twindock.invalid" commit -q -m "TwinDock ${rev} for Hugging Face Spaces"
git remote add space "${HF_REMOTE:-https://huggingface.co/spaces/${HF_SPACE}}"  # HF_REMOTE: only for testing the script
git push --force space main
echo "Pushed ${rev} to https://huggingface.co/spaces/${HF_SPACE} (the Space rebuilds the image now)."
