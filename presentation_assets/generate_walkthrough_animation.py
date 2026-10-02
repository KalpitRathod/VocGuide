import os
import sys
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    # Try standard Windows fonts
    font_paths = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

def create_base_hud(title, step_idx, step_label):
    W, H = 1280, 720
    im = Image.new("RGB", (W, H), (15, 23, 42)) # Slate 900
    draw = ImageDraw.Draw(im)

    # Top Navigation Bar HUD
    draw.rectangle([(0, 0), (W, 56)], fill=(10, 15, 30))
    draw.line([(0, 56), (W, 56)], fill=(30, 41, 59), width=2)

    font_logo = get_font(18, bold=True)
    font_title = get_font(14, bold=False)
    font_badge = get_font(12, bold=True)

    # Logo
    draw.ellipse([(20, 14), (46, 40)], fill=(249, 115, 22))
    draw.text((28, 17), "V", fill=(255, 255, 255), font=font_logo)
    draw.text((56, 17), "VocGuide", fill=(255, 255, 255), font=font_logo)
    draw.text((150, 19), "CAREER GUIDANCE | SIH 2026 PS-26241", fill=(148, 163, 184), font=font_title)

    # Step Badge on Right
    badge_text = f"Step {step_idx}/7: {step_label}"
    draw.rounded_rectangle([(W - 280, 12), (W - 20, 44)], radius=16, fill=(30, 58, 138), outline=(59, 130, 246))
    draw.text((W - 265, 17), badge_text, fill=(219, 234, 254), font=font_badge)

    # Bottom Progress Bar
    draw.rectangle([(0, H - 32), (W, H)], fill=(10, 15, 30))
    progress_w = int((step_idx / 7.0) * W)
    draw.rectangle([(0, H - 4), (progress_w, H)], fill=(249, 115, 22))
    draw.text((20, H - 24), "VocGuide Prototype Demo - Typed Text Dialogue & End-to-End Walkthrough", fill=(148, 163, 184), font=font_badge)

    return im

def draw_hud(im, step_idx, step_label):
    W, H = im.size
    draw = ImageDraw.Draw(im)
    # Top HUD
    draw.rectangle([(0, 0), (W, 52)], fill=(10, 15, 30))
    draw.line([(0, 52), (W, 52)], fill=(30, 41, 59), width=2)

    font_logo = get_font(18, bold=True)
    font_sub = get_font(13, bold=False)
    font_badge = get_font(12, bold=True)

    draw.ellipse([(18, 12), (40, 34)], fill=(249, 115, 22))
    draw.text((23, 13), "V", fill=(255, 255, 255), font=font_logo)
    draw.text((48, 14), "VocGuide", fill=(255, 255, 255), font=font_logo)
    draw.text((140, 17), "• SIH 2026 Prototype Walkthrough (Typed Text Demo)", fill=(148, 163, 184), font=font_sub)

    badge_text = f"Step {step_idx}/7: {step_label}"
    draw.rounded_rectangle([(W - 270, 10), (W - 16, 40)], radius=15, fill=(30, 58, 138), outline=(59, 130, 246))
    draw.text((W - 256, 15), badge_text, fill=(219, 234, 254), font=font_badge)

    # Bottom ticker
    draw.rectangle([(0, H - 30), (W, H)], fill=(10, 15, 30))
    progress_w = int((step_idx / 7.0) * W)
    draw.rectangle([(0, H - 4), (progress_w, H)], fill=(249, 115, 22))
    draw.text((20, H - 23), "All interactions are purely text-driven • Joint family counseling • Verified NSQF data", fill=(148, 163, 184), font=font_badge)

