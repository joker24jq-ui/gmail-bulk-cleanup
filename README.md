# Gmail Bulk Cleanup 🧹

A **one‑click Windows application** to bulk delete old Gmail emails. No Python setup needed — just download the `.exe` and run it.

## 🚀 Download

The Windows executable is available on the Releases page:

👉 **Download here:** https://github.com/joker24jq-ui/gmail-bulk-cleanup/releases/latest

On the releases page, download **`Gmail Bulk Cleanup.exe`**, then double‑click it to start the app.

## ✨ Features

- **Standalone .exe** – Works on Windows without installing Python
- **Modern web UI** – Runs locally in your browser at `http://localhost:5000`
- **19+ cleanup filters** – By category, age, read status, labels, custom search, and more
- **Safe previews** – Check how many emails will be affected before deleting
- **Batch deletion** – Uses Gmail API to delete in efficient batches
- **Secure OAuth 2.0** – You sign in directly with Google; credentials aren’t stored on any server

## 🧩 How It Works

1. The `.exe` starts a local Flask web server on your machine.
2. Your browser opens the **Gmail Bulk Cleanup** UI.
3. When you click **Check Count / Delete**, the app:
   - Sends a search query to the Gmail API
   - Shows how many emails match
   - Deletes them only after you confirm

All operations happen between **your computer and Google** using the official Gmail API.

## 📝 Example Cleanups

- Delete all **Promotions** older than 1 year  
- Delete **Social** notifications older than 6 months  
- Delete anything with `"receipt"` in the subject older than 6 months  
- Use a custom query like:  
  - `from:amazon.com older_than:1y`  
  - `has:attachment older_than:2y`  

## 🛠️ Run from Source (Optional)

If you prefer running the Python app instead of the `.exe`:

```bash
git clone https://github.com/joker24jq-ui/gmail-bulk-cleanup.git
cd gmail-bulk-cleanup
pip install -r requirements.txt
python run_app.py
Then open http://localhost:5000/ in your browser.

🧱 Building the .exe
To rebuild the Windows executable yourself:

bash
pip install -r requirements.txt
pyinstaller "Gmail Bulk Cleanup.spec"
The new executable will appear in the dist folder as Gmail Bulk Cleanup.exe.

🔒 Security & Privacy
Uses official Google OAuth 2.0 for Gmail access

Tokens are stored locally (token.pickle) and never uploaded by this app

No analytics, tracking, or external servers

Code is open source so you can inspect or modify it

🤝 Contributing
Issues, ideas, and pull requests are welcome.

Open an Issue for bugs or feature requests

Submit a Pull Request if you’d like to improve filters, UI, or docs

📄 License
This project is released under the MIT License.
