#!/bin/bash
# Fix permissions
rm -rf node_modules
rm -rf package-lock.json

# Install dependencies
npm install --force

# Build project
npm run build