def make_scene_1():
    # Login scene
    im = Image.open("screencapture-localhost-5000-2026-10-02-02_23_22.png")
    # Crop to top 1280x720
    im = im.crop((0, 0, 1920, 1080)).resize((1280, 720), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im, "RGBA")

    # Dark overlay
    draw.rectangle([(0, 0), (1280, 720)], fill=(0, 0, 0, 160))

    # Modal dialog
    mx1, my1, mx2, my2 = 440, 180, 840, 540
    draw.rounded_rectangle([(mx1, my1), (mx2, my2)], radius=12, fill=(15, 23, 42, 250), outline=(59, 130, 246, 255), width=2)

    font_title = get_font(20, bold=True)
    font_body = get_font(14, bold=False)
    font_bold = get_font(14, bold=True)

    draw.text((mx1 + 30, my1 + 25), "Sign In to VocGuide", fill=(255, 255, 255), font=font_title)
    draw.text((mx1 + 30, my1 + 60), "Enter administrator or student credentials", fill=(148, 163, 184), font=font_body)

    # Username field
    draw.text((mx1 + 30, my1 + 100), "Username", fill=(203, 213, 225), font=font_bold)
    draw.rounded_rectangle([(mx1 + 30, my1 + 125), (mx2 - 30, my1 + 165)], radius=6, fill=(30, 41, 59), outline=(96, 165, 250), width=1)
    draw.text((mx1 + 42, my1 + 135), "admin|", fill=(255, 255, 255), font=font_body)

    # Password field
    draw.text((mx1 + 30, my1 + 185), "Password", fill=(203, 213, 225), font=font_bold)
    draw.rounded_rectangle([(mx1 + 30, my1 + 210), (mx2 - 30, my1 + 250)], radius=6, fill=(30, 41, 59), outline=(71, 85, 105), width=1)
    draw.text((mx1 + 42, my1 + 220), "••••••••", fill=(255, 255, 255), font=font_body)

    # Sign In Button
    draw.rounded_rectangle([(mx1 + 30, my1 + 280), (mx2 - 30, my1 + 325)], radius=8, fill=(234, 88, 12))
    draw.text((mx1 + 150, my1 + 292), "Sign In ->", fill=(255, 255, 255), font=font_bold)

    draw_hud(im, 1, "Sign In & Authentication")
    return im

def make_scene_2():
    # Home Portal
    im = Image.open("screencapture-localhost-5000-2026-10-02-02_23_22.png")
    im = im.crop((0, 0, 1920, 1080)).resize((1280, 720), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im, "RGBA")

    # Callout badge
    draw.rounded_rectangle([(40, 80), (450, 150)], radius=10, fill=(15, 23, 42, 230), outline=(249, 115, 22, 255), width=2)
    font_bold = get_font(15, bold=True)
    font_sub = get_font(13, bold=False)
    draw.text((55, 90), "✨ Joint Family Career Guidance Portal", fill=(249, 115, 22), font=font_bold)
    draw.text((55, 115), "Verified data addressing both student aspirations & parental hesitation", fill=(226, 232, 240), font=font_sub)

    draw_hud(im, 2, "Home & Citizen Family Services")
    return im

def make_scene_3():
    # Trades Explorer
    im = Image.open("screencapture-localhost-5000-2026-10-02-02_23_44.png")
    im = im.crop((0, 0, 1920, 1080)).resize((1280, 720), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im, "RGBA")

    # Highlight Electrician
    draw.rounded_rectangle([(30, 80), (480, 150)], radius=10, fill=(15, 23, 42, 230), outline=(59, 130, 246, 255), width=2)
    font_bold = get_font(15, bold=True)
    font_sub = get_font(13, bold=False)
    draw.text((45, 90), "🔍 Verified NSQF Trade Catalog", fill=(96, 165, 250), font=font_bold)
    draw.text((45, 115), "Filter by Sector: Electrical, Automotive, Healthcare, IT & Apparel", fill=(226, 232, 240), font=font_sub)

    draw_hud(im, 3, "Explore Verified Vocational Trades")
    return im

def make_scene_4():
    # Setup guidance form
    im = Image.open("screencapture-localhost-5000-2026-10-02-02_23_58.png")
    im = im.crop((0, 0, 1920, 1080)).resize((1280, 720), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im, "RGBA")

    # Highlight Setup Form on left
    draw.rounded_rectangle([(20, 80), (420, 150)], radius=10, fill=(15, 23, 42, 230), outline=(34, 197, 94, 255), width=2)
    font_bold = get_font(15, bold=True)
    font_sub = get_font(13, bold=False)
    draw.text((35, 90), "📝 Joint Session Profile Setup", fill=(74, 222, 128), font=font_bold)
    draw.text((35, 115), "Learner: Rahul Sharma | Trade: Electrician | Concern: Safety & Income", fill=(226, 232, 240), font=font_sub)

    draw_hud(im, 4, "Guidance Session Profile Setup")
    return im

