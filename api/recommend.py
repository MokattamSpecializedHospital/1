import os
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler
import json

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
- "أمراض-الدم": "أمراض الدم"
"""

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # --- CORS Handling for Vercel ---
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        if self.command == 'OPTIONS':
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            symptoms = data.get('symptoms')

            if not symptoms:
                self.wfile.write(json.dumps({"error": "Missing symptoms"}).encode('utf-8'))
                return
            
            # --- Gemini AI Logic ---
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set in Vercel environment variables.")

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
            
            self.wfile.write(cleaned_response.encode('utf-8'))

        except Exception as e:
            # Send a more descriptive error back for debugging
            error_payload = json.dumps({"error": f"An internal error occurred: {str(e)}"}).encode('utf-8')
            self.wfile.write(error_payload)
        return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
