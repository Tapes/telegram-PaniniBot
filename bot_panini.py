import requests
import sys
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

# -------- CONFIG --------
TOKEN = "8979502192:AAEpZ4nx0pZiX8qNY708s1dTZQSO-_eKda0"
CHAT_ID = None  # 👈 guardado após /start

# 👉 Lista de produtos
PRODUCTS = {
    "Panini * Caixa 50 saquetas - 75€": "https://www.paniniportugal.com/shp_prt_pt/fifa-world-cup-2026-official-sticker-collection-caixa-de-50-saquetas-cole-o-oficial-panini-005460box50ew-es01.html",
    "Panini * Caixa 8 saquetas - 12€": "https://www.paniniportugal.com/shp_prt_pt/fifa-world-cup-2026-official-sticker-blister-8-saquetas-cole-o-oficial-panini-005460kbe8w-es01.html",
    "Panini * TinBox 16 saquetas - 27€": "https://www.paniniportugal.com/shp_prt_pt/fifa-world-cup-2026-official-sticker-collection-tin-box-cole-o-oficial-panini-005460tinew-es01.html",
    "Panini * Caderneta": "https://www.paniniportugal.com/shp_prt_pt/fifa-world-cup-2026-official-sticker-collection-caderneta-cole-o-oficial-panini-005460aptw-es01.html",
    "Note * Caixa 8 saquetas - 12€": "https://noteonline.pt/products/ecoblister-world-cup-2026-8831667",
    "FNAC * Caixa 8 saquetas - 12€": "https://www.fnac.pt/Saqueta-de-Cromos-Panini-FIFA-World-Cup-2026-Ecoblister-com-8-Unidades-Escrita-e-Material-de-Papelaria-Outros-acessorios-de-escrita-e-material-de-papelaria/a14147237"
}

last_state = {}
history = {}

# Corrigir encoding
for stream_name in ("stdout", "stderr"):
    stream = getattr(sys, stream_name, None)
    if stream and hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


# -------- CHECK STOCK --------
def check_stock(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        raw_text = soup.get_text(separator=" ").lower()

        # ✂️ cortar texto após frase
        cut_phrase = "encontrámos outros produtos que podem ser do seu interesse!"
        text = raw_text.split(cut_phrase)[0]

        if "esgotado" in text:
            return False

        if "brevemente disponivel" in text:
            return False

        if "adicionar ao carrinho" in text:
            return True

        return False

    except Exception as e:
        print(f"[ERRO CHECK STOCK] {e}", flush=True)
        return False


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID

    CHAT_ID = update.effective_chat.id

    print(f"[START] Chat registado: {CHAT_ID}", flush=True)

    await update.message.reply_text("🤖 Monitorização iniciada!")

    context.job_queue.run_repeating(
        monitor,
        interval=60,
        first=10
    )


# -------- STATUS --------
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📦 Estado atual:\n\n"

    for name, url in PRODUCTS.items():
        available = check_stock(url)
        state = "🟢 Disponível" if available else "🔴 Esgotado"
        msg += f"{name}: {state}\n"

    await update.message.reply_text(msg)


# -------- HISTORY --------
async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not history:
        await update.message.reply_text("📊 Ainda sem histórico.")
        return

    msg = "📊 Histórico:\n\n"

    for name, logs in history.items():
        msg += f"{name}:\n"
        for entry in logs:
            msg += f"  - {entry}\n"
        msg += "\n"

    await update.message.reply_text(msg)


# -------- MONITOR --------
async def monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_state, history, CHAT_ID

    print("[MONITOR] A verificar...", flush=True)

    for name, url in PRODUCTS.items():
        available = check_stock(url)
        previous = last_state.get(name)

        print(f"[CHECK] {name} -> {available}", flush=True)

        if previous is None:
            last_state[name] = available
            continue

        # 🔥 mudança detectada
        if available != previous:

            print(f"[MUDANÇA] {name}", flush=True)

            now = datetime.now().strftime("%d/%m %H:%M")
            estado = "Disponível" if available else "Esgotado"

            if name not in history:
                history[name] = []

            history[name].append(f"{now} → {estado}")
            history[name] = history[name][-10:]

            if available:
                texto = f"🔥 DISPONÍVEL!\n{name}\n{url}"
            else:
                texto = f"❌ ESGOTADO!\n{name}\n{url}"

            if CHAT_ID:
                await context.bot.send_message(
                    chat_id=CHAT_ID,
                    text=texto
                )
            else:
                print("[ERRO] CHAT_ID não definido!", flush=True)

        last_state[name] = available


# -------- ERROR --------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"[ERRO] {context.error}", flush=True)


# -------- APP --------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("history", history_cmd))
app.add_error_handler(error_handler)

print("Bot a correr...", flush=True)
app.run_polling()