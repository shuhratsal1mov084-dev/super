import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# =============================================
# 🔧 O'ZINGIZNING MA'LUMOTLARINGIZNI KIRITING
# =============================================
BOT_TOKEN = "BU_YERGA_BOT_TOKENINGIZNI_KIRITING"
ADMIN_ID = 123456789  # O'ZINGIZNING TELEGRAM ID
# =============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =============================================
# 🎮 OYINCHILAR — shu yerga qo'shing
# =============================================
PLAYERS = {
    "dynamo": {
        "name": "🇮🇳 Dynamo Gaming",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Dynamo_Gaming.jpg/220px-Dynamo_Gaming.jpg",
        "sensitivity": (
            "📱 Camera: 95\n"
            "ADS: 82\n"
            "Gyroscope: 280\n\n"
            "🕹 4-barmoq, Claw uslubi\n"
            "Grafika: HDR + Ultra"
        ),
    },
    "mortal": {
        "name": "🇮🇳 Mortal",
        "image": "https://upload.wikimedia.org/wikipedia/commons/3/3a/Mortal_pubg.jpg",
        "sensitivity": (
            "📱 Camera: 88\n"
            "ADS: 75\n"
            "Gyroscope: 260\n\n"
            "🕹 3-barmoq, Klassik\n"
            "Grafika: Smooth + Extreme"
        ),
    },
    "jonathan": {
        "name": "🇮🇳 Jonathan Gaming",
        "image": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Jonathan_Gaming.jpg",
        "sensitivity": (
            "📱 Camera: 87\n"
            "ADS: 77\n"
            "Gyroscope: 290\n\n"
            "🕹 4-barmoq, Aggressive\n"
            "Grafika: HDR + Ultra"
        ),
    },
    "paraboy": {
        "name": "🇺🇾 Paraboy",
        "image": "https://upload.wikimedia.org/wikipedia/commons/6/6b/Paraboy.jpg",
        "sensitivity": (
            "📱 Camera: 92\n"
            "ADS: 80\n"
            "Gyroscope: 310\n\n"
            "🕹 4-barmoq Professional\n"
            "World Esports Chempioni uslubi"
        ),
    },
}

# =============================================
# 📢 MAJBURIY KANALLAR — shu yerga qo'shing
# =============================================
# Format: {"name": "Kanal nomi", "id": "@username", "link": "https://t.me/username"}
CHANNELS = [
    # {"name": "PUBG UZ", "id": "@pubg_uz", "link": "https://t.me/pubg_uz"},
]

# ─── Conversation states ───────────────────
(
    ADD_PLAYER_NAME,
    ADD_PLAYER_IMAGE,
    ADD_PLAYER_SENSITIVITY,
    ADD_CHANNEL,
    WAIT_DELETE_PLAYER,
    WAIT_DELETE_CHANNEL,
) = range(6)


# =============================================
# KANALGA A'ZO TEKSHIRISH
# =============================================
async def check_subscriptions(user_id, context):
    if not CHANNELS:
        return True, []
    not_joined = []
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch["id"], user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)
    return len(not_joined) == 0, not_joined


def sub_keyboard(not_joined):
    keyboard = []
    for ch in not_joined:
        keyboard.append([InlineKeyboardButton(f"📢 {ch['name']} — A'zo bo'lish", url=ch["link"])])
    keyboard.append([InlineKeyboardButton("✅ A'zo bo'ldim, tekshir!", callback_data="check_sub")])
    return InlineKeyboardMarkup(keyboard)


# =============================================
# /start
# =============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ok, not_joined = await check_subscriptions(user_id, context)
    if not ok:
        await update.message.reply_text(
            "⛔ <b>Botdan foydalanish uchun avval quyidagi kanallarga a'zo bo'ling:</b>",
            reply_markup=sub_keyboard(not_joined),
            parse_mode="HTML",
        )
        return
    await show_players_menu(update.message)


