# 🤖 Advanced Telegram Broadcast & Auto-Reply Bot

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Data-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

[![Telegram](https://img.shields.io/badge/Telegram-Join%20Channel-2CA5E0?style=flat&logo=telegram&logoColor=white)](https://t.me/imrankhan95)
[![Instagram](https://img.shields.io/badge/Instagram-Follow%20Me-E4405F?style=flat&logo=instagram&logoColor=white)](https://www.instagram.com/_imrannkhn/)
[![Website](https://img.shields.io/badge/Website-Mystic%20Movies-4caf50?style=flat&logo=google-chrome&logoColor=white)](https://mysticmovies.site/)

---

A powerful, full-featured Telegram bot built with **Python** and **SQLite**. It features a user database, an interactive Admin Panel, broadcasting capabilities, and auto-deleting messages with persistent warnings.

---

## ✨ Features

### 👤 **User Management**
- **Silent User Saving:** Automatically saves every user's ID, Username, and Name into a local SQLite database (`bot_data.db`) upon their first interaction.
- **Zero Config Database:** No need to install MySQL or PostgreSQL; uses built-in SQLite.

### 👮‍♂️ **Admin Panel (GUI-like)**
- **Interactive Menu:** Accessible via the `/admin` command (restricted to the Admin ID).
- **Live Stats:** View total user count instantly.
- **View Current Message:** Preview exactly what users see.
- **Custom Auto-Reply:** Set a welcome message with **Text** or **Image + Caption** directly from the chat.
- **Auto-Delete Timer:** Set a self-destruct timer for the welcome message (e.g., delete after 10 seconds).

### 📢 **Broadcasting**
- **Rich Media Support:** Broadcast **Text, Photos, Videos, Stickers, or Voice Notes** to all users.
- **Smart Forwarding:** Uses `copy_message` to ensure perfect delivery.
- **Performance Report:** Returns a summary of **Success vs. Blocked** users after broadcasting.

### ⚙️ **Advanced Logic**
- **JobQueue:** Handles auto-deletion of messages seamlessly.
- **Persistent Warning:** If a message auto-deletes, a permanent "Link Expired" warning is left in its place with instructions.
- **Error Handling:** Robust error catching for blocked users or API limits.

---

## 🛠️ Prerequisites

Before you begin, ensure you have met the following requirements:
* **Python 3.9+** installed.
* A **Telegram Bot Token** (from [@BotFather](https://t.me/BotFather)).
* Your numeric **Telegram User ID** (from [@userinfobot](https://t.me/userinfobot)).

---

## 🚀 Installation

1.  **Clone the repository** (or download the files):
    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
    cd YOUR_REPO_NAME
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(If you don't have a `requirements.txt`, run: `pip install "python-telegram-bot[job-queue]"`)*

3.  **Configure the Bot:**
    Open `bot.py` and edit the configuration section:
    ```python
    # --- CONFIGURATION ---
    TOKEN = "YOUR_BOT_TOKEN"    # Your Bot Token
    ADMIN_ID = 123456789        # Your Numeric Admin ID
    ```

---

## 🕹️ Usage

### Running the Bot
```bash
python bot.py
