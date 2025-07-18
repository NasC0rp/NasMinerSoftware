# 🔥 NasMiner PRO - Visual Mining Software

**NasMiner PRO** is a clean, user-friendly mining dashboard that lets you mine multiple cryptocurrencies using your CPU. Designed for performance, clarity, and accessibility, NasMiner PRO combines power and simplicity with a dark-themed visual interface.

---

## 💡 Features

- ✅ **Multi-Crypto Mining** — Supports LTC, ETH, BNB, and SOL with switchable or simultaneous mining.
- 🔐 **Custom Wallets & Workers** — Easily set and save your wallet addresses and worker name.
- 🎛️ **Thread Control** — Adjust CPU threads (mining intensity) directly from the GUI.
- 📊 **Live Stats** — Real-time display of:
  - CPU and RAM usage
  - Energy consumption estimate (kWh)
  - Total estimated mined crypto
  - Estimated earnings in EUR
- 🧠 **Smart Estimation Engine** — Uses fixed share rates and live crypto prices (via CoinGecko API) to estimate earnings.
- 📓 **Mining Logs** — Real-time miner logs with accepted shares and technical output.

---

## 🚀 How It Works

1. **Select a Coin** from the top panel using its logo.
2. **Enter your Wallet Address** and **Worker Name**.
3. **Adjust the Thread Slider** to control how many CPU threads are used.
4. *(Optional)* Check the **Multi-Crypto Mode** box to mine all coins at once.
5. Click **"Start Mining"** — NasMiner will launch and monitor the mining process.

> Behind the scenes, NasMiner uses a high-performance mining core engine and connects to reliable mining pools optimized for each coin.

---

## 📦 Installation

1. Ensure you have **Python 3.9+** installed.
2. Run `setup.bat` (included) to install dependencies and prepare the software.
3. Run the software:
   ```bash
   python main.py