async def show_players_menu(message):
    keyboard = []
    row = []
    for i, (pid, p) in enumerate(PLAYERS.items()):
        row.append(InlineKeyboardButton(p["name"], callback_data=f"player_{pid}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    await message.reply_text(
        "🎮 <b>PUBG Mobile — Mashhur Oyinchilar</b>\n\n"
        "Oyinchini tanlang 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


# =============================================
# FOYDALANUVCHI CALLBACKLARI
# =============================================
async def user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "check_sub":
        ok, not_joined = await check_subscriptions(user_id, context)
        if not ok:
            await query.message.edit_text(
                "❌ <b>Hali barcha kanallarga a'zo emassiz!</b>",
                reply_markup=sub_keyboard(not_joined),
                parse_mode="HTML",
            )
        else:
            await query.message.delete()
            await show_players_menu(query.message)
        return

    if data.startswith("player_"):
        pid = data[7:]
        if pid not in PLAYERS:
            await query.message.reply_text("❌ Oyinchi topilmadi!")
            return
        p = PLAYERS[pid]
        back = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_menu")]])
        caption = f"👤 <b>{p['name']}</b>\n\n🎯 <b>Chust va Upravlenie:</b>\n\n{p['sensitivity']}"
        try:
            await query.message.reply_photo(photo=p["image"], caption=caption, parse_mode="HTML", reply_markup=back)
        except Exception:
            await query.message.reply_text(caption, parse_mode="HTML", reply_markup=back)
        return

    if data == "back_menu":
        await show_players_menu(query.message)
        return


# =============================================
# ADMIN PANEL
# =============================================
def admin_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Oyinchi qo'shish", callback_data="adm_add_player")],
        [InlineKeyboardButton("🗑 Oyinchi o'chirish", callback_data="adm_del_player")],
        [InlineKeyboardButton("👥 Oyinchilar ro'yxati", callback_data="adm_list_players")],
        [InlineKeyboardButton("📢 Kanal qo'shish (kod orqali)", callback_data="adm_channel_info")],
        [InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="adm_list_channels")],
    ])


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return ConversationHandler.END
    await update.message.reply_text(
        "👑 <b>Admin Panel</b>\n\nNimani qilmoqchisiz?",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML",
    )
    return ConversationHandler.END


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("❌ Ruxsat yo'q!")
        return ConversationHandler.END

    data = query.data

    if data == "adm_add_player":
        await query.message.reply_text(
            "➕ <b>Yangi oyinchi — Qadam 1/3</b>\n\n"
            "Oyinchining <b>ismini</b> yuboring:\n"
            "<i>Masalan: 🇺🇿 Alpha UZ</i>\n\n"
            "/bekor — bekor qilish",
            parse_mode="HTML",
        )
        return ADD_PLAYER_NAME

    elif data == "adm_del_player":
        if not PLAYERS:
            await query.message.reply_text("📭 Hozircha oyinchi yo'q.")
            return ConversationHandler.END
        keyboard = [[InlineKeyboardButton(f"🗑 {p['name']}", callback_data=f"delp_{pid}")] for pid, p in PLAYERS.items()]
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")])
        await query.message.reply_text(
            "🗑 <b>O'chirish uchun oyinchi tanlang:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return WAIT_DELETE_PLAYER

    elif data == "adm_list_players":
        if not PLAYERS:
            text = "📭 Hozircha oyinchi yo'q."
        else:
            text = "👥 <b>Oyinchilar:</b>\n\n"
            for i, (pid, p) in enumerate(PLAYERS.items(), 1):
                text += f"{i}. {p['name']} — <code>{pid}</code>\n"
        await query.message.reply_text(text, parse_mode="HTML")
        return ConversationHandler.END

    elif data == "adm_channel_info":
        await query.message.reply_text(
            "📢 <b>Kanal qo'shish</b>\n\n"
            "Render da fayl saqlanmagani uchun kanallarni to'g'ridan-to'g'ri kodga qo'shish kerak.\n\n"
            "<b>pubg_bot.py</b> faylida <code>CHANNELS</code> ro'yxatini toping va shu formatda qo'shing:\n\n"
            "<code>{\"name\": \"Kanal nomi\", \"id\": \"@username\", \"link\": \"https://t.me/username\"}</code>\n\n"
            "Keyin GitHub ga push qiling — Render avtomatik yangilanadi.",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    elif data == "adm_list_channels":
        if not CHANNELS:
            text = "📭 Hozircha majburiy kanal yo'q.\n\nKanallarni kodga qo'shing (CHANNELS ro'yxati)."
        else:
            text = "📢 <b>Majburiy kanallar:</b>\n\n"
            for i, ch in enumerate(CHANNELS, 1):
                text += f"{i}. {ch['name']} — {ch['link']}\n"
        await query.message.reply_text(text, parse_mode="HTML")
        return ConversationHandler.END

    elif data == "adm_back":
        await query.message.reply_text(
            "👑 <b>Admin Panel</b>",
            reply_markup=admin_main_keyboard(),
            parse_mode="HTML",
        )
        return ConversationHandler.END

    elif data.startswith("delp_"):
        pid = data[5:]
        if pid in PLAYERS:
            name = PLAYERS[pid]["name"]
            del PLAYERS[pid]
            await query.message.reply_text(
                f"✅ <b>{name}</b> o'chirildi!\n\n"
                f"⚠️ Bot qayta ishga tushganda bu o'zgarish yo'qoladi.\n"
                f"Doimiy o'chirish uchun kodni ham yangilang.",
                parse_mode="HTML"
            )
        else:
            await query.message.reply_text("❌ Topilmadi.")
        return ConversationHandler.END

    return ConversationHandler.END


# =============================================
# CONVERSATION: Oyinchi qo'shish
# =============================================
async def recv_player_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    context.user_data["np_name"] = update.message.text.strip()
    await update.message.reply_text(
        "🖼 <b>Qadam 2/3 — Rasm URL</b>\n\n"
        "Oyinchining rasm URL ini yuboring:\n"
        "<i>(telegra.ph, imgur yoki boshqa to'g'ri link)</i>\n\n"
        "/bekor — bekor qilish",
        parse_mode="HTML",
    )
    return ADD_PLAYER_IMAGE


async def recv_player_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    if update.message.photo:
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        context.user_data["np_image"] = file.file_path
    else:
        context.user_data["np_image"] = update.message.text.strip()
    await update.message.reply_text(
        "🎯 <b>Qadam 3/3 — Chust va Upravlenie</b>\n\n"
        "Matnini yuboring:\n\n"
        "<code>📱 Camera: 90\n"
        "ADS: 80\n"
        "Gyroscope: 300\n\n"
        "🕹 4-barmoq + Gyro\n"
        "Grafika: Smooth + Extreme</code>\n\n"
        "/bekor — bekor qilish",
        parse_mode="HTML",
    )
    return ADD_PLAYER_SENSITIVITY


async def recv_player_sensitivity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    name = context.user_data.get("np_name", "Nomsiz")
    image = context.user_data.get("np_image", "")
    sensitivity = update.message.text.strip()

    pid = ''.join(c for c in name.lower().replace(" ", "_") if c.isalnum() or c == "_")
    if not pid:
        pid = f"player_{len(PLAYERS) + 1}"
    base_pid, counter = pid, 1
    while pid in PLAYERS:
        pid = f"{base_pid}_{counter}"
        counter += 1

    PLAYERS[pid] = {"name": name, "image": image, "sensitivity": sensitivity}

    await update.message.reply_text(
        f"✅ <b>{name}</b> qo'shildi! (faqat shu sessiyada)\n\n"
        f"⚠️ Doimiy saqlash uchun kodni ham yangilang:\n"
        f"<code>\"{pid}\": {{\n"
        f"  \"name\": \"{name}\",\n"
        f"  \"image\": \"{image}\",\n"
        f"  \"sensitivity\": \"...\"\n"
        f"}}</code>",
        parse_mode="HTML",
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END


# =============================================
# MAIN
# =============================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("admin", admin_command),
            CallbackQueryHandler(admin_callback, pattern="^adm_"),
        ],
        states={
            ADD_PLAYER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_player_name)],
            ADD_PLAYER_IMAGE: [
                MessageHandler(filters.PHOTO, recv_player_image),
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_player_image),
            ],
            ADD_PLAYER_SENSITIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_player_sensitivity)],
            WAIT_DELETE_PLAYER: [CallbackQueryHandler(admin_callback, pattern="^(delp_|adm_back)")],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(user_callback))

    print("🤖 PUBG Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
