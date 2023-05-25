import threading
import app
import bot


def main():
    # Create a thread for the Flask app
    flask_thread = threading.Thread(target=app.app.run)

    # Start the Flask app thread
    flask_thread.start()

    # Start the Telegram bot
    bot.start_bot()


if __name__ == '__main__':
    main()
