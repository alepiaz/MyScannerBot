# -*- coding: UTF-8 -*-
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyMarkup,\
                    ForceReply, PhotoSize, Video
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters, BaseFilter

import os
from scanner import *
from sklearn.cluster import MiniBatchKMeans
import shutil
from fpdf import FPDF

def error_callback(bot, update, error):
    raise error
    print(str(error))

def check_file(update, context):
    try:
        message = update.message
        doc = message.document
        chat_id = message.chat_id
        message_id = message.message_id
        doc_file = doc.get_file()
        if doc.mime_type.split("/")[0] == "image":
            doc_path, doc_dir = get_path(chat_id, message_id)
            doc_file.download(doc_path)
            scan_image(context.bot, chat_id, message_id, doc_path, doc_dir)

        else:
            context.bot.send_message(chat_id = chat_id, text = "Invia una foto o un'immagine come file.")

    except Exception as e:
        print(str(e))

def check_photo(update, context):
    try:
        message = update.message
        photo = message.photo
        chat_id = message.chat_id
        message_id = message.message_id
        image_file = photo[-1].get_file()
        image_path, image_dir = get_path(chat_id, message_id)
        image_file.download(image_path)
        scan_image(context.bot, chat_id, message_id, image_path, image_dir)
        # cv2.imshow('FRAME', image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    except Exception as e:

        print(str(e))

def get_path(chat_id, message_id):
    image_dir = "data/"+str(chat_id)+"/"+str(message_id)
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    image_path = image_dir+"/input.jpg"
    return image_path, image_dir

