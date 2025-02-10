import json
import os
import random
import time
import requests
import sys
from datetime import datetime, timezone
from colorama import init, Fore, Style

# Inisialisasi Colorama
init(autoreset=True)

# === KONFIGURASI PROXY (GEONODE) ===
GEONODE_API_URL = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
PROXIES = []  # List proxy

def fetch_proxies():
    """Mengambil daftar proxy dari Geonode."""
    global PROXIES
    try:
        response = requests.get(GEONODE_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        if "data" in data:
            PROXIES = [f"http://{proxy['ip']}:{proxy['port']}" for proxy in data["data"] if proxy['protocols'] == ['http']]
            print(Fore.GREEN + f"✅ Berhasil mengambil {len(PROXIES)} proxy dari Geonode!")
        else:
            print(Fore.RED + "⚠️ Tidak ada data proxy dari Geonode.")
            PROXIES = []
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal mengambil proxy: {e}")
        PROXIES = []

def get_random_proxy():
    """Mengembalikan proxy acak dari daftar yang tersedia."""
    if not PROXIES:
        fetch_proxies()
    return random.choice(PROXIES) if PROXIES else None

# === KONFIGURASI AGENT & FILE ===
agents = {
    "deployment_p5J9lz1Zxe7CYEoo0TZpRVay": {"name": "Professor 🧠", "topic": "ai"},
    "deployment_7sZJSiCqCNDy9bBHTEh7dwd9": {"name": "Crypto Buddy 💰", "topic": "crypto"},
    "deployment_SoFftlsf9z4fyA3QCHYkaANq": {"name": "Sherlock 🔎", "topic": "fraud_detection"}
}

wallet_file = "akun.txt"
interaction_log_file = "interaction_log.json"
random_questions_file = "random_questions.json"

# === FUNGSI PENDUKUNG ===
def read_wallets():
    """Membaca daftar wallet dari akun.txt."""
    try:
        with open(wallet_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + f"⚠️ File {wallet_file} tidak ditemukan!")
        sys.exit(1)

def read_interaction_log():
    """Membaca file log interaksi harian."""
    try:
        with open(interaction_log_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_interaction_log(log_data):
    """Menyimpan log interaksi ke file."""
    with open(interaction_log_file, "w") as f:
        json.dump(log_data, f, indent=2)

def get_today_date_utc():
    """Mengembalikan tanggal hari ini (UTC) dalam format YYYY-MM-DD."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def reset_daily_interactions(log_data, daily_limit, wallet):
    """Reset interaksi harian jika hari baru dimulai."""
    today_utc = get_today_date_utc()
    if log_data.get("date") != today_utc:
        print(Fore.YELLOW + "⚠️ Hari baru dimulai! Reset interaksi harian.")
        log_data = {
            "date": today_utc,
            "wallet": wallet,
            "dailyLimit": daily_limit,
            "interactions": {agent_id: 0 for agent_id in agents}
        }
    return log_data

def get_random_questions_by_topic(file_path, topic, count):
    """Mengambil pertanyaan acak dari file JSON berdasarkan topik."""
    try:
        with open(file_path, "r") as f:
            questions = json.load(f)
        return random.sample(questions.get(topic, []), min(count, len(questions.get(topic, []))))
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal membaca pertanyaan: {e}")
        sys.exit(1)

def send_question_to_agent(agent_id, question):
    """Mengirim pertanyaan ke agent menggunakan proxy acak."""
    url = f"https://{agent_id.lower().replace('_', '-')}.stag-vxzy.zettablock.com/main"
    payload = {"message": question, "stream": False}
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(3):  # Maksimal 3 kali percobaan
        proxy = get_random_proxy()
        proxies = {"http": proxy, "https": proxy} if proxy else None
        try:
            response = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=5)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]
        except Exception as e:
            print(Fore.RED + f"⚠️ (Percobaan {attempt+1}/3) Gagal mengirim ke {agent_id} melalui proxy {proxy}: {e}")
            time.sleep(2)
    return None

def report_usage(wallet, options):
    """Melaporkan penggunaan ke endpoint."""
    url = "https://quests-usage-dev.prod.zettablock.com/api/report_usage"
    payload = {
        "wallet_address": wallet,
        "agent_id": options["agent_id"],
        "request_text": options["question"],
        "response_text": options["response"],
        "request_metadata": {}
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(Fore.YELLOW + "✅ Data penggunaan berhasil dilaporkan!")
    except Exception as e:
        print(Fore.RED + f"⚠️ Gagal melaporkan penggunaan: {e}")

# === FUNGSI UTAMA ===
def main():
    print(Fore.CYAN + Style.BRIGHT + "🚀 Kite AI - Daily Interaction 🚀")
    
    wallets = read_wallets()
    interaction_log = read_interaction_log()
    daily_limit = interaction_log.get("dailyLimit", 20)
    
    for wallet_index, wallet in enumerate(wallets, start=1):
        print(Fore.YELLOW + f"\n🔄 Wallet ke-{wallet_index}: {wallet}")
        interaction_log = reset_daily_interactions(interaction_log, daily_limit, wallet)
        save_interaction_log(interaction_log)
        
        for agent_id, agent_info in agents.items():
            agent_name = agent_info['name']
            if interaction_log["interactions"].get(agent_id, 0) >= daily_limit:
                continue
            
            print(Fore.MAGENTA + f"\n🤖 Menggunakan Agent: {agent_name}")
            questions = get_random_questions_by_topic(random_questions_file, agent_info["topic"], daily_limit)
            
            for i, question in enumerate(questions, start=1):
                interaksi_ke = interaction_log["interactions"][agent_id] + 1
                print(Fore.YELLOW + f"🔄 Interaksi ke-{interaksi_ke} dengan {agent_name}")
                print(Fore.CYAN + f"❓ Pertanyaan: {question}")
                
                response = send_question_to_agent(agent_id, question) or "Tidak ada jawaban"
                print(Fore.GREEN + f"💡 Jawaban: {response}")
                report_usage(wallet, {"agent_id": agent_id, "question": question, "response": response})
                
                interaction_log["interactions"][agent_id] += 1
                save_interaction_log(interaction_log)
                time.sleep(random.randint(2, 5))

    print(Fore.GREEN + "\n✅ Semua wallet selesai diproses!")

if __name__ == "__main__":
    main()
