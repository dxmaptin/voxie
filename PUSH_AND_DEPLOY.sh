#!/bin/bash

# Quick Push and Deploy Script
# This will push the Railway deployment fix to GitHub

echo "🔧 Railway Deployment Fix - Push Script"
echo "======================================="
echo ""

# Navigate to correct directory
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

echo "📍 Current directory: $(pwd)"
echo ""

# Show what's committed
echo "📦 Commits ready to push:"
git log origin/malik-branch-ex2..HEAD --oneline
echo ""

# Show current status
echo "📋 Git Status:"
git status --short
echo ""

# Ask for confirmation
echo "🚀 Ready to push the fix to GitHub?"
echo ""
echo "This will push:"
echo "  ✅ function_call/__init__.py (CRITICAL FIX)"
echo "  ✅ RAILWAY_DEBUG_GUIDE.md"
echo "  ✅ DEPLOYMENT_FIX_READY.md"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted"
    exit 1
fi

echo ""
echo "⬆️  Pushing to GitHub..."
echo ""

# Try to push
git push origin malik-branch-ex2

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🎯 Next Steps:"
    echo ""
    echo "1. Railway will auto-deploy in 2-3 minutes"
    echo "   Watch at: https://railway.app"
    echo ""
    echo "2. After deployment succeeds, add environment variables:"
    echo "   Go to: Railway Dashboard → voxie-1 → Variables"
    echo "   Add all variables from DEPLOYMENT_FIX_READY.md"
    echo ""
    echo "3. Click 'Deploy' to restart with environment variables"
    echo ""
    echo "4. Test deployment:"
    echo "   curl https://voxie-1.railway.app/"
    echo ""
    echo "✨ Your backend will be live at: https://voxie-1.railway.app"
else
    echo ""
    echo "❌ Push failed!"
    echo ""
    echo "📋 Common solutions:"
    echo ""
    echo "1. Authenticate with Personal Access Token:"
    echo "   Go to: https://github.com/settings/tokens"
    echo "   Generate a token with 'repo' scope"
    echo "   Then run:"
    echo "   git push https://YOUR_TOKEN@github.com/mmamuhammad2006/voxie.git malik-branch-ex2"
    echo ""
    echo "2. Or use SSH (if configured):"
    echo "   git remote set-url origin git@github.com:mmamuhammad2006/voxie.git"
    echo "   git push origin malik-branch-ex2"
    echo ""
    echo "3. Or use GitHub CLI:"
    echo "   gh auth login"
    echo "   git push origin malik-branch-ex2"
    echo ""
fi

echo ""
echo "📚 Documentation:"
echo "  - DEPLOYMENT_FIX_READY.md  ← Read this for full instructions"
echo "  - RAILWAY_DEBUG_GUIDE.md   ← If issues persist"
echo ""
