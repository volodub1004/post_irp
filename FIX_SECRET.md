# Fix: Remove API Key from Git History

GitHub is blocking the push because the API key is still in git history (old commit).

## Option 1: Use GitHub's Allow Secret (Quick but not secure)

Visit this URL to allow the secret (temporary workaround):
https://github.com/volodub1004/post_irp/security/secret-scanning/unblock-secret/38lvUsYsmyIaoJOiX7tymRMMC68

**⚠️ WARNING:** This allows the exposed key to be pushed. The key should be rotated/revoked immediately.

## Option 2: Remove from Git History (Recommended)

### Step 1: Install git-filter-repo (if not installed)
```powershell
pip install git-filter-repo
```

### Step 2: Remove the secret from history
```powershell
cd "D:\brian\Projects(from 2025.6.22)\Anthony\clean-repos\post_irp"
git filter-repo --invert-paths --path notebooks/ModelDevelopment/Benchmarking.ipynb
# Then re-add the fixed file
git add notebooks/ModelDevelopment/Benchmarking.ipynb
git commit -m "Add fixed notebook without API key"
git push --force origin main
```

### Step 3: Rotate the API Key
**IMPORTANT:** Since the key was exposed, you MUST:
1. Go to OpenAI dashboard
2. Revoke the old key (check OpenAI dashboard - the key was exposed in Benchmarking.ipynb)
3. Generate a new key
4. Update any systems using the old key

## Option 3: Start Fresh (Easiest)

If this is a new repo and history doesn't matter:
```powershell
cd "D:\brian\Projects(from 2025.6.22)\Anthony\clean-repos\post_irp"
# Remove old remote
git remote remove origin
# Create new repo on GitHub (with different name or delete old one)
# Add new remote
git remote add origin https://github.com/volodub1004/post_irp.git
# Force push (this will overwrite remote history)
git push --force origin main
```

**Note:** Force push will overwrite remote history. Only do this if you're sure no one else is using the repo.
