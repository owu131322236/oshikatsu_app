# Windowsのコマンドプロンプトで set GOOGLE_API_KEY=自分のAPIキーを実行しておく

###########################################################
## 以下、Geminiを使うための前処理          ################
###########################################################

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "libs"))
import google.generativeai as genai
import os


GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY') #または、GOOGLE_API_KEY="自分のAPIキー"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')#gemini-2.0-flash

import base64
import PIL.Image

###########################################################
## 以下、Webサーバーとして動かすための処理 ################
###########################################################

from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import socket
import urllib
from urllib.parse import unquote

def ask_gemini(request):
    imgurl = request.form["imgurl"]
    prompt = request.form["prompt"]

    # デコード
    imgBin = base64.b64decode(imgurl)
    prompt = unquote(prompt)

    # 画像保存
    with open("uploaded.png", "wb") as f:
        f.write(imgBin)
    img = PIL.Image.open("uploaded.png")
    img.thumbnail((768, 768))

    # Geminiへ(利用制限に影響する可能性があるので一時的にコメントアウト)
    response = model.generate_content([prompt, img])

    answer = "<b>" + response.text + "</b>"
    return answer

# 先生のコード！念の為、残しておきますが、Flask版を使ってください。
# class MyHandler(SimpleHTTPRequestHandler):

#     def htmlheader(self): #httpヘッダーを出力
#         self.send_response(200)
#         self.end_headers()

#     def do_POST(self):
#         length=self.headers.get('content-length')
#         try:
#             nbytes=int(length)
#         except (TypeError, ValueError):
#             nbytes=0
#         data=self.rfile.read(nbytes)
#         post=urllib.parse.parse_qs(data)

#         if (self.path == "/upload"):
#              imgurl=post[b'imgurl'][0].decode() #パラメタの取り出し。bが必要！
#              imgBin=base64.b64decode(imgurl)
#              open("uploaded.png", mode="wb").write(imgBin) #PNGファイルに保存
             
#              prompt=post[b'prompt'][0].decode() #パラメタの取り出し。bが必要！
#              prompt=unquote(prompt)#日本語文字化け対策
#              print(prompt)
                         
#              img=PIL.Image.open('./uploaded.png')

#              # アスペクト比を維持しながら、指定したサイズ以下の画像に縮小させる。
#              # https://ai.google.dev/gemini-api/docs/image-understanding?hl=ja
#              max_size = (768, 768)
#              img.thumbnail(max_size)
             
#              response=model.generate_content([prompt, img])#geminiに質問して回答を得る
#              answer = "<b>" + response.text + "</b>" #webブラウザに返信するHTML文を作成する
#              print(prompt)
            
#              self.htmlheader()
#              self.wfile.write(answer.encode("utf-8"))#webブラウザに返信する
             

# #openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes

# host = socket.gethostbyname(socket.gethostname()) #'localhost'
# port = 8000
# httpd = HTTPServer((host, port), MyHandler)

# #httpd.socket = ssl.wrap_socket (httpd.socket, certfile='server.pem', server_side=True)
# context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# context.load_cert_chain(certfile='server.pem')
# httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

# print('Ready! Now you can access to https://%s:%s' % (host, port))
# httpd.serve_forever()


