import os,json,logging
from datetime import datetime
from anthropic import Anthropic
from duckduckgo_search import DDGS
from telegram import Update,ReplyKeyboardMarkup,KeyboardButton
from telegram.ext import ApplicationBuilder,CommandHandler,MessageHandler,ContextTypes,filters

def get_env(key): 
    return os.environ.get(key)
    
TELEGRAM_TOKEN=get_env("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY=get_env("ANTHROPIC_API_KEY")
YOUR_CHAT_ID=int(get_env("YOUR_CHAT_ID"))
client=Anthropic(api_key=ANTHROPIC_API_KEY)

def auth(u):
    return u.effective_chat.id==YOUR_CHAT_ID

def claude(msg):
    try:
        r=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=500,messages=[{"role":"user","content":msg}])
        return r.content[0].text
    except Exception as e:
        return str(e)

def get_goals():
    if os.path.exists("goals.json"):
        return json.load(open("goals.json"))
    return {"goals":[],"checkins":[]}

def save_goals(d):
    json.dump(d,open("goals.json","w"))

async def start(u,c):
    if not auth(u):return
    await u.message.reply_text("AXIOM online! Your accountability partner is ready.\nCommands: /addgoal /goals /checkin /progress /search /ask")

async def addgoal(u,c):
    if not auth(u):return
    t=" ".join(c.args)
    if not t:
        await u.message.reply_text("Example: /addgoal Wake up at 6am")
        return
    d=get_goals()
    d["goals"].append({"id":len(d["goals"])+1,"text":t,"active":True})
    save_goals(d)
    await u.message.reply_text("Goal saved: "+t)

async def showgoals(u,c):
    if not auth(u):return
    d=get_goals()
    g=[x for x in d["goals"] if x.get("active")]
    if not g:
        await u.message.reply_text("No goals yet. Use /addgoal")
        return
    await u.message.reply_text("Your Goals:\n"+"\n".join(["#"+str(x["id"])+" "+x["text"] for x in g]))

async def checkin(u,c):
    if not auth(u):return
    d=get_goals()
    g=[x["text"] for x in d["goals"] if x.get("active")]
    d["checkins"].append({"date":datetime.now().isoformat()})
    save_goals(d)
    await u.message.reply_text(claude("Give short accountability feedback for these goals: "+str(g)))

async def progress(u,c):
    if not auth(u):return
    d=get_goals()
    await u.message.reply_text(claude("Short progress report for goals:"+str(d["goals"])+" checkins:"+str(len(d["checkins"]))))

async def dosearch(u,c):
    if not auth(u):return
    q=" ".join(c.args)
    if not q:
        await u.message.reply_text("Example: /search latest news")
        return
    try:
        with DDGS() as dd:
            results="\n".join([x["title"]+": "+x["body"] for x in dd.text(q,max_results=3)])
        await u.message.reply_text(claude("Summarize in bullets: "+results))
    except Exception as e:
        await u.message.reply_text(str(e))

async def ask(u,c):
    if not auth(u):return
    q=" ".join(c.args)
    if not q:
        await u.message.reply_text("Example: /ask how to focus")
        return
    await u.message.reply_text(claude(q))

async def msg(u,c):
    if not auth(u):return
    await u.message.reply_text(claude(u.message.text))

def main():
    print("AXIOM booting up...")
    app=ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("addgoal",addgoal))
    app.add_handler(CommandHandler("goals",showgoals))
    app.add_handler(CommandHandler("checkin",checkin))
    app.add_handler(CommandHandler("progress",progress))
    app.add_handler(CommandHandler("search",dosearch))
    app.add_handler(CommandHandler("ask",ask))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,msg))
    print("AXIOM is live!")
    app.run_polling()

if __name__=="__main__":
    main()
