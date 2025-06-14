#!/bin/bash

# Check repo
if [ ! -d ".git" ]; then
  echo "❌ No git repository found."
  exit 1
fi

# Ask for branch name
read -p "Enter branch name to use (or press ENTER for main): " BRANCH
if [ -z "$BRANCH" ]; then
  BRANCH="main"
fi

git checkout -B $BRANCH

# Pull latest changes
git pull origin $BRANCH

# Stage all modified files
git add .

# Ask for commit message
read -p "Enter your commit message: " MESSAGE

git commit -m "$MESSAGE"
git push origin $BRANCH

echo "✅ Code committed and pushed to $BRANCH successfully."
