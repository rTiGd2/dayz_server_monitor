#!/bin/bash

# Check repo
if [ ! -d ".git" ]; then
  echo "❌ No git repository found."
  exit 1
fi

# Ask for branch to checkout
read -p "Enter branch name to checkout: " BRANCH

git checkout $BRANCH
git pull origin $BRANCH

echo "✅ Checked out latest code for $BRANCH."
