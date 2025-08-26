import os
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler
import json

# قائمة العيادات
CLINICS_LIST = """
- "الباطنة-العامة": "الباطنة العامة"
- "غدد-صماء-وسكر": "غدد صماء وسكر"
- "جهاز-هضمي-ومناظير": "جهاز هضمي ومناظير"
- "الجراحة-العامة": "الجراحة العامة"
- "نساء-وتوليد": "نساء وتوليد"
- "أنف-وأذن-وحنجرة": "أنف وأذن وحنجرة"
- "الصدر": "الصدر"
- "الجلدية": "الجلدية"
- "العظام": "العظام"
- "المخ-والأعصاب-باطنة": "المخ والأعصاب (باطنة)"
- "المسالك-البولية": "المسالك البولية"
- "الأطفال": "الأطفال"
- "الرمد": "الرمد"
- "القلب": "القلب"
- "الأسنان": "الأسنان"
"""

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data)
            symptoms = data.get('symptoms')

            if not symptoms:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing symptoms"}).encode())
                return

            # --- Gemini AI Logic ---
            api_key = os.environ.get("GEMINI_API_KEY")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            prompt = f"""
            أنت مساعد طبي ذكي. مهمتك هي قراءة شكوى المريض واقتراح أفضل عيادتين من القائمة.
            القائمة (ID: "اسم العيادة"): {CLINICS_LIST}
            شكوى المريض: "{symptoms}"
            ردك يجب أن يكون بصيغة JSON فقط، يحتوي على قائمة اسمها "recommendations" بداخلها الـ ID الخاص بالعيادات.
            مثال: {{"recommendations": ["الرمد", "الباطنة-العامة"]}}
            """
            
            response = model.generate_content(prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(cleaned_response.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
        return
