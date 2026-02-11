import matplotlib
matplotlib.use("Agg")

import os
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, white, grey, whitesmoke
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


# =============================================
# THEME & CONFIGURATION
# =============================================
PRIMARY = HexColor("#0B5ED7")
LIGHT_BG = HexColor("#EDF2FC")
CARD_BG = HexColor("#F7F9FD")
TEXT_GRAY = HexColor("#5A5A5A")

VIOLATION_TYPES = [
    "stagnant_water", "water_logging_at_toe_OB_dump", "vehicle_red_flag_absent",
    "vehicle_red_flag_present", "overhanging_loose_boulders", "cracks",
    "unsafe_movement_person_on_haul_road", "unsafe_movement_lmv_near_shovel_dumper_dozer_drill",
    "rest_shelter", "lighting_arrangement", "blocked_drain", "water_sprinkling_arrangement",
    "fire", "smoke", "person_near_edge_unsafe_area", "unsafe_movement_person_near_dumper_dozer_shovel_drill",
    "scrap_management_required", "exit_boom_barrier_open", "lmv_tipper_plying_on_same_road",
    "vehicle_crowding", "person_unsafe", "overcrowding_person", "illegal_mining_pit", "broken_fence"
]

class FinalDroneReport:
    def __init__(self, filename, site_meta):
        self.c = canvas.Canvas(filename, pagesize=A4)
        self.w, self.h = A4
        self.site_name = str(site_meta.get('location', 'Site')).replace("_", " ")
        self.report_date = site_meta.get('date', '2026-02-09')
        self.drone_id = site_meta.get('drone_id', 'DRONE-X')
        self.cache_dir = "image_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def round_box(self, x, y, w, h, r=14, fill=CARD_BG):
        self.c.setFillColor(fill)
        self.c.roundRect(x, y, w, h, r, stroke=0, fill=1)
    def draw_fixed_header(self, page_title):
        top_margin = 25
        header_height = 110

        header_y = self.h - header_height - top_margin

        # Header Background
        self.round_box(25, header_y, self.w - 50, header_height, r=20, fill=LIGHT_BG)

        # Main Title
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(PRIMARY)
        self.c.drawString(50, header_y + 70, "Central Coalfields Limited (CCL)")

        # Subtitle
        self.c.setFont("Helvetica-Bold", 13)
        self.c.setFillColor(TEXT_GRAY)
        self.c.drawString(50, header_y + 45, page_title.upper())

        # Meta Info
        self.c.setFont("Helvetica", 9)
        self.c.drawString(
            50,
            header_y + 25,
            f"Location: {self.site_name} | Drone: {self.drone_id} | Date: {self.report_date}"
        )

        return header_y   # 🔥 return bottom of header

    def footer(self, pageno):
        self.c.setStrokeColor(LIGHT_BG)
        self.c.line(40, 40, self.w - 40, 40)
        self.c.setFont("Helvetica", 8)
        self.c.setFillColor(TEXT_GRAY)
        self.c.drawCentredString(self.w/2, 25, f"AI Surveillance Report - Aerovania Pvt. Ltd. | Page {pageno}")

    # =============================================
    # PAGE 1: COVER PAGE
    # =============================================
    # =============================================
    # PAGE 1: COVER PAGE (PROPER STRUCTURED LAYOUT)
    # =============================================
    def build_cover_page(self, df, video_link=None):

        # Draw Header


        total_v = len(df)
        top_v = df['type'].mode()[0].replace("_", " ").title() if not df.empty else "N/A"

        # =====================================================
        # SAFE START POSITION (BASED ON HEADER)
        # =====================================================
        header_bottom = self.draw_fixed_header("Executive Safety Summary")

        current_y = header_bottom - 111  # safe spacing below header


        # =====================================================
        # 1️⃣ SUMMARY CARDS (2 × 3 GRID)
        # =====================================================
        cards = [
            ("Reporting Site", self.site_name),
            ("Deployment Date", self.report_date),
            ("UAV Hardware ID", self.drone_id),
            ("Total Violations", total_v),
            ("Primary Risk Factor", top_v),
            ("Status", "Review Required")
        ]

        box_width = 160
        box_height = 70
        gap_x = 25
        gap_y = 35
        start_x = 50

        grid_top = current_y
        index = 0

        for row in range(2):
            for col in range(3):
                if index >= len(cards):
                    break

                x = start_x + col * (box_width + gap_x)
                y = grid_top - row * (box_height + gap_y)

                self.round_box(x, y, box_width, box_height, r=14)

                # Label
                self.c.setFont("Helvetica", 9)
                self.c.setFillColor(TEXT_GRAY)
                self.c.drawString(x + 12, y + 48, cards[index][0])

                # Value
                self.c.setFont("Helvetica-Bold", 11)
                self.c.setFillColor(black)
                self.c.drawString(x + 12, y + 25, str(cards[index][1]))

                index += 1

        # Move below grid
        grid_bottom = grid_top - (2 * box_height + gap_y)
        current_y = grid_bottom - 50

        # =====================================================
        # 2️⃣ SUBMISSION SECTION
        # =====================================================
        self.c.setFont("Helvetica-Bold", 14)
        self.c.setFillColor(PRIMARY)
        self.c.drawString(50, current_y, "Submission Details")

        submission_box_height = 65
        submission_box_y = current_y - 25 - submission_box_height

        self.round_box(50, submission_box_y, self.w - 100, submission_box_height, r=16)

        self.c.setFont("Helvetica", 11)
        self.c.setFillColor(black)
        self.c.drawString(70, submission_box_y + 40,
                          "Submitted By: Aerovania Pvt. Ltd.")
        self.c.drawString(70, submission_box_y + 20,
                          "Submitted To: CCL Safety Division")

        current_y = submission_box_y - 60

        # =====================================================
        # 3️⃣ VIDEO SECTION
        # =====================================================
        self.c.setFont("Helvetica-Bold", 14)
        self.c.setFillColor(PRIMARY)
        self.c.drawString(50, current_y, "Video Evidence")

        video_box_height = 55
        video_box_y = current_y - 25 - video_box_height

        self.round_box(50, video_box_y, self.w - 100, video_box_height, r=16)

        self.c.setFont("Helvetica", 10)
        self.c.setFillColor(TEXT_GRAY)

        if video_link:
            self.c.drawString(70, video_box_y + 22, video_link)

            # clickable link area
            self.c.linkURL(
                video_link,
                (70, video_box_y + 10, self.w - 50, video_box_y + 40),
                relative=0
            )
        else:
            self.c.drawString(70, video_box_y + 22, "No video link provided")

        # Footer
        self.footer(1)
        self.c.showPage()


    # =============================================
    # PAGE 2: ANALYTICS & DISTRIBUTION
    # =============================================
    def build_analytics_page(self, df):
        self.draw_fixed_header("Violation Analytics Overview")

        # Chart Generation
        counts = df['type'].value_counts()
        plt.figure(figsize=(7, 4), facecolor='#F7F9FD')
        ax = plt.gca()
        ax.set_facecolor('#F7F9FD')
        counts.plot(kind='bar', color='#0B5ED7', alpha=0.8)
        plt.title("Violation Frequency by Category", fontsize=12, fontweight='bold')
        plt.xticks(rotation=30, ha='right', fontsize=8)
        plt.tight_layout()

        chart_path = os.path.join(self.cache_dir, "analytics_chart.png")
        plt.savefig(chart_path, dpi=200)
        plt.close()

        # Draw Chart
        self.c.drawImage(chart_path, 50, self.h - 380, width=500, height=240)

        # Summary Table
        table_data = [["Violation Category", "Count", "Risk Level"]]
        for cat, val in counts.items():
            risk = "CRITICAL" if val > 3 else "High"
            table_data.append([cat.replace("_", " ").title(), str(val), risk])

        t = Table(table_data, colWidths=[280, 80, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), PRIMARY),
            ('TEXTCOLOR', (0,0), (-1,0), white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [whitesmoke, white])
        ]))

        t.wrapOn(self.c, self.w, self.h)
        t.drawOn(self.c, 65, self.h - 650)

        self.footer(2)
        self.c.showPage()

    # =============================================
    # PAGE 3+: CATEGORY-WISE EVIDENCE
    # =============================================
    def build_evidence_log(self, df):
        page_count = 3

        for category in VIOLATION_TYPES:
            cat_df = df[df['type'] == category]
            if cat_df.empty: continue

            # Start Category Section
            self.draw_fixed_header(f"Evidence: {category.replace('_',' ').title()}")

            # Y-cursor starts safely below the header
            y_cursor = self.h - 300
            x_pos = [50, 315]

            for i, (_, row) in enumerate(cat_df.iterrows()):
                col = i % 2
                if i > 0 and col == 0:
                    y_cursor -= 240 # Space for next row

                # Check for page overflow
                if y_cursor < 120:
                    self.footer(page_count)
                    self.c.showPage()
                    page_count += 1
                    self.draw_fixed_header(f"Evidence: {category.replace('_',' ').title()} (Cont.)")
                    y_cursor = self.h - 300

                # Image Handling
                img_path = os.path.join(self.cache_dir, f"{row['id']}.jpg")
                if not os.path.exists(img_path):
                    url = row['image_url']
                    if "drive.google.com" in url:
                        try:
                            fid = url.split("/file/d/")[1].split("/")[0]
                            url = f"https://drive.google.com/uc?export=download&id={fid}"
                        except: pass
                    try:
                        res = requests.get(url, timeout=15)
                        res.raise_for_status()

                        if "text/html" in res.headers.get("Content-Type", ""):
                              raise Exception("Not direct image link")

                        img = Image.open(BytesIO(res.content))
                        img = img.convert("RGB")
                        img.save(img_path)
                    except Exception as e:
                          print(f"❌ Failed to download image {row['id']}: {e}")

                # Draw Image
                if os.path.exists(img_path):
                    self.c.drawImage(img_path, x_pos[col], y_cursor, width=230, height=155)
                else:
                    self.c.setStrokeColor(grey)
                    self.c.rect(x_pos[col], y_cursor, 230, 155)
                    self.c.drawCentredString(x_pos[col]+115, y_cursor+75, "Image Link Broken")

                # Caption
                self.c.setFont("Helvetica-Bold", 9)
                self.c.setFillColor(black)
                self.c.drawString(x_pos[col], y_cursor - 15, f"Alert ID: {row['id']}")
                self.c.setFont("Helvetica", 8)
                self.c.setFillColor(TEXT_GRAY)
                self.c.drawString(x_pos[col], y_cursor - 28, f"GPS: {row.get('latitude')}, {row.get('longitude')}")
                self.c.drawString(x_pos[col], y_cursor - 38, f"Timestamp: {row.get('timestamp')}")

            self.footer(page_count)
            self.c.showPage()
            page_count += 1

    # =============================================
    # FINAL PAGE: CONCLUSION
    # =============================================
    def build_conclusion(self, df):
        self.draw_fixed_header("Final Inspection Assessment")

        text = self.c.beginText(60, self.h - 180)
        text.setFont("Helvetica-Bold", 14)
        text.setFillColor(PRIMARY)
        text.textLine("Conclusion & Statutory Remarks")
        text.moveCursor(0, 15)

        text.setFont("Helvetica", 11)
        text.setFillColor(black)
        text.setLeading(20)

        lines = [
            f"1. A comprehensive AI analysis identified {len(df)} safety deviations.",
            f"2. Priority attention is required for: {df['type'].mode()[0].replace('_',' ').upper()}.",
            "3. All visual evidence provided is timestamped and geolocated.",
            "4. Deployment of safety marshals is advised at coordinates flagged in this report.",
            "5. The rest shelter and lighting arrangements should be reviewed as per DGMS guidelines.",
            "",
            "Disclaimer: This is an AI-generated report for surveillance support.",
            "Verification by a Safety Officer is mandatory before statutory action."
        ]

        for line in lines:
            text.textLine(line)

        self.c.drawText(text)
        self.footer("End")
        self.c.showPage()

# =============================================
# WORKFLOW EXECUTION
# =============================================
def generate_report_from_json(data, output_path="report.pdf"):
    violations = data.get("violations", [])
    meta = {
        "location": data.get("location", "Site"),
        "date": data.get("date", "2026-01-01"),
        "drone_id": data.get("drone_id", "DRONE-X")
    }

    df = pd.DataFrame(violations)

    report = FinalDroneReport(output_path, meta)
    report.build_cover_page(df, video_link=data.get("video_link"))
    report.build_analytics_page(df)
    report.build_evidence_log(df)
    report.build_conclusion(df)
    import shutil
    report.c.save()

# Optional cleanup
    shutil.rmtree("image_cache", ignore_errors=True)

    return output_path

 
