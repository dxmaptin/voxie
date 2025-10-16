#!/bin/bash

# Quick Commit and Deploy Script for Exercise 4
# This will commit all deployment files and prepare for Railway deployment

echo "🚀 Exercise 4: Committing Deployment Files"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "backend_server.py" ]; then
    echo "❌ Error: Not in the voxie directory"
    echo "Please run: cd '/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie'"
    exit 1
fi

echo "✅ In correct directory: $(pwd)"
echo ""

# Show status
echo "📋 Current Git Status:"
git status --short
echo ""

# Ask for confirmation
echo "📦 Files to be committed:"
echo "  - requirements.txt (Python dependencies)"
echo "  - Procfile (Railway start command)"
echo "  - railway.toml (Railway configuration)"
echo "  - nixpacks.toml (Python detection)"
echo "  - runtime.txt (Python version)"
echo "  - All documentation files"
echo "  - Modified backend files"
echo ""

read -p "Continue with commit? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted"
    exit 1
fi

# Add all files
echo ""
echo "📁 Adding all files to Git..."
git add .

# Commit
echo ""
echo "💾 Committing files..."
git commit -m "Exercise 4: Add Railway deployment configuration

- Add requirements.txt with all Python dependencies
- Add Procfile defining start command
- Add railway.toml with Python provider
- Add nixpacks.toml for explicit detection
- Add runtime.txt specifying Python 3.11
- Update backend_server.py for cloud environment
- Update supabase_client.py for cloud environment
- Update simple_call_interface.html to auto-detect backend
- Add simple_call_interface_cloud.html with configurable URL
- Add comprehensive deployment documentation:
  * EXERCISE_4_BACKEND_DEPLOYMENT.md
  * EXERCISE_4_QUICKSTART.md
  * EXERCISE_4_FILES_SUMMARY.md
  * EXERCISE_4_COMPLETE.md
  * DEPLOY_NOW.md
  * LOCAL_TESTING.md
  * TROUBLESHOOTING.md
  * RAILWAY_DEPLOYMENT_FIX.md
- Add test_deployment.sh for automated testing

All files configured for deployment to https://voxie-1.railway.app
Ready for Railway deployment with automatic Python detection.
"

echo ""
echo "✅ Files committed successfully!"
echo ""

# Show current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📌 Current branch: $CURRENT_BRANCH"
echo ""

# Ask about pushing
read -p "Push to GitHub now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "⬆️  Pushing to origin/$CURRENT_BRANCH..."
    git push origin "$CURRENT_BRANCH"

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Successfully pushed to GitHub!"
        echo ""
        echo "🎯 Next Steps:"
        echo "1. Go to Railway: https://railway.app"
        echo "2. Select your 'voxie-1' project (or create new)"
        echo "3. Click 'New' → 'GitHub Repo'"
        echo "4. Select your repository and branch: $CURRENT_BRANCH"
        echo "5. Railway will detect Python and deploy automatically!"
        echo ""
        echo "Your deployment URL: https://voxie-1.railway.app"
        echo ""
        echo "After deployment:"
        echo "- Add environment variables in Railway dashboard"
        echo "- Test: curl https://voxie-1.railway.app/"
        echo "- See DEPLOY_NOW.md for detailed instructions"
        echo ""
        echo "✨ Exercise 4 ready to deploy!"
    else
        echo ""
        echo "❌ Push failed. Please check your Git configuration."
        echo ""
        echo "Try manually:"
        echo "  git push origin $CURRENT_BRANCH"
    fi
else
    echo ""
    echo "⏸️  Files committed but not pushed."
    echo ""
    echo "To push later, run:"
    echo "  git push origin $CURRENT_BRANCH"
    echo ""
    echo "Then deploy on Railway."
fi

echo ""
echo "📚 Documentation:"
echo "  - RAILWAY_DEPLOYMENT_FIX.md  ← Fixes the Railway detection issue"
echo "  - DEPLOY_NOW.md               ← Quick deploy guide"
echo "  - TROUBLESHOOTING.md          ← Common issues and fixes"
echo ""
