import os
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler
import json

# قائمة العيادات المتاحة كما هي
CLINICS_LIST = """
"الباطنة-العامة", "غدد-صماء-وسكر", "جهاز-هضمي-ومناظير", "الجراحة-العامة", "نساء-وتوليد", 
"أنف-وأذن-وحنجرة", "الصدر", "الجلدية", "العظام", "المخ-والأعصاب-باطنة", "المسالك-البولية", 
"الأطفال", "الرمد", "القلب", "الأسنان", "أمراض-الدم"
"""

class handler(BaseHTTPRequestHandler):
    
    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

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

            # === الطلب الجديد والأكثر ذكاءً لـ Gemini ===
            prompt = f"""
            أنت مساعد طبي خبير في مستشفى. مهمتك هي تحليل شكوى المريض واقتراح أفضل عيادتين بحد أقصى من قائمة العيادات المتاحة.

            قائمة IDs العيادات المتاحة هي: [{CLINICS_LIST}]

            شكوى المريض: "{symptoms}"

            المطلوب:
            1.  حدد العيادة الأساسية الأكثر احتمالاً.
            2.  اشرح للمريض بلغة بسيطة ومباشرة **لماذا** قمت بترشيح هذه العيادة (اذكر الأعراض التي استندت عليها).
            3.  إذا كان هناك احتمال آخر قوي، حدد عيادة ثانوية واشرح أيضاً لماذا قد تكون خياراً جيداً.
            4.  ردك يجب أن يكون بصيغة JSON فقط، على هذا الشكل بالضبط:
            {{
              "recommendations": [
                {{
                  "id": "ID_العيادة_الأساسية",
                  "reason": "شرح سبب اختيار العيادة الأساسية هنا."
                }},
                {{
                  "id": "ID_العيادة_الثانوية",
                  "reason": "شرح سبب اختيار العيادة الثانوية هنا."
                }}
              ]
            }}
            إذا كانت هناك توصية واحدة فقط، أعد القائمة بعنصر واحد. إذا كانت الشكوى غير طبية، أعد قائمة فارغة.
            """
            
            response = model.generate_content(prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            
            self._set_headers(200)
            self.wfile.write(cleaned_response.encode('utf-8'))

        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