def make_scene_5():
    # Typed Chat Conversation
    im = Image.open("screencapture-localhost-5000-2026-10-02-02_23_58.png")
    im = im.crop((0, 0, 1920, 1080)).resize((1280, 720), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im, "RGBA")

    # Focus on chat dialogue in center-right
    cx1, cy1, cx2, cy2 = 420, 160, 1240, 640
    draw.rounded_rectangle([(cx1, cy1), (cx2, cy2)], radius=12, fill=(15, 23, 42, 245), outline=(59, 130, 246), width=2)

    font_title = get_font(16, bold=True)
    font_bold = get_font(14, bold=True)
    font_text = get_font(13, bold=False)

    draw.text((cx1 + 25, cy1 + 20), "💬 Live Typed Conversation (Student & Parent Joint Chat)", fill=(255, 255, 255), font=font_title)

    # Sentiment Pill
    draw.rounded_rectangle([(cx2 - 220, cy1 + 18), (cx2 - 25, cy1 + 45)], radius=12, fill=(20, 83, 45), outline=(34, 197, 94))
    draw.text((cx2 - 205, cy1 + 24), "● Sentiment: Positive (88%)", fill=(187, 247, 208), font=get_font(11, bold=True))

    # User Query Message Bubble
    draw.rounded_rectangle([(cx1 + 200, cy1 + 65), (cx2 - 25, cy1 + 115)], radius=10, fill=(30, 58, 138))
    draw.text((cx1 + 215, cy1 + 75), "Parent Query (Typed):", fill=(147, 197, 253), font=font_bold)
    draw.text((cx1 + 215, cy1 + 92), "\"Is electrician work safe for my child, and what is the salary in 3-5 years?\"", fill=(255, 255, 255), font=font_text)

    # AI Response Bubble
    draw.rounded_rectangle([(cx1 + 25, cy1 + 130), (cx2 - 100, cy1 + 380)], radius=10, fill=(30, 41, 59), outline=(71, 85, 105))
    draw.text((cx1 + 40, cy1 + 145), "🤖 VocGuide AI Family Counsellor (Llama 3.1 + RAG Grounded):", fill=(249, 115, 22), font=font_bold)

    p_text = (
        "1. For Parents (Safety & Dignity):\n"
        "   - Modern certified ITIs enforce full factory PPE standards: insulated boots, high-voltage gloves, arc-flash helmets.\n"
        "   - Starting stipend: ₹12,000-₹15,000/month under NAPS.\n"
        "   - Experienced salary (3-5 yrs): ₹28,000 to ₹55,000/month with 87% verified placement rate.\n\n"
        "2. For Learner (Career Progression):\n"
        "   - NSQF Level 4 Electrician -> Senior Technician -> Electrical Supervisor -> Licensed Contractor.\n"
        "   - High self-employment potential: Rooftop solar & EV charging infrastructure."
    )
    draw.text((cx1 + 40, cy1 + 175), p_text, fill=(226, 232, 240), font=font_text)

    # Chat Input Box at bottom
    draw.rounded_rectangle([(cx1 + 25, cy1 + 400), (cx2 - 25, cy1 + 450)], radius=8, fill=(15, 23, 42), outline=(96, 165, 250), width=2)
    draw.text((cx1 + 40, cy1 + 415), "Type your question here... (e.g. scholarship eligibility, training duration)|", fill=(148, 163, 184), font=font_text)

    draw_hud(im, 5, "Typed Text Conversation & Grounded AI Guidance")
    return im

