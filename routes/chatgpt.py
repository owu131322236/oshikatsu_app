# 事前に pip install Pillow を実行して、画像処理ライブラリPillowをインストールしておく

###########################################################
## 以下、OpenAI APIを使うための前処理       ################
###########################################################
from openai import OpenAI
import os
from PIL import Image
import io
import base64

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI APIキーが設定されていません。環境変数 'OPENAI_API_KEY' を設定してください。")
client = OpenAI(api_key=api_key)

def build_prompt(category_names):
    category_text = "\n".join([f"- {c}" for c in category_names])

    return f"""
次の画像はアニメグッズです。

以下のカテゴリ一覧の中から、
最も適切なカテゴリを1つだけ選んでください。

カテゴリ一覧:
{category_text}

あわせて以下を推測してください：
- 作品名
- キャラクター名
- 検索用キーワード（日本語、3〜6個）

以下のJSON形式でのみ答えてください：

{{
  "category": "カテゴリ名",
  "title": "作品名",
  "character": "キャラクター名",
  "keywords": ["...", "..."]
}}
"""


def get_chatgpt_response(imgurl_data, prompt):
    try:
        # --- 1. 送られてきたBase64データをデコードして保存 ---
        # ブラウザから届いた文字列を、画像ファイル（バイナリ）に戻します
        image_data = base64.b64decode(imgurl_data)
        
        # 指定された通り「uploaded.png」として一度保存
        with open("uploaded.png", mode="wb") as f:
            f.write(image_data)

        # --- 2. 画像リサイズ処理 ---
        image = Image.open("uploaded.png")
        max_size_tuple = (768, 768)
        # thumbnailメソッドは、アスペクト比（縦横比）を維持したままリサイズします
        image.thumbnail(max_size_tuple)
            
        # --- 3. リサイズした画像をBase64に再エンコード ---
        # APIに送るために、再びテキスト形式（Base64）に変換します
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        resized_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # APIが受け取れる形式（Data URI形式）に整える
        full_data_url = f"data:image/png;base64,{resized_base64}"

        # --- 4. OpenAI API (gpt-4o-mini) を呼び出す ---
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": full_data_url
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
        )
        
        # 回答テキストを返す
        return response.choices[0].message.content

    except Exception as e:
        print(f"Error in chatgpt.py: {e}")
        return f"エラーが発生しました: {str(e)}"
