python
import os
import re
import nextcord
from nextcord.ext import commands
import aiohttp

# ตั้งค่า Intents
intents = nextcord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='/', intents=intents)

# กำหนดค่าตัวแปร (แนะนำให้ดึงจาก Environment Variables เพื่อความปลอดภัย)
TOKEN = os.getenv("DISCORD_TOKEN", "MTM0NDk5Mzk4_YOUR_TOKEN_HERE")
PHONE_NUMBER = "08xxxxxxxx"  # เบอร์สำหรับรับซองอั่งเปา
API_URL = "http://51.75.118.171:20210/apisnyxai"

@client.event
async def on_ready():
    print(f'Logged in successfully as: {client.user}')
    await client.change_presence(
        activity=nextcord.Streaming(
            name="ระบบโดเนท 24 ชม.",
            url="https://www.twitch.tv/monstercat"
        )
    )

# Modal สำหรับกรอกซองอั่งเปา TrueMoney
class TopupModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(title="💸 ระบบเติมเงิน / โดเนทอั่งเปา")
        
        self.topup_link = nextcord.ui.TextInput(
            label="ลิงก์ซองอั่งเปา TrueMoney",
            placeholder="https://gift.truemoney.com/campaign/?v=...",
            required=True,
            style=nextcord.TextInputStyle.short
        )
        self.add_item(self.topup_link)

    async def callback(self, interaction: nextcord.Interaction):
        link = self.topup_link.value.strip()
        
        # ตรวจสอบรูปแบบลิงก์อั่งเปา
        if not re.match(r"^https:\/\/gift\.truemoney\.com\/campaign\/\?v=[a-zA-Z0-9]{18}$", link):
            await interaction.response.send_message(
                "❌ รูปแบบลิงก์อั่งเปาไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง", 
                ephemeral=True
            )
            return

        voucher_code = link.split("?v=")[1]

        await interaction.response.defer(ephemeral=True)

        try:
            async with aiohttp.ClientSession() as session:
                # ยิงไปที่ API TrueMoney หรือ API หลังบ้าน
                payload = {
                    "mobile": PHONE_NUMBER,
                    "voucher_hash": voucher_code
                }
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0"
                }
                
                async with session.post(f"https://gift.truemoney.com/campaign/vouchers/{voucher_code}/redeem", json=payload, headers=headers) as response:
                    data = await response.json()

                    if response.status == 200 and data.get("status", {}).get("code") == "SUCCESS":
                        amount = float(data["data"]["my_ticket"]["amount_baht"])
                        
                        embed = nextcord.Embed(
                            title="✅ เติมเงินสำเร็จ",
                            description=f"ได้รับยอดเงินจำนวน **{amount:,.2f} บาท** เรียบร้อย!",
                            color=nextcord.Color.green()
                        )
                        embed.set_footer(text="ขอบคุณที่สนับสนุนพวกเราครับ 🙏")
                        
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        
                        # (Optional) ส่งข้อมูลไปบันทึกที่ API ของเรา
                        async with session.post(f"{API_URL}/log-donation", json={"user_id": str(interaction.user.id), "amount": amount}):
                            pass
                    else:
                        error_msg = data.get("status", {}).get("message", "ซองนี้อาจถูกใช้งานไปแล้ว หรือหมดอายุ")
                        await interaction.followup.send(f"❌ เติมเงินไม่สำเร็จ: {error_msg}", ephemeral=True)

        except Exception as e:
            print(f"Error handling voucher: {e}")
            await interaction.followup.send("⚠️ เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง", ephemeral=True)

# View สำหรับปุ่มกดโดเนท
class DonateView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(
        label="สนับสนุนเซิร์ฟเวอร์", 
        style=nextcord.ButtonStyle.green, 
        emoji="🎁", 
        custom_id="donate_button_persistent"
    )
    async def donate_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(TopupModal())

# Slash Command สำหรับเรียกหน้าต่างโดเนท
@client.slash_command(description="เปิดใช้งานแผงระบบโดเนทสำหรับสมาชิก")
async def donate(interaction: nextcord.Interaction):
    embed = nextcord.Embed(
        title="🌟 ระบบโดเนทสนับสนุนเซิร์ฟเวอร์",
        description="> สนับสนุนพวกเราได้ง่ายๆ ตลอด 24 ชั่วโมง\n> คลิกปุ่มด้านล่างเพื่อกรอกลิงก์ซองอั่งเปา TrueMoney ไม่มีขั้นต่ำ!",
        color=nextcord.EmbedColor.from_rgb(136, 0, 255)
    )
    embed.set_image(url="https://i.pinimg.com/originals/54/ad/ed/54aded2832204ae26b6c57ddf7ad4854.gif")
    embed.set_footer(text="ระบบอัตโนมัติรวดเร็วทันใจ 24 ชม.")

    await interaction.send(embed=embed, view=DonateView())

# รันบอท
client.run(TOKEN)