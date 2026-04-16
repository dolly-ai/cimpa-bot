from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                           MessageHandler, filters, ConversationHandler,
                           ContextTypes)
import sqlite3
import os

TOKEN = os.environ.get("TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# State untuk ConversationHandler
NAMA, NOMOR_HP, LAYANAN, DETAIL = range(4)

# ─────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    # Drop table lama jika ada dan buat ulang
    c.execute("DROP TABLE IF EXISTS orders")
    c.execute('''CREATE TABLE orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    nama TEXT,
                    nomor_hp TEXT,
                    layanan TEXT,
                    detail TEXT,
                    status TEXT DEFAULT 'Menunggu Konfirmasi',
                    waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def simpan_order(user_id, username, nama, nomor_hp, layanan, detail):
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, username, nama, nomor_hp, layanan, detail) VALUES (?,?,?,?,?,?)",
              (user_id, username, nama, nomor_hp, layanan, detail))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_orders_by_user(user_id):
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("SELECT id, layanan, status, waktu FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 5", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# ─────────────────────────────────────────
# MENU UTAMA (Keyboard Interaktif)
# ─────────────────────────────────────────
def menu_utama():
    keyboard = [
        [InlineKeyboardButton("📋 Lihat Layanan", callback_data="lihat_layanan")],
        [InlineKeyboardButton("🛒 Buat Order", callback_data="mulai_order")],
        [InlineKeyboardButton("📦 Cek Status Order", callback_data="cek_status")],
        [InlineKeyboardButton("📞 Hubungi Admin", callback_data="hubungi_admin")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ─────────────────────────────────────────
# /start
# ─────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nama = update.effective_user.first_name
    await update.message.reply_text(
        f"Halo *{nama}*! 👋\n\n"
        "Selamat datang di *Cimpa IT Services* 🚀\n"
        "Kami siap membantu bisnis kamu go digital!\n\n"
        "Silakan pilih menu di bawah ini:",
        parse_mode="Markdown",
        reply_markup=menu_utama()
    )

# ─────────────────────────────────────────
# CALLBACK TOMBOL
# ─────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "lihat_layanan":
        keyboard = [
            [InlineKeyboardButton("🛒 Order Sekarang", callback_data="mulai_order")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="kembali")]
        ]
        await query.edit_message_text(
            "📋 *LAYANAN KAMI:*\n\n"
            "1️⃣ *Landing Page* — Rp 500.000\n"
            "   Website 1 halaman, modern & responsif\n\n"
            "2️⃣ *Bot Telegram* — Rp 750.000\n"
            "   Bot custom sesuai kebutuhan bisnis\n\n"
            "3️⃣ *Aplikasi Web* — Rp 1.500.000\n"
            "   Web app lengkap dengan database\n\n"
            "4️⃣ *Toko Online* — Rp 2.000.000\n"
            "   Lengkap dengan katalog & order system\n\n"
            "_Harga bisa disesuaikan. Konsultasi GRATIS!_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "cek_status":
        orders = get_orders_by_user(query.from_user.id)
        if not orders:
            text = "📭 Kamu belum punya order.\n\nYuk mulai order pertamamu!"
        else:
            text = "📦 *Status Order Kamu:*\n\n"
            for o in orders:
                status_emoji = {"Menunggu Konfirmasi": "🟡", "Diproses": "🔵", "Selesai": "✅", "Dibatalkan": "❌"}.get(o[2], "⚪")
                text += f"Order #{o[0]}\n"
                text += f"📦 {o[1]}\n"
                text += f"{status_emoji} Status: {o[2]}\n"
                text += f"🕐 {o[3][:16]}\n\n"

        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="kembali")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "hubungi_admin":
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="kembali")]]
        await query.edit_message_text(
            "📞 *Hubungi Kami:*\n\n"
            "💬 Telegram Admin: @username_admin_kamu\n"
            "📱 WhatsApp: 08xxxxxxxxxx\n"
            "⏰ Respon: Senin–Sabtu, 08.00–21.00\n\n"
            "_Konsultasi gratis, tanpa syarat!_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "kembali":
        nama = query.from_user.first_name
        await query.edit_message_text(
            f"Halo *{nama}*! 👋\n\n"
            "Selamat datang di *Cimpa IT Services* 🚀\n"
            "Kami siap membantu bisnis kamu go digital!\n\n"
            "Silakan pilih menu di bawah ini:",
            parse_mode="Markdown",
            reply_markup=menu_utama()
        )

    elif data == "mulai_order":
        await query.edit_message_text(
            "📝 *Form Order — Langkah 1/4*\n\n"
            "Silakan ketik *nama lengkap* kamu:",
            parse_mode="Markdown"
        )
        return NAMA

# ─────────────────────────────────────────
# CONVERSATION — FORM ORDER
# ─────────────────────────────────────────
async def tanya_nama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nama'] = update.message.text
    await update.message.reply_text(
        "📝 *Form Order — Langkah 2/4*\n\n"
        "Ketik *nomor HP/WhatsApp* kamu\n"
        "_(agar kami bisa menghubungi kamu)_",
        parse_mode="Markdown"
    )
    return NOMOR_HP

async def tanya_hp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nomor_hp'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Landing Page — Rp 500rb", callback_data="pilih_Landing Page - Rp 500.000")],
        [InlineKeyboardButton("Bot Telegram — Rp 750rb", callback_data="pilih_Bot Telegram - Rp 750.000")],
        [InlineKeyboardButton("Aplikasi Web — Rp 1.5jt", callback_data="pilih_Aplikasi Web - Rp 1.500.000")],
        [InlineKeyboardButton("Toko Online — Rp 2jt", callback_data="pilih_Toko Online - Rp 2.000.000")],
    ]
    await update.message.reply_text(
        "📝 *Form Order — Langkah 3/4*\n\n"
        "Pilih layanan yang kamu inginkan:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return LAYANAN

async def pilih_layanan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    layanan = query.data.replace("pilih_", "")
    context.user_data['layanan'] = layanan
    await query.edit_message_text(
        "📝 *Form Order — Langkah 4/4*\n\n"
        f"Layanan dipilih: *{layanan}*\n\n"
        "Ceritakan kebutuhan kamu lebih detail:\n"
        "_(contoh: warna, fitur khusus, referensi, dll)_",
        parse_mode="Markdown"
    )
    return DETAIL

async def simpan_dan_kirim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    detail = update.message.text
    user = update.effective_user
    data = context.user_data

    order_id = simpan_order(
        user.id,
        user.username or "tidak ada",
        data['nama'],
        data['nomor_hp'],
        data['layanan'],
        detail
    )

    # Konfirmasi ke user
    await update.message.reply_text(
        f"✅ *Order #{order_id} Berhasil Dikirim!*\n\n"
        f"👤 Nama: {data['nama']}\n"
        f"📱 HP: {data['nomor_hp']}\n"
        f"📦 Layanan: {data['layanan']}\n"
        f"📝 Detail: {detail}\n\n"
        "Tim kami akan menghubungi kamu dalam *1x24 jam*. 🙏\n\n"
        "Ketik /start untuk kembali ke menu.",
        parse_mode="Markdown"
    )

    # Notifikasi ke admin
    pesan_admin = (
        f"🔔 *ORDER BARU MASUK! — #{order_id}*\n\n"
        f"👤 Nama: {data['nama']}\n"
        f"📱 HP: {data['nomor_hp']}\n"
        f"📦 Layanan: {data['layanan']}\n"
        f"📝 Detail: {detail}\n"
        f"🆔 Telegram: @{user.username or 'tidak ada'}\n"
        f"🔗 User ID: {user.id}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=pesan_admin, parse_mode="Markdown")
    except:
        pass

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Order dibatalkan. Ketik /start untuk mulai lagi.")
    context.user_data.clear()
    return ConversationHandler.END

# ──────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────
def main():
    init_db()
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^mulai_order$")],
        states={
            NAMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, tanya_nama)],
            NOMOR_HP: [MessageHandler(filters.TEXT & ~filters.COMMAND, tanya_hp)],
            LAYANAN: [CallbackQueryHandler(pilih_layanan, pattern="^pilih_")],
            DETAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, simpan_dan_kirim)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Bot berjalan... OK")
    application.run_polling()

if __name__ == "__main__":
    main()