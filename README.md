# Mispah Skool – Digital Daily Attendance Register

A simple web system that replaces the paper “Daaglikse Leerder Bywoningsregister”.

Teachers log in, mark attendance from a shared learner list, and the administrator sees a full daily register that can be printed.

---

## Quick start (on any computer)

```bash
python3 server.py
```

Then open: **http://localhost:8080**

### Demo logins

| Role          | Username                                      | Password    |
|---------------|-----------------------------------------------|-------------|
| Administrator | `admin`                                       | `admin123`  |
| Teachers      | `maree` `cupido` `hess` `veroni` `april` `fisher` `vandyk` | `teacher123` |

---

## Deploy as a permanent website

### Option 1 – Render.com (recommended, free)

1. Create a free account at https://render.com
2. Click **New → Web Service**
3. Connect your GitHub account (or upload the zip)
4. Settings:
   - **Runtime**: Python 3
   - **Build Command**: leave empty (or `echo "no build needed"`)
   - **Start Command**: `python server.py`
5. Click **Create Web Service**

Your site will be live at something like:  
`https://mispah-attendance.onrender.com`

> Free tier spins down after 15 min of inactivity. The first visit after sleep can take ~30 seconds.

---

### Option 2 – Railway.app (also free)

1. Go to https://railway.app and sign up
2. **New Project → Deploy from GitHub** (or drag-and-drop the folder)
3. Railway detects the `Procfile` automatically
4. Your live URL appears in the dashboard

---

### Option 3 – School computer / Raspberry Pi (best for privacy)

1. Copy the whole `attendance_system` folder to the computer
2. Open a terminal and run:
   ```bash
   cd attendance_system
   python3 server.py
   ```
3. Teachers open the computer’s IP address on the school Wi-Fi, e.g.  
   `http://192.168.1.50:8080`
4. To keep it running after you close the terminal:
   ```bash
   nohup python3 server.py > attendance.log 2>&1 &
   ```

---

### Option 4 – PythonAnywhere

1. Create a free account at https://www.pythonanywhere.com
2. Upload the files via the Files tab
3. Open a Bash console and run `python server.py`
4. Use the “Web” tab to set up a WSGI or simply keep the console running

---

## Changing passwords & adding real learners

1. Log in as **admin**
2. Go to **Leerders** to add or edit learners
3. To change passwords, edit the `db.py` file (look for `hash_password(...)`) and delete the `attendance.db` file so it recreates with the new passwords, **or** use any SQLite browser on `attendance.db`.

---

## Files in this package

| File              | Purpose                              |
|-------------------|--------------------------------------|
| `server.py`       | The web application                  |
| `db.py`           | Database setup and helper functions  |
| `attendance.db`   | SQLite database (created automatically) |
| `requirements.txt`| Empty – app needs no extra packages  |
| `Procfile`        | Used by Railway / Heroku             |
| `README.md`       | This file                            |

---

**School:** Mispah Skool vir LSEN, Elim  
**Original contact:** mispah.inclusive@wcschools.gov.za
