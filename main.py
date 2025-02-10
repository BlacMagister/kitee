import json
import os
import random
import time
import requests
import sys
from datetime import datetime, timedelta, timezone
from colorama import init, Fore, Style
import concurrent.futures
import threading
import logging

# Inisialisasi Colorama
init(autoreset=True)

# Konfigurasi Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',  # Tambahkan threadName
    handlers=[
        logging.FileHandler("kite_ai.log"),  # Log ke file
        logging.StreamHandler(sys.stdout)   # Log ke konsol
    ]
)

# Tambahkan custom level untuk sukses
SUCCESS = 25
logging.addLevelName(SUCCESS, "SUCCESS")
def success(self, message, *args, **kws):
    self.log(SUCCESS, message, *args, **kws)
logging.Logger.success = success
logging.getLogger().success = success


# Warna untuk log (bisa disesuaikan)
LOG_COLORS = {
    "INFO": Fore.CYAN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.RED + Style.BRIGHT,
    "SUCCESS": Fore.GREEN
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_color = LOG_COLORS.get(record.levelname, Fore.WHITE)
        message = super().format(record)
        return log_color + message + Style.RESET_ALL

# Ganti formatter default dengan formatter berwarna
for handler in logging.getLogger().handlers:
    handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(threadName)s - %(message)s'))

# Global lock untuk mengupdate file log dengan aman
log_lock = threading.Lock()

# Konfigurasi agents dengan topik spesifik
agents = {
    "deployment_p5J9lz1Zxe7CYEoo0TZpRVay": {"name": "Professor 🧠", "topic": "ai"},
    "deployment_7sZJSiCqCNDy9bBHTEh7dwd9": {"name": "Crypto Buddy 💰", "topic": "crypto"},
    "deployment_SoFftlsf9z4fyA3QCHYkaANq": {"name": "Sherlock 🔎", "topic": "fraud_detection"}
}

# Konfigurasi
DEFAULT_DAILY_LIMIT = 20  # Batas interaksi harian untuk semua akun
interaction_log_file = "interaction_log.json"
random_questions_file = "random_questions.json"
akun_file = "akun.txt"
RETRY_DELAY = 10  # Detik
MAX_RETRIES = 3
REPORT_USAGE_INITIAL_DELAY = 5 # Detik, delay sebelum retry report_usage pertama kali.
REQUEST_TIMEOUT = 20 # Timeout untuk request ke agent

# Fungsi untuk membaca daftar wallet dari file (1 address per baris)
def read_wallets():
    try:
        with open(akun_file, "r") as f:
            wallets = [line.strip() for line in f.readlines() if line.strip()]
        if not wallets:
            logging.error(f"File {akun_file} kosong atau tidak berisi wallet yang valid.")
            exit(1)
        return wallets
    except FileNotFoundError:
        logging.error(f"File {akun_file} tidak ditemukan! Harap buat file tersebut dengan daftar wallet.")
        exit(1)

# Fungsi untuk membaca data interaksi harian
def read_interaction_log():
    try:
        with open(interaction_log_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        logging.warning(f"File {interaction_log_file} rusak.  Memulai dengan log kosong.")
        return {}

# Fungsi untuk menyimpan data interaksi harian
def save_interaction_log(log_data):
    with log_lock:  # Amankan akses ke file
        try:
            with open(interaction_log_file, "w") as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            logging.error(f"Gagal menyimpan log interaksi: {e}")

# Fungsi untuk mendapatkan tanggal hari ini berdasarkan WIB (format YYYY-MM-DD)
def get_today_date_wib():
    now_wib = datetime.now(timezone.utc) + timedelta(hours=7)
    return now_wib.strftime("%Y-%m-%d")

# Fungsi untuk mereset interaksi harian jika hari sudah berganti (WIB)
def check_and_reset_daily_interactions(log_data, wallet, wallet_index):
    today_wib = get_today_date_wib()
    if log_data.get(wallet, {}).get("date") != today_wib:
        logging.info(f"Hari baru dimulai! Mereset interaksi harian untuk akun ke-{wallet_index}: {wallet}.")
        log_data[wallet] = {
            "index": wallet_index,  # Menyimpan nomor urut wallet
            "date": today_wib,
            "dailyLimit": DEFAULT_DAILY_LIMIT,
            "interactions": {agent_id: 0 for agent_id in agents}
        }
    return log_data

# Fungsi untuk membaca pertanyaan acak berdasarkan topik
def get_random_questions_by_topic(file_path, topic, count):
    try:
        with open(file_path, "r") as f:
            questions = json.load(f)
        questions_list = questions.get(topic, [])
        if not questions_list:
             logging.warning(f"Tidak ada pertanyaan untuk topik {topic} di {file_path}.")
             return [] # Kembalikan list kosong jika tidak ada pertanyaan
        if len(questions_list) < count:
            logging.warning(f"Jumlah pertanyaan untuk topik {topic} kurang dari {count}. Menggunakan semua pertanyaan yang tersedia.")
            return questions_list.copy()
        return random.sample(questions_list, count)
    except FileNotFoundError:
        logging.error(f"File {file_path} tidak ditemukan.")
        exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Gagal memproses JSON dari {file_path}: {e}")
        exit(1)
    except Exception as e:
        logging.error(f"Gagal membaca pertanyaan acak untuk topik {topic}: {e}")
        exit(1)

# Fungsi untuk mengirim pertanyaan ke agent AI dengan retry
def send_question_to_agent(agent_id, question):
    url = f"https://{agent_id.lower().replace('_', '-')}.stag-vxzy.zettablock.com/main"
    payload = {"message": question, "stream": False}
    headers = {"Content-Type": "application/json"}

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0].get("message", None)
            else:
                logging.warning(f"Format respons tidak sesuai dari agent {agent_id}: {data}")
                return None

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 500:
                 logging.error(f"Server Error (500) saat mengirim pertanyaan ke agent {agent_id} (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            else:
                logging.error(f"HTTP error saat mengirim pertanyaan ke agent {agent_id} (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Gagal mengirim pertanyaan ke agent {agent_id} setelah {MAX_RETRIES} percobaan.")
                return None

        except requests.exceptions.RequestException as e:  # Catch all request-related errors
            logging.error(f"Error saat mengirim pertanyaan ke agent {agent_id} (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Gagal mengirim pertanyaan ke agent {agent_id} setelah {MAX_RETRIES} percobaan.")
                return None
        except json.JSONDecodeError as e:
            logging.error(f"Gagal memproses JSON response dari agent {agent_id} (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            return None


# Fungsi untuk melaporkan penggunaan dengan retry
def report_usage(wallet, options, agent_name): # tambahkan agent name
    url = "https://quests-usage-dev.prod.zettablock.com/api/report_usage"
    payload = {
        "wallet_address": wallet,
        "agent_id": options["agent_id"],
        "request_text": options["question"],
        "response_text": options["response"],
        "request_metadata": {}
    }
    headers = {"Content-Type": "application/json"}

    for attempt in range(MAX_RETRIES):
        try:
            # Tambahkan delay sebelum retry pertama
            if attempt == 0:
                time.sleep(REPORT_USAGE_INITIAL_DELAY)

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logging.success(f"Data penggunaan untuk {wallet} ({agent_name}) berhasil dilaporkan!") #tambahkan agent name
            return  # Success, exit the retry loop

        except requests.exceptions.HTTPError as http_err:
            status = http_err.response.status_code if http_err.response else None
            if status == 429:
                delay = 2 ** attempt  # Exponential backoff
                logging.warning(f"Rate limit terdeteksi saat melaporkan penggunaan untuk {wallet} ({agent_name}), retrying dalam {delay} detik... ({attempt + 1}/{MAX_RETRIES})") #tambahkan agent name
                time.sleep(delay)
            else:
                logging.error(f"Gagal melaporkan penggunaan untuk {wallet} ({agent_name}): {http_err}") #tambahkan agent name
                return

        except requests.exceptions.RequestException as e:
            logging.error(f"Gagal melaporkan penggunaan untuk {wallet} ({agent_name}) (Attempt {attempt + 1}/{MAX_RETRIES}): {e}") #tambahkan agent name
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Gagal melaporkan penggunaan untuk {wallet} ({agent_name}) setelah {MAX_RETRIES} percobaan.") #tambahkan agent name
                return
        except Exception as e:
            logging.error(f"Gagal melaporkan penggunaan untuk {wallet} ({agent_name}): {e}") #tambahkan agent name
            return

# Fungsi yang memproses interaksi untuk satu agent secara concurrent
def process_agent_interactions(agent_id, agent_info, wallet, questions, interaction_log):
    agent_name = agent_info["name"]
    logging.info(f"Menggunakan Agent: {agent_name} (concurrent) untuk wallet: {wallet}")

    # Periksa batas interaksi harian
    if interaction_log[wallet]["interactions"][agent_id] >= DEFAULT_DAILY_LIMIT:
        logging.warning(f"Batas interaksi harian untuk {agent_name} sudah tercapai ({DEFAULT_DAILY_LIMIT}x) untuk wallet: {wallet}.")
        return

    remaining_interactions = DEFAULT_DAILY_LIMIT - interaction_log[wallet]["interactions"][agent_id]
    for _ in range(remaining_interactions):
        if not questions:
            logging.warning(f"Tidak ada pertanyaan tersisa untuk topik {agent_info['topic']} untuk wallet: {wallet}.")
            break

        question = questions.pop()
        logging.info(f"Pertanyaan untuk {agent_name} untuk wallet {wallet}: {question}")
        response = send_question_to_agent(agent_id, question)

        if response:
            response_text = response
        else:
            response_text = "Tidak ada jawaban"

        if isinstance(response_text, dict):
            response_text = response_text.get("content", "Tidak ada jawaban")

        #panggil report usage dengan agent name
        report_usage(wallet.lower(), {
            "agent_id": agent_id,
            "question": question,
            "response": response_text
        }, agent_name)

        with log_lock:
            interaction_log[wallet]["interactions"][agent_id] += 1
            save_interaction_log(interaction_log)

        time.sleep(random.randint(5, 10))  # Jeda antar interaksi

# Fungsi utama
def main():
    logging.info("🚀 Kite AI - Multi Account Daily Interaction 🚀")
    logging.info("----------------------------------------")

    # Pastikan file random_questions.json ada, jika tidak buat file tersebut
    if not os.path.exists(random_questions_file):
        logging.warning("File random_questions.json tidak ditemukan. Membuat file baru...")
        try:
            os.system(f"{sys.executable} rand.py")
            logging.info("File random_questions.json berhasil dibuat.")
        except Exception as e:
            logging.error(f"Gagal menjalankan rand.py: {e}")
            exit(1)

    while True:
        wallets = read_wallets()
        logging.info(f"Ditemukan {len(wallets)} akun dalam {akun_file}")

        # Baca data interaksi harian
        interaction_log = read_interaction_log()

        # Proses setiap akun secara berurutan
        for index, wallet in enumerate(wallets, start=1):
            logging.info(f"Memproses akun ke-{index}: {wallet}")
            interaction_log = check_and_reset_daily_interactions(interaction_log, wallet, index)
            save_interaction_log(interaction_log)

            # Ambil pertanyaan acak dari file random_questions.json per topik untuk masing-masing agent
            random_questions_by_topic_dict = {}
            for agent_id, agent_info in agents.items():
                topic = agent_info["topic"]
                random_questions_by_topic_dict[agent_id] = get_random_questions_by_topic(random_questions_file, topic, DEFAULT_DAILY_LIMIT)

            # Jalankan interaksi untuk ketiga agent secara concurrent
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(agents), thread_name_prefix="AgentThread-") as executor:
                futures = []
                for agent_id, agent_info in agents.items():
                    # Skip agent jika tidak ada pertanyaan untuk topiknya
                    if not random_questions_by_topic_dict[agent_id]:
                        logging.warning(f"Tidak ada pertanyaan untuk agent {agent_info['name']} (topik: {agent_info['topic']}). Melewati.")
                        continue

                    futures.append(
                        executor.submit(
                            process_agent_interactions,
                            agent_id,
                            agent_info,
                            wallet,
                            random_questions_by_topic_dict[agent_id],
                            interaction_log
                        )
                    )
                # Tunggu hingga semua thread selesai
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()  # Re-raise any exceptions that occurred in the thread
                    except Exception as e:
                        logging.error(f"Thread mengalami error: {e}")

        logging.info("Sesi selesai! Menunggu hingga ±08:00 WIB untuk interaksi berikutnya...")

        # Hitung waktu hingga reset harian (08:00 WIB)
        now_wib = datetime.now(timezone.utc) + timedelta(hours=7)
        next_reset_wib = now_wib.replace(hour=8, minute=0, second=0, microsecond=0)
        if next_reset_wib <= now_wib:
            next_reset_wib += timedelta(days=1)
        time_until_reset = (next_reset_wib - now_wib).total_seconds()
        logging.info(f"Waktu hingga reset harian: {int(time_until_reset)} detik")

        time.sleep(time_until_reset)


if __name__ == "__main__":
    main()
