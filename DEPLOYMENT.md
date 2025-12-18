# Deploying to Streamlit Community Cloud

This guide will help you deploy your **Recruitment Agent** to the web using Streamlit Community Cloud.

## Prerequisites
1.  A [GitHub](https://github.com/) account.
2.  A [Streamlit Community Cloud](https://streamlit.io/cloud) account (connected to your GitHub).

## Step 1: Push Code to GitHub
1.  Create a new repository on GitHub (e.g., `recruitment-agent`).
2.  Open your terminal in the project folder:
    ```powershell
    cd "C:\Users\getac\Desktop\AI Engineer Project\ai-projects\recruitment-agent"
    ```
3.  Initialize git and push:
    ```powershell
    git init
    git add .
    git commit -m "Initial deploy"
    git branch -M main
    git remote add origin https://github.com/<YOUR_USERNAME>/recruitment-agent.git
    git push -u origin main
    ```

## Step 2: Deploy on Streamlit
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **"New app"**.
3.  Select your repository (`recruitment-agent`).
4.  Set **Main file path** to `app.py`.
5.  Click **"Deploy!"**.

## Step 3: Configure Secrets (CRITICAL)
Your app will fail initially because it needs your API keys. You must move them from `secrets.toml` to the Cloud dashboard.

1.  On your deployed app screen, click "Manage app" (bottom right) or the **Settings** menu.
2.  Go to **Secrets**.
3.  Copy the **entire content** of your local `.streamlit/secrets.toml` file.
    *(It contains `[supabase]` and `[google]` sections with your keys).*
4.  Paste it into the Streamlit Secrets text area.
5.  Click **Save**.

## Step 4: Add System Dependencies (Optional)
If the app complains about missing libraries, ensure you have a `requirements.txt` file (already created).
If you need system-level packages (unlikely for this app), create a `packages.txt` file.

## Troubleshooting
-   **"Module not found"**: Check `requirements.txt`.
-   **"KeyError: 'supabase'"**: You forgot Step 3 (Secrets).
-   **"White Flash"**: We fixed this in the verification phase, so it should be smooth!