def scan_image(bot, chat_id, message_id, image_path, image_dir):
    try:
        image = cv2.imread(image_path,1)
        output, warp = scanner(image)

        if output == []:
            shutil.rmtree(image_dir)
            bot.send_message(chat_id = chat_id, text = "Immagine non riconosciuta, riprovare.")
        else:
            for i,o in enumerate(output):
                cv2.imwrite(image_dir+"/output_"+str(i+1)+".png",o)
            if not os.path.exists(image_dir+"/warps"):
                os.makedirs(image_dir+"/warps")
            for i,w in enumerate(warp):
                cv2.imwrite(image_dir+"/warps/warp_"+str(i+1)+".png",w)
            n = len(os.listdir(image_dir))-2
            if n > 1:
                keyboard = [[InlineKeyboardButton("Successiva ▶️", callback_data = "next2")],
                            [InlineKeyboardButton("Ritaglia ✂️", callback_data = "crop1")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                caption = "Usa le frecce per scegliere come ritagliare il documento"
            else:
                keyboard = [[InlineKeyboardButton("Ritaglia ✂️", callback_data = "crop1")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                caption = None

            bot.send_photo(chat_id = chat_id, photo = open(image_dir+"/output_1.png","rb"), reply_markup = reply_markup, reply_to_message_id = message_id, caption = caption)
    except Exception as e:
        print("scanner")
        print(str(e))

def next_handler(update, context):
    print("here")
    query = update.callback_query
    data = query.data
    chat_id = query.from_user.id
    message_id = query.message.message_id
    reply_id = query.message.reply_to_message.message_id
    image_dir = "data/"+str(chat_id)+"/"+str(reply_id)
    caption = "Scorri le immagini con le frecce per scegliere come ritagliare il documento"
    # print(data)
    # print(data.find("next"))
    # print(data[-1])
    i = int(data.split("next")[1])
    n = len(os.listdir(image_dir))-2
    next = InlineKeyboardButton("Successiva ▶️", callback_data = "next"+str(i+1))
    prev = InlineKeyboardButton("◀️ Precedente", callback_data = "prev"+str(i-1))
    crop = InlineKeyboardButton("Ritaglia ✂️", callback_data = "crop"+str(i))
    if i == n:
        keyboard = [[prev],
                    [crop]]
    else:
        keyboard = [[prev,next],
                    [crop]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.answer()
    path = str(image_dir)+"/output_"+str(i)+".png"
    image = open(path,"rb")
    context.bot.edit_message_media(chat_id = chat_id, message_id = message_id, media = telegram.InputMediaPhoto(image))
    context.bot.edit_message_caption(chat_id = chat_id, message_id = message_id, caption = caption, reply_markup = reply_markup)


def prev_handler(update, context):
    query = update.callback_query
    data = query.data
    chat_id = query.from_user.id
    message_id = query.message.message_id
    reply_id = query.message.reply_to_message.message_id
    image_dir = "data/"+str(chat_id)+"/"+str(reply_id)
    caption = "Scorri le immagini con le frecce per scegliere come ritagliare il documento"
    i = int(data.split("prev")[1])

    n = len(os.listdir(image_dir))-2
    next = InlineKeyboardButton("Successiva ▶️", callback_data = "next"+str(i+1))
    prev = InlineKeyboardButton("◀️ Precedente", callback_data = "prev"+str(i-1))
    crop = InlineKeyboardButton("Ritaglia ✂️", callback_data = "crop"+str(i))
    if i == 1:
        keyboard = [[next],
                    [crop]]
    else:
        keyboard = [[prev,next],
                    [crop]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.answer()
    path = image_dir+"/output_"+str(i)+".png"
    image = open(path,"rb")
    context.bot.edit_message_media(chat_id = chat_id, message_id = message_id, media = telegram.InputMediaPhoto(image))
    context.bot.edit_message_caption(chat_id = chat_id, message_id = message_id, caption = caption, reply_markup = reply_markup)

def crop_handler(update, context):
    query = update.callback_query
    data = query.data
    chat_id = query.from_user.id
    message_id = query.message.message_id
    reply_id = query.message.reply_to_message.message_id
    image_dir = "data/"+str(chat_id)+"/"+str(reply_id)
    if data.find("crop") >= 0:
        i = int(data.split("crop")[1])
        path = str(image_dir)+"/warps/warp_"+str(i)+".png"
        i = cv2.imread(path,1)
        # image = open(path,"rb")
        cv2.imwrite(str(image_dir)+"/warp.png", i)

        adapt = InlineKeyboardButton("☑️ Adatta automaticamente", callback_data = "adapt")
        a4 = InlineKeyboardButton("↕️ Adatta in altezza", callback_data = "a4")
        card = InlineKeyboardButton("↔️ Adatta in larghezza", callback_data = "card")
        keyboard = [[adapt], [a4], [card]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        caption = "Scegli il formato da usare per il documento"
        query.answer()
        context.bot.edit_message_caption(chat_id = chat_id, message_id = message_id, caption = caption, reply_markup = reply_markup)

def adapt_handler(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    message_id = query.message.message_id
    reply_id = query.message.reply_to_message.message_id
    image_dir = "data/"+str(chat_id)+"/"+str(reply_id)
    path = str(image_dir)+"/warp.png"
    image = open(path,"rb")
    bw = InlineKeyboardButton("⚪️⚫️ Bianco e Nero", callback_data = "bw")
    grayk = InlineKeyboardButton("🔘 Scala di grigi", callback_data = "grayk")
    colork = InlineKeyboardButton("🎨 A colori", callback_data = "colork")
    orig = InlineKeyboardButton("🖼 Originale", callback_data = "orig")
    keyboard = [[bw], [grayk], [colork], [orig]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.answer()
    context.bot.edit_message_media(chat_id = chat_id, message_id = message_id, media = telegram.InputMediaPhoto(image), reply_markup = reply_markup)
    # bot.edit_message_caption(chat_id = chat_id, message_id = message_id, caption = None)

def height_handler(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    message_id = query.message.message_id
    reply_id = query.message.reply_to_message.message_id
    image_dir = "data/"+str(chat_id)+"/"+str(reply_id)
    
    path = str(image_dir)+"/warp.png"
    i = cv2.imread(path,1)
    w,h,_ = i.shape
    if h>=w:
        i = cv2.resize(i,(int(h*210/297),h),cv2.INTER_AREA)
    else:
        i = cv2.resize(i,(w,int(w*297/210)),cv2.INTER_AREA)
    cv2.imwrite(path,i)
    image = open(path,"rb")
    bw = InlineKeyboardButton("⚪️⚫️ Bianco e Nero", callback_data = "bw")
    grayk = InlineKeyboardButton("🔘 Scala di grigi", callback_data = "grayk")
    colork = InlineKeyboardButton("🎨 A colori", callback_data = "colork")
    orig = InlineKeyboardButton("🖼 Originale", callback_data = "orig")
    keyboard = [[bw], [grayk], [colork], [orig]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.answer()
    context.bot.edit_message_media(chat_id = chat_id, message_id = message_id, media = telegram.InputMediaPhoto(image), reply_markup = reply_markup)


def width_handler(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    message_id = query.message.message_id
    reply_id = query.message.reply_to_message.message_id
    image_dir = "data/"+str(chat_id)+"/"+str(reply_id)
    
    path = str(image_dir)+"/warp.png"
    i = cv2.imread(path,1)
    w,h,_ = i.shape
    if h>=w:
        i = cv2.resize(i,(int(h*8560/5398),h))
    else:
        i = cv2.resize(i,(w,int(w*5398/8560)))
    cv2.imwrite(path,i)
    image = open(path,"rb")
    bw = InlineKeyboardButton("⚪️⚫️ Bianco e Nero", callback_data = "bw")
    grayk = InlineKeyboardButton("🔘 Scala di grigi", callback_data = "grayk")
    colork = InlineKeyboardButton("🎨 A colori", callback_data = "colork")
    orig = InlineKeyboardButton("🖼 Originale", callback_data = "orig")
    keyboard = [[bw], [grayk], [colork], [orig]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.answer()
    context.bot.edit_message_media(chat_id = chat_id, message_id = message_id, media = telegram.InputMediaPhoto(image), reply_markup = reply_markup)

def bw_handler(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    message_id = query.message.message_id
    reply_id = query.message.reply_to_message.message_id
    image_dir = "data/"+str(chat_id)+"/"+str(reply_id)

    path = image_dir
    img = cv2.imread(path+"/warp.png",1)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)
    denoised = cv2.fastNlMeansDenoising(thresh, 11, 31, 9)
    cv2.imwrite(path+"/output.png", denoised)
    image = open(path+"/output.png", "rb")
    dl = InlineKeyboardButton("📥 Scarica", callback_data = "dl")
    back = InlineKeyboardButton("🔙", callback_data = "back")
    pdf = InlineKeyboardButton("📝 Aggiungi al PDF", callback_data = "pdf")
    keyboard = [[dl, pdf],
                [back]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.answer()
    context.bot.edit_message_media(chat_id = chat_id, message_id = message_id, media = telegram.InputMediaPhoto(image), reply_markup = reply_markup)

def orig_handler(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    message_id = query.message.message_id
    reply_id = query.message.reply_to_message.message_id
    image_dir = "data/"+str(chat_id)+"/"+str(reply_id)

    path = image_dir
    img = cv2.imread(path+"/warp.png",1)
    cv2.imwrite(path+"/output.png", img)
    image = open(path+"/output.png","rb")
    dl = InlineKeyboardButton("📥 Scarica", callback_data = "dl")
    back = InlineKeyboardButton("🔙", callback_data = "back")
    pdf = InlineKeyboardButton("📝 Aggiungi al PDF", callback_data = "pdf")
    keyboard = [[dl, pdf],
                [back]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.answer()
    context.bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = reply_markup)

def colork_handler(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    message_id = query.message.message_id
    reply_id = query.message.reply_to_message.message_id
    image_dir = "data/"+str(chat_id)+"/"+str(reply_id)

    path = image_dir
    img = cv2.imread(path+"/warp.png",1)
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    img = kimage(lab)
    cv2.imwrite(path+"/output.png", img)
    image = open(path+"/output.png","rb")
    dl = InlineKeyboardButton("📥 Scarica", callback_data = "dl")
    back = InlineKeyboardButton("🔙", callback_data = "back")
    pdf = InlineKeyboardButton("📝 Aggiungi al PDF", callback_data = "pdf")
    keyboard = [[dl, pdf],
                [back]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.answer()
    context.bot.edit_message_media(chat_id = chat_id, message_id = message_id, media = telegram.InputMediaPhoto(image), reply_markup = reply_markup)

def grayk_handler(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    message_id = query.message.message_id
    reply_id = query.message.reply_to_message.message_id
    image_dir = "data/"+str(chat_id)+"/"+str(reply_id)
    
    path = image_dir
    img = cv2.imread(path+"/warp.png",1)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    lab = cv2.cvtColor(cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB),cv2.COLOR_RGB2LAB)
    img = kimage(lab)
    cv2.imwrite(path+"/output.png", img)
    image = open(path+"/output.png","rb")
    dl = InlineKeyboardButton("📥 Scarica", callback_data = "dl")
    back = InlineKeyboardButton("🔙", callback_data = "back")
    pdf = InlineKeyboardButton("📝 Aggiungi al PDF", callback_data = "pdf")
    keyboard = [[dl, pdf],
                [back]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.answer()
    context.bot.edit_message_media(chat_id = chat_id, message_id = message_id, media = telegram.InputMediaPhoto(image), reply_markup = reply_markup)

def pdf_handler(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    message_id = query.message.message_id
    reply_id = query.message.reply_to_message.message_id
    image_dir = "data/"+str(chat_id)+"/"+str(reply_id)

    path = image_dir+"/output.png"
    pathpdf = "data/"+str(chat_id)+"/pdf"
    if not os.path.exists(pathpdf):
        os.makedirs(pathpdf)
    img = cv2.imread(path,1)
    n = len(os.listdir(pathpdf))+1
    cv2.imwrite(pathpdf+"/"+str(n)+".png",img)
    shutil.rmtree(image_dir)
    query.answer()
    context.bot.delete_message(chat_id = chat_id, message_id = message_id)
    context.bot.send_message(chat_id = chat_id, text = "Immagine aggiunta al PDF")

def back_handler(update, context):
    try:
        query = update.callback_query
        chat_id = query.from_user.id
        message_id = query.message.message_id
        reply_id = query.message.reply_to_message.message_id
        image_dir = "data/"+str(chat_id)+"/"+str(reply_id)

        path = image_dir
        image = open(path+"/warp.png","rb")
        bw = InlineKeyboardButton("⚪️⚫️ Bianco e Nero", callback_data = "bw")
        grayk = InlineKeyboardButton("🔘 Scala di grigi", callback_data = "grayk")
        colork = InlineKeyboardButton("🎨 A colori", callback_data = "colork")
        orig = InlineKeyboardButton("🖼 Originale", callback_data = "orig")
        keyboard = [[bw], [grayk], [colork], [orig]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.answer()
        context.bot.edit_message_media(chat_id = chat_id, message_id = message_id, media = telegram.InputMediaPhoto(image), reply_markup = reply_markup)
    except Exception as e:
        print(str(e))

def dl_handler(update, context):
    try:
        query = update.callback_query
        chat_id = query.from_user.id
        message_id = query.message.message_id
        reply_id = query.message.reply_to_message.message_id
        image_dir = "data/"+str(chat_id)+"/"+str(reply_id)
        path = image_dir+"/output.png"
        context.bot.delete_message(chat_id = chat_id, message_id = message_id)
        context.bot.send_message(chat_id = chat_id, text = "Ecco la tua immagine:")
        context.bot.send_document(chat_id = chat_id, document = open(path,"rb"))
    except Exception as e:
        print(str(e))

def kimage(image):
    (h, w) = image.shape[:2]
    image = image.reshape((image.shape[0] * image.shape[1], 3))
    clt = MiniBatchKMeans(n_clusters = 16)
    labels = clt.fit_predict(image)
    quant = clt.cluster_centers_.astype("uint8")[labels]
    quant = quant.reshape((h, w, 3))
    image = image.reshape((h, w, 3))
    quant = cv2.cvtColor(quant, cv2.COLOR_LAB2RGB)
    # image = cv2.cvtColor(image, cv2.COLOR_LAB2RGB)
    return quant

def helpcmd(update,context):
    chat_id = update.message.from_user.id

    text = """Questo Bot permette di creare un PDF dalle immagini che vengono inviate.

È molto semplice:
• Invia un'immagine come foto o documento;
• Seleziona il ritaglio che preferisci;
• Scegli il filtro da applicare;
• Ripeti finchè non sei soddisfatto;
• Quando hai finito scarica il PDF con il comando /download o scartalo e ricomincia con il comando /delete;

Ogni volta che avrai bisogno di aiuto usa il comando /help per mostrare nuovamente questo messaggio."""

    context.bot.send_message(chat_id = chat_id, text = text)

def downloadcmd(update, context):
    try:
        chat_id = update.message.from_user.id

        pdf = FPDF()
        pdf_size = {'w': 210, 'h': 297}
        path = "data/"+str(chat_id)+"/pdf/"
        images = os.listdir(path)
        images.sort()
        for i in images:
            pdf.add_page()
            img = cv2.imread(path+i,1)
            (height, width) = img.shape[:2]
            width = width*0.264583
            height = height*0.264583

            height = 210*height/width


            pdf.image(path+i,5,149-(height-10)/2,200,height-10)

        filepath = "data/"+str(chat_id)+"/output.pdf"
        pdf.output(filepath, "F")
        file = open(filepath, "rb")
        context.bot.send_document(chat_id = chat_id, document = file, caption = "Ecco il tuo pdf.")
        shutil.rmtree(path)
        if os.path.exists(filepath):
            os.remove(filepath)

    except Exception as e:
        print(str(e))

def deletecmd(update, context):
    chat_id = update.message.from_user.id
    path = "data/"+str(chat_id)+"/pdf/"
    shutil.rmtree(path)
    context.bot.send_message(chat_id = chat_id, text = "Pdf eliminato. Invia un'altra immagine per crearne uno nuovo.")
