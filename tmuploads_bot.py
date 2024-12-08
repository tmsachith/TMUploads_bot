import requests
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os

TOKEN = 'telegram token'

CHUNK_SIZE = 1024  # Define chunk size for download (1 KB)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hi! Send me a URL of a file, and I will upload it here.')

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    file_name = url.split('/')[-1]
    progress_message: Message = await update.message.reply_text(f'Starting download of {file_name}...')

    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))

        if response.status_code == 200:
            bytes_downloaded = 0
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)

                        # Calculate the current progress
                        percentage = (bytes_downloaded / total_size) * 100
                        downloaded_mb = bytes_downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        await progress_message.edit_text(
                            f'Download progress: {percentage:.2f}%\n'
                            f'Downloaded: {downloaded_mb:.2f} MB / {total_mb:.2f} MB'
                        )

            # Now upload to Telegram
            await progress_message.edit_text('Uploading file...')
            with open(file_name, 'rb') as f:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=f)
            
            await update.message.reply_text('File has been uploaded successfully!')
            os.remove(file_name)  # Clean up the file after upload

        else:
            await progress_message.edit_text('Failed to download the file. Please check the URL.')

    except requests.exceptions.RequestException as e:
        await progress_message.edit_text(f'An error occurred: {e}')

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    # Use the appropriate running method for most Python environments
    application.run_polling()

if __name__ == '__main__':
    main()