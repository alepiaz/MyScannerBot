# -*- coding: utf-8 -*-

from functions import *
TOKEN = "827961133:AAE66epsHDf8Yr3xeofp3KRyvP8qiigrrqk"
bot = telegram.Bot(TOKEN)


def main():
    updater = Updater(TOKEN, request_kwargs={'read_timeout': 20, 'connect_timeout': 20})
    dp = updater.dispatcher
    j = updater.job_queue
    dp.add_handler(CommandHandler('start', helpcmd))
    dp.add_handler(CommandHandler('help', helpcmd))
    dp.add_handler(CommandHandler('download', downloadcmd))
    dp.add_handler(CommandHandler('delete', deletecmd))
    dp.add_handler(MessageHandler(Filters.photo, check_photo))
    dp.add_handler(MessageHandler(Filters.document, check_file ))

    dp.add_handler(CallbackQueryHandler(next_handler, pattern='next[0-9].*'))
    dp.add_handler(CallbackQueryHandler(prev_handler, pattern='prev[0-9].*'))
    dp.add_handler(CallbackQueryHandler(crop_handler, pattern='crop[0-9].*'))
    dp.add_handler(CallbackQueryHandler(adapt_handler, pattern='adapt.*'))
    dp.add_handler(CallbackQueryHandler(height_handler, pattern='a4.*'))
    dp.add_handler(CallbackQueryHandler(width_handler, pattern='card.*'))
    dp.add_handler(CallbackQueryHandler(bw_handler, pattern='bw.*'))
    dp.add_handler(CallbackQueryHandler(orig_handler, pattern='orig.*'))
    dp.add_handler(CallbackQueryHandler(colork_handler, pattern='colork.*'))
    dp.add_handler(CallbackQueryHandler(grayk_handler, pattern='grayk.*'))
    dp.add_handler(CallbackQueryHandler(pdf_handler, pattern='pdf.*'))
    dp.add_handler(CallbackQueryHandler(dl_handler, pattern='dl.*'))
    dp.add_handler(CallbackQueryHandler(back_handler, pattern='back.*'))
    dp.add_error_handler(error_callback)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
