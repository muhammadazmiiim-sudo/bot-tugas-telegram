import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

# Inisialisasi Database SQLite
def init_db():
    conn = sqlite3.connect('tugas.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            task_name TEXT,
            deadline TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Halo! Bot pengelola tugas kerja & kuliah kamu sudah aktif dengan fitur pengingat.\n\n"
        "**Perintah yang tersedia:**\n"
        "• `/tambah [kategori] | [nama tugas] | [DD-MM-YYYY]`\n"
        "  (Contoh: `/tambah Kuliah | Tugas PBO | 10-10-2026`)\n"
        "• `/list` - Melihat daftar tugas\n"
        "• `/selesai [id]` - Menandai tugas selesai\n"
        "• `/hapus [id]` - Menandais tugas"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

# Perintah /tambah
async def tambah_tugas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = " ".join(context.args)
    
    try:
        parts = text.split("|")
        category = parts[0].strip()
        task_name = parts[1].strip()
        deadline = parts[2].strip()
        
        # Validasi format tanggal sederhana
        datetime.strptime(deadline, "%d-%m-%Y")
        
        conn = sqlite3.connect('tugas.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (user_id, category, task_name, deadline, status) VALUES (?, ?, ?, ?, ?)",
                       (user_id, category, task_name, deadline, "Belum Selesai"))
        conn.commit()
        conn.close()
        
        await update.message.reply_text("Tugas berhasil ditambahkan dan pengingat aktif!")
    except Exception:
        await update.message.reply_text("Format salah! Gunakan format:\n`/tambah Kategori | Nama Tugas | 31-12-2026`", parse_mode="Markdown")

# Perintah /list
async def list_tugas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('tugas.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, category, task_name, deadline, status FROM tasks WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        await update.message.reply_text("Belum ada tugas yang tersimpan.")
        return
    
    message = "**Daftar Tugas Kamu:**\n\n"
    for row in rows:
        task_id, category, task_name, deadline, status = row
        icon = "✅" if status == "Selesai" else "⏳"
        message += f"ID: {task_id} | [{category}] {task_name}\nDeadline: {deadline}\nStatus: {icon} {status}\n-------------------\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

# Perintah /selesai
async def selesai_tugas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        task_id = context.args[0]
        conn = sqlite3.connect('tugas.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = 'Selesai' WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Tugas dengan ID {task_id} diubah menjadi Selesai! 🎉")
    except Exception:
        await update.message.reply_text("Gunakan format: `/selesai [id_tugas]`", parse_mode="Markdown")

# Perintah /hapus
async def hapus_tugas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        task_id = context.args[0]
        conn = sqlite3.connect('tugas.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Tugas dengan ID {task_id} berhasil dihapus.")
    except Exception:
        await update.message.reply_text("Gunakan format: `/hapus [id_tugas]`", parse_mode="Markdown")

# Fungsi Pengecekan Deadline Otomatis
async def cek_deadline(application):
    conn = sqlite3.connect('tugas.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, category, task_name, deadline FROM tasks WHERE status = 'Belum Selesai'")
    rows = cursor.fetchall()
    conn.close()
    
    hari_ini = datetime.now().strftime("%d-%m-%Y")
    
    for row in rows:
        user_id, category, task_name, deadline = row
        if deadline == hari_ini:
            pesan = f"🚨 **PENGINGAT DEADLINE HARI INI!** 🚨\n\nKategori: {category}\nTugas: {task_name}\nSegera selesaikan tugasmu ya!"
            await application.bot.send_message(chat_id=user_id, text=pesan, parse_mode="Markdown")

# Main Program
def main():
    TOKEN = "8388402140:AAEMIGIH6EiPDPaKm1v_LmYQ4PCwXC-SYDQ"
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tambah", tambah_tugas))
    app.add_handler(CommandHandler("list", list_tugas))
    app.add_handler(CommandHandler("selesai", selesai_tugas))
    app.add_handler(CommandHandler("hapus", hapus_tugas))
    
    # Konfigurasi Scheduler untuk mengecek deadline setiap hari jam 08:00 pagi
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.job_queue.run_once(lambda ctx: cek_deadline(app), 0), 'cron', hour=8, minute=0)
    scheduler.start()
    
    print("Bot dan sistem pengingat sedang berjalan...")
    app.run_polling()

if __name__ == '__main__':
    main()