def make_scene_6():
    # Regional Hindi Localization
    im = Image.open("screencapture-localhost-5000-2026-10-02-02_23_58.png")
    im = im.crop((0, 0, 1920, 1080)).resize((1280, 720), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im, "RGBA")

    cx1, cy1, cx2, cy2 = 420, 160, 1240, 640
    draw.rounded_rectangle([(cx1, cy1), (cx2, cy2)], radius=12, fill=(15, 23, 42, 245), outline=(249, 115, 22), width=2)

    font_title = get_font(16, bold=True)
    font_bold = get_font(14, bold=True)
    font_text = get_font(13, bold=False)

    draw.text((cx1 + 25, cy1 + 20), "🌐 क्षेत्रीय भाषा समर्थन (Bilingual Hindi Translation via TranslateGemma)", fill=(255, 255, 255), font=font_title)

    # Active Language Indicator
    draw.rounded_rectangle([(cx2 - 180, cy1 + 18), (cx2 - 25, cy1 + 45)], radius=12, fill=(124, 45, 18), outline=(249, 115, 22))
    draw.text((cx2 - 165, cy1 + 24), "भाषा: हिन्दी (Active)", fill=(254, 215, 170), font=get_font(11, bold=True))

    # User Query Bubble
    draw.rounded_rectangle([(cx1 + 200, cy1 + 65), (cx2 - 25, cy1 + 115)], radius=10, fill=(30, 58, 138))
    draw.text((cx1 + 215, cy1 + 75), "अभिभावक का प्रश्न (Typed in Hindi):", fill=(147, 197, 253), font=font_bold)
    draw.text((cx1 + 215, cy1 + 92), "\"क्या सरकार इस कोर्स के लिए छात्रवृत्ति या वजीफा देती है?\"", fill=(255, 255, 255), font=font_text)

    # AI Response Bubble
    draw.rounded_rectangle([(cx1 + 25, cy1 + 130), (cx2 - 80, cy1 + 380)], radius=10, fill=(30, 41, 59), outline=(71, 85, 105))
    draw.text((cx1 + 40, cy1 + 145), "🤖 परामर्शदाता उत्तर (Devanagari Localized Response):", fill=(249, 115, 22), font=font_bold)

    hi_text = (
        "हाँ! भारत सरकार और कौशल विकास मंत्रालय (MSDE) के तहत कई योजनाएं उपलब्ध हैं:\n\n"
        "1. PMKVY 4.0: संपूर्ण पाठ्यक्रम शुल्क माफ और प्रमाणन के बाद वित्तीय सहायता।\n"
        "2. राष्ट्रीय शिक्षुता संवर्धन योजना (NAPS): ₹1,500 से ₹2,500 प्रतिमाह प्रत्यक्ष लाभ अंतरण (DBT)।\n"
        "3. राज्य आईटीआई छात्रवृत्ति: अनुसूचित जाति / जनजाति और ईडब्ल्यूएस परिवारों के लिए विशेष वित्तीय सहायता।\n\n"
        "इससे परिवार पर पढ़ाई का कोई आर्थिक बोझ नहीं पड़ता।"
    )
    draw.text((cx1 + 40, cy1 + 175), hi_text, fill=(226, 232, 240), font=font_text)

    draw_hud(im, 6, "Regional Language Localization (Hindi)")
    return im

def make_scene_7():
    # Admin Analytics
    im = Image.open("screencapture-localhost-5000-2026-10-02-02_24_37.png")
    im = im.crop((0, 0, 1920, 1080)).resize((1280, 720), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im, "RGBA")

    # Callout badge
    draw.rounded_rectangle([(30, 80), (520, 150)], radius=10, fill=(15, 23, 42, 230), outline=(249, 115, 22, 255), width=2)
    font_bold = get_font(15, bold=True)
    font_sub = get_font(13, bold=False)
    draw.text((45, 90), "📊 Real-Time Administration & Resistance Analytics", fill=(249, 115, 22), font=font_bold)
    draw.text((45, 115), "Track sentiment shifts, regional resistance topics & manage human escalations", fill=(226, 232, 240), font=font_sub)

    draw_hud(im, 7, "Scheme Administration & Telemetry")
    return im

def main():
    print("Generating prototype walkthrough video frames...")
    scenes = [
        (make_scene_1(), 3500), # 3.5s
        (make_scene_2(), 3500),
        (make_scene_3(), 3500),
        (make_scene_4(), 3500),
        (make_scene_5(), 5000), # 5.0s for chat
        (make_scene_6(), 4500), # 4.5s for hindi
        (make_scene_7(), 4000), # 4.0s for admin
    ]

    images = [s[0] for s in scenes]
    durations = [s[1] for s in scenes]

    out_path = "presentation_assets/prototype_walkthrough_demo.webp"
    images[0].save(
        out_path,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        quality=90
    )
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Created animated demo: {out_path} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
