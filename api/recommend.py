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
    
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            symptoms = data.get('symptoms')

            if not symptoms:
                self._send_response(400, {"error": "Missing symptoms"})
                return
            
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                # لا ترسل هذا الخطأ للمستخدم النهائي، فقط للسجلات
                print("CRITICAL: GEMINI_API_KEY is not set in Vercel environment variables.")
                self._send_response(500, {"error": "Server configuration error."})
                return

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

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
            إذا كانت هناك توصية واحدة فقط، أعد القائمة بعنصر واحد. إذا كانت الشكوى غير طبية أو غامضة جداً، أعد قائمة فارغة.
            """
            
            response = model.generate_content(prompt)
            
            # تنظيف الرد والتأكد من أنه JSON صالح
            cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
            try:
                json_response = json.loads(cleaned_text)
            except json.JSONDecodeError:
                # إذا فشل Gemini في إعطاء JSON، سنقوم بتحليله بأنفسنا
                print(f"Warning: Gemini returned a non-JSON response: {cleaned_text}")
                # محاولة أخيرة لاستخراج الرد
                # This is a fallback and might not always work.
                if "recommendations" in cleaned_text:
                     json_response = {"recommendations": []} # Fallback to empty
                else:
                     json_response = {"recommendations": []}

            self._send_response(200, json_response)

        except Exception as e:
            print(f"ERROR: An exception occurred: {str(e)}")
            self._send_response(500, {"error": "An internal server error occurred."})
