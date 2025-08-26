import os
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler
import json

CLINICS_LIST = """
"الباطنة-العامة", "غدد-صماء-وسكر", "جهاز-هضمي-ومناظير", "الجراحة-العامة", "نساء-وتوليد", 
"أنف-وأذن-وحنجرة", "الصدر", "الجلدية", "العظام", "المخ-والأعصاب-باطنة", "المسالك-البولية", 
"الأطفال", "الرمد", "القلب", "الأسنان", "أمراض-الدم"
"""

class handler(BaseHTTPRequestHandler):
    
    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        # الرد على الطلبات العادية التي تحدث عند زيارة الصفحة الرئيسية
        # هذا يمنع ظهور خطأ 501
        self._set_headers()
        response = {"status": "ok", "message": "AI server is running"}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            symptoms = data.get('symptoms')

            if not symptoms:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing symptoms"}).encode('utf-8'))
                return
            
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": "API key not configured"}).encode('utf-8'))
                return

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            prompt = f"""
            أنت مساعد طبي ذكي. مهمتك هي قراءة شكوى المريض واقتراح أفضل عيادتين من قائمة العيادات المتاحة.
            قائمة IDs العيادات المتاحة هي: [{CLINICS_LIST}]
            شكوى المريض: "{symptoms}"
            ردك يجب أن يكون بصيغة JSON فقط، يحتوي على قائمة اسمها "recommendations" بداخلها الـ ID الخاص بالعيادات المقترحة.
            مثال للرد الصحيح: {{"recommendations": ["الرمد", "الباطنة-العامة"]}}
            """
            
            response = model.generate_content(prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            
            self._set_headers(200)
            self.wfile.write(cleaned_response.encode('utf-8'))

        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
