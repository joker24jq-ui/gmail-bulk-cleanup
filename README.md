
text
# Gmail Bulk Cleanup 🧹
A **powerful, one-click Windows application** to bulk delete old Gmail emails. Works without Python installation — just download and run!
 ## ✨ Features

- **One-Click Executable** - No Python installation needed
- **19 Email Filter Options** - Delete by category, age, sender, keywords, and more
- **Safe Multi-Confirmation System** - Review before you delete
- **Real-Time Progress Tracking** - Watch your inbox get cleaned
- **Secure OAuth Authentication** - Your credentials stay safe
- **Beautiful Web Interface** - Runs in your browser

## 🚀 Quick Start

1. **Download** the latest `.exe` from [Releases](https://github.com/joker24jq-ui/gmail-bulk-cleanup/releases)
2. **Double-click** `Gmail Bulk Cleanup.exe`
3. **Authorize** Gmail access when prompted (first time only)
4. **Select** your filters and delete!

## 🎯 Common Use Cases

### Delete Old Promotional Emails
Filter: Promotions category
Older than: 1 year

text

### Clean Up Social Notifications
Filter: Social updates category
Older than: 6 months

text

### Remove Old Forums/Mailing Lists
Filter: Forums category
Older than: 2 years

text

### Custom Search
Use any Gmail search syntax:
- `from:amazon@amazon.com older_than:1y`
- `subject:receipt older_than:6m`
- `has:attachment older_than:2y`

## 🔒 Security & Privacy

- ✅ OAuth 2.0 authentication (your password never stored)
- ✅ Credentials stored locally only
- ✅ No data sent to third-party servers
- ✅ Open source — audit the code yourself
- ✅ Runs entirely on your machine

## 📋 System Requirements

- **Windows 7** or later
- **Internet connection**
- **Gmail account**

## 🛠️ Build from Source (Optional)

If you want to build it yourself:

```bash
git clone https://github.com/joker24jq-ui/gmail-bulk-cleanup.git
cd gmail-bulk-cleanup
pip install -r requirements.txt
python run_app.py
pyinstaller Gmail\ Bulk\ Cleanup.spec
📝 Available Filters
✉️ By Category: Promotions, Social, Updates, Forums

🕐 By Age: Older than (1m, 3m, 6m, 1y, 2y)

👤 By Sender: Specific email addresses

🔤 By Keyword: Custom Gmail search queries

📎 With Attachments: Find and delete files

🏷️ By Label: Specific Gmail labels

⚠️ Important Notes
Review Before Deleting - Use the preview to see what will be deleted

Test First - Start with smaller batches to get comfortable

No Undo - Deleted emails go to Gmail's Trash for 30 days

Automatic Filter - Once enabled, Gmail's built-in filter auto-deletes emails older than 2 years

🤝 Contributing
Found a bug? Want to suggest a feature? Open an Issue or submit a Pull Request!

📄 License
MIT License - Feel free to use, modify, and distribute!

🙏 Support
If you find this useful, consider:

⭐ Starring the repo

📢 Sharing with friends

🐛 Reporting bugs

💡 Suggesting improvements
