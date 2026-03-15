import asyncio

async def hacker_animation(update):

    try:
        await update.message.reply_animation(
            animation=open("hacker_animation_v15_final_ultimate.mp4","rb")
        )

        await asyncio.sleep(8)

    except Exception as e:
        print(e)
