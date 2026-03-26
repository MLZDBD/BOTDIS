import discord
from discord.ext import commands
import os
import asyncio

# --- إعدادات البوت (السويدة - النسخة الاحترافية v12.1 - Railway Edition) ---
# ملاحظة: سيقوم البوت بقراءة التوكن من إعدادات الاستضافة (Variables) أو من الكود مباشرة
TOKEN = os.getenv('DISCORD_TOKEN') or 'MTQ4NjU0MzcwNDM2MDYyMDIwNA.GPoWw5.a3TUQH2MtS_Rq28SamDvRgvHBQntLfTbBiUWw0'
OWNER_ID = 802934285006143508
LOG_CHANNEL_ID = 1482212827681787934
PREFIX = '!'

# تثبيت المكتبات المطلوبة: pip install py-cord[voice] PyNaCl

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# تخزين معلومات التسجيل النشطة
active_recordings = {}

@bot.event
async def on_ready():
    print(f'--- [ السويدة أونلاين v12.1 - Railway ] ---')
    print(f'تم تسجيل الدخول كـ: {bot.user.name}')
    print(f'آيدي البوت: {bot.user.id}')
    print(f'قناة السجلات: {LOG_CHANNEL_ID}')
    print(f'---------------------------------------')

# --- وظيفة معالجة التسجيل بعد الانتهاء ---
async def finished_callback(sink, channel: discord.TextChannel, *args):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        log_channel = channel

    files = []
    recorded_mentions = ""

    for user_id, audio in sink.recorded_users.items():
        file_path = f"voice_{user_id}.mp3"
        with open(file_path, "wb") as f:
            f.write(audio.file.read())
        files.append(discord.File(file_path, filename=f"swaida_{user_id}.mp3"))
        recorded_mentions += f"<@{user_id}> "

    embed = discord.Embed(
        title="🕵️‍♂️ تقرير السويدة - تم حفظ التسجيل",
        description=f"🎙️ الأشخاص الذين تم تسجيلهم: {recorded_mentions if recorded_mentions else 'لا يوجد (ربما لم يتحدثوا)'}",
        color=discord.Color.dark_red()
    )
    
    try:
        await log_channel.send(embed=embed, files=files)
    except Exception as e:
        print(f"خطأ في إرسال اللوقات: {e}")
    
    # تنظيف الملفات المؤقتة فوراً لتوفير مساحة الاستضافة
    for f in files:
        try: os.remove(f.filename)
        except: pass

# --- الأوامر ---

@bot.command()
async def تعال(ctx):
    """أمر دخول البوت وبدء التسجيل تلقائياً"""
    if ctx.author.id != OWNER_ID: return
    
    if not ctx.author.voice:
        return await ctx.send("يجب أن تكون في روم صوتي أولاً! ❌")
    
    channel = ctx.author.voice.channel
    
    # التحقق إذا كان البوت يسجل بالفعل في هذا السيرفر
    if ctx.guild.id in active_recordings:
        return await ctx.send("البوت يسجل بالفعل في هذا السيرفر! ⚠️")

    try:
        # 1. الاتصال بالروم
        if ctx.voice_client:
            vc = ctx.voice_client
            await vc.move_to(channel)
        else:
            vc = await channel.connect()
        
        # 2. الانتظار حتى استقرار الاتصال (مهم جداً في Railway)
        for i in range(10): # محاولة لمدة 10 ثوانٍ
            if vc.is_connected():
                break
            await asyncio.sleep(1)
        
        if not vc.is_connected():
            return await ctx.send("فشل الاتصال بالروم الصوتي (تأخرت الاستجابة). يرجى المحاولة مرة أخرى. ❌")

        # 3. بدء التسجيل تلقائياً
        sink = discord.sinks.MP3Sink()
        
        try:
            vc.start_recording(sink, finished_callback, ctx.channel)
            active_recordings[ctx.guild.id] = vc
            await ctx.send(f"🔴 دخلت {channel.name} وبدأت التسجيل تلقائياً.. 🕵️‍♂️")
            print(f"بدأ التسجيل التلقائي في: {channel.name}")
        except Exception as e:
            # محاولة ثانية في حال فشل الأولى
            await asyncio.sleep(2)
            vc.start_recording(sink, finished_callback, ctx.channel)
            active_recordings[ctx.guild.id] = vc
            await ctx.send(f"🔴 دخلت {channel.name} وبدأت التسجيل (بعد محاولة ثانية).. 🕵️‍♂️")
        
    except Exception as e:
        await ctx.send(f"حدث خطأ أثناء محاولة الدخول أو التسجيل: {e}")
        print(f"خطأ: {e}")

@bot.command()
async def وقف(ctx):
    """إيقاف التسجيل والحفظ والخروج"""
    if ctx.author.id != OWNER_ID: return
    
    vc = ctx.voice_client
    if vc and vc.recording:
        try:
            vc.stop_recording()
            await asyncio.sleep(1.5) # انتظار بسيط لضمان انتهاء الحفظ
            await vc.disconnect()
            if ctx.guild.id in active_recordings:
                del active_recordings[ctx.guild.id]
            await ctx.send("⌛ تم إيقاف التسجيل وجاري الحفظ والإرسال.. 💾")
        except Exception as e:
            await ctx.send(f"خطأ في إيقاف التسجيل: {e}")
    else:
        await ctx.send("لا يوجد تسجيل جاري حالياً! 🤡")

@bot.event
async def on_voice_state_update(member, before, after):
    # نظام الهروب الذكي: إذا طُرد البوت أو خرج فجأة
    if member.id == bot.user.id:
        if before.channel and not after.channel:
            guild_id = before.channel.guild.id
            if guild_id in active_recordings:
                vc = active_recordings[guild_id]
                try:
                    vc.stop_recording()
                except:
                    pass
                del active_recordings[guild_id]
                print(f"تم رصد خروج البوت.. تم حفظ التسجيل اضطرارياً.")

bot.run(TOKEN)
