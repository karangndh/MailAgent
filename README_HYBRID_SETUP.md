# 🚀 Hybrid Mail Agent Setup

Create a `.exe` package that Windows users can run to process their own emails while using your shared database and LLM services.

## 📋 Overview

### **Architecture:**
```
Windows User (.exe) → Their Outlook Login → Extract Emails → Your Database + LLM
```

### **What Each User Gets:**
- ✅ **Their own Outlook login** (processes their emails)
- ✅ **No dependencies** (everything bundled in .exe)
- ✅ **Shared database** (all results in one place)
- ✅ **Shared LLM** (uses your Ollama service)

---

## 🛠️ **Step 1: Build the Hybrid Executable**

### **On Your Machine (Host):**

```bash
# 1. Navigate to your MailAgent directory
cd /path/to/MailAgent

# 2. Build the hybrid executable
python build_executable.py

# 3. When prompted, select option 2
# Select build type:
# 1. Full standalone executables (local setup)
# 2. Hybrid client executable (connects to remote services)
# Enter choice (1 or 2): 2
```

### **Result:**
- Creates `dist/MailAgent_Client.exe` (Windows executable)
- Self-contained with all dependencies
- Connects to your machine for database and LLM

---

## 🌐 **Step 2: Setup Host Machine (Your Machine)**

### **1. Start Web Interface in Host Mode:**
```bash
# Enable external access (replace YOUR_IP with your actual IP)
python web_interface.py --host 0.0.0.0 --port 8080
```

### **2. Get Your IP Address:**

**On macOS:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**On Windows:**
```bash
ipconfig | findstr "IPv4"
```

**On Linux:**
```bash
hostname -I
```

### **3. Configure Firewall:**
- **macOS:** System Preferences > Security & Privacy > Firewall > Allow port 8080
- **Windows:** Windows Defender Firewall > Allow port 8080
- **Linux:** `sudo ufw allow 8080`

### **4. Test Connection:**
```bash
# From another machine, test if accessible:
curl http://YOUR_IP_ADDRESS:8080/api/status
```

---

## 📦 **Step 3: Distribute to Windows Users**

### **What to Share:**
1. **`MailAgent_Client.exe`** file (from `dist/` folder)
2. **Your IP address** and **port number**
3. **Simple instructions** (see below)

### **Instructions for Windows Users:**

```
📧 Mail Agent Client - Setup Instructions

1. Download MailAgent_Client.exe
2. Double-click to run
3. When prompted, enter:
   - Host IP: [YOUR_IP_ADDRESS]
   - Port: 8080
4. Click OK to connect
5. Log into your Outlook account when browser opens
6. Wait for processing to complete
7. View results at: http://[YOUR_IP_ADDRESS]:8080

That's it! Your emails will be processed and added to the shared database.
```

---

## 🔧 **Step 4: How It Works**

### **User Experience:**
1. **Run .exe** → Opens setup dialog
2. **Enter your IP** → Connects to your services
3. **Login to Outlook** → Uses their own account
4. **Processing** → Extracts their emails
5. **Results** → Saved to your shared database

### **Technical Flow:**
```mermaid
graph TD
    A[Windows User runs .exe] --> B[Enter Host IP]
    B --> C[Connect to your machine]
    C --> D[Open their Outlook]
    D --> E[Extract their emails]
    E --> F[Send to your database]
    E --> G[Use your LLM service]
    F --> H[View results on your dashboard]
```

---

## 📊 **Step 5: Monitor Results**

### **Your Dashboard:**
- **URL:** `http://localhost:8080`
- **Shows emails from all users**
- **Summary counts include everyone**
- **Real-time updates**

### **User Activity:**
```
Total LOAs: 15 (from all users)
Approved: 8
Awaiting: 7

Recent Activity:
- John.Smith@company.com: 3 emails processed
- Jane.Doe@company.com: 2 emails processed
```

---

## 🔐 **Security Considerations**

### **What's Shared:**
- ✅ **Database:** All processed email data
- ✅ **LLM Service:** Text summarization
- ✅ **Web Dashboard:** View all results

### **What's Private:**
- 🔒 **Outlook Login:** Each user uses their own
- 🔒 **Email Content:** Only processed metadata shared
- 🔒 **Credentials:** Never transmitted

### **Recommendations:**
- Use **VPN** for secure connection
- Set up **HTTPS** for production
- Implement **user authentication** for dashboard
- Consider **database backups**

---

## 🚀 **Quick Start Commands**

### **Host Machine:**
```bash
# Build executable
python build_executable.py  # Choose option 2

# Start host service
python web_interface.py --host 0.0.0.0

# Check status
curl http://localhost:8080/api/status
```

### **Windows User:**
```bash
# Just run the executable
MailAgent_Client.exe
```

---

## 🎯 **Benefits of This Setup**

| Feature | Benefit |
|---------|---------|
| **Centralized Database** | All email data in one place |
| **Shared LLM** | No need for users to install Ollama |
| **No Dependencies** | Users just run .exe file |
| **Own Outlook** | Each user processes their emails |
| **Easy Updates** | Update .exe and redistribute |
| **Scalable** | Add more users easily |

---

## 🔧 **Troubleshooting**

### **Connection Issues:**
```bash
# Test connectivity
ping YOUR_IP_ADDRESS
telnet YOUR_IP_ADDRESS 8080
```

### **Firewall Problems:**
- Check host machine firewall
- Verify port 8080 is open
- Test from local network first

### **Executable Issues:**
- Run as administrator on Windows
- Check antivirus settings
- Verify .exe is not corrupted

---

## 📈 **Scaling Up**

### **For More Users:**
1. **Upgrade Database:** SQLite → PostgreSQL/MySQL
2. **Add Authentication:** User login system
3. **Use HTTPS:** Secure connections
4. **Load Balancing:** Multiple host machines
5. **Docker Deployment:** Containerized services

### **Enterprise Setup:**
```bash
# Example with PostgreSQL
docker run -d \
  --name mailagent-db \
  -e POSTGRES_DB=mailagent \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=secure123 \
  -p 5432:5432 \
  postgres:13

# Run web interface with PostgreSQL
python web_interface.py --host 0.0.0.0 --db postgresql://admin:secure123@localhost:5432/mailagent
```

---

This setup allows you to create a true **"plug-and-play"** solution where Windows users can process their own emails with zero setup while leveraging your shared infrastructure! 🎉 