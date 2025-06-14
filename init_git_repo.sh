#!/bin/bash

echo "🌐 Initializing Git project for RC9..."

# Ask for GitHub repo URL
read -p "Enter Git remote repository URL (SSH or HTTPS): " GIT_REMOTE

# Ask for user details
read -p "Enter your Git username: " GIT_USER
git config --global user.name "$GIT_USER"

read -p "Enter your Git email: " GIT_EMAIL
git config --global user.email "$GIT_EMAIL"

# Setup credential caching
git config --global credential.helper store

# Initialize repo if not already done
if [ ! -d ".git" ]; then
  git init
fi

git remote add origin "$GIT_REMOTE"

echo "✅ Git initialized successfully."
echo "✅ Credentials will be cached for future use."
