import openai
import os
import time
import json
import csv
from openai import OpenAI

client = OpenAI(
    api_key="your-api",
    base_url="https://api.deepseek.com/v1",
)


def ask_gpt(full_prompt, retry=3):
    for attempt in range(retry):
        try:
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {
                        "role": "system",
                        "content": """，請回答以下問題：
        【請務必根據台灣法條回答，不要編造或推測】
        請僅回應 A、B、C 或 D，不要提供額外解釋。""",
                    },
                    {"role": "user", "content": full_prompt},
                ],
                temperature=0.1,
                max_tokens=2,
            )
            # 檢查 API 回應
            print(f"🟢 API 回應類型: {type(response)}")

            # 檢查 response 是否為字串
            if isinstance(response, str):
                print("⚠️ API 回傳字串，可能是錯誤訊息！")
                print(f"🟢 API 回應內容: {response}")
                print(f"⚠️ 第 {attempt+1} 次請求 API，結果是空字串，重試中...")
                time.sleep(3)  # 等待 2 秒再試
            else:
                return response.choices[0].message.content 

        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
            return None


def load_data(filename):
    """讀取 JSON 或 CSV 檔案"""
    if filename.endswith(".json"):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    elif filename.endswith(".csv"):
        data = []
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    else:
        raise ValueError("Unsupported file format")


def save_data(data, filename):
    """儲存 JSON 檔案"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ 資料已儲存至 {filename}")


"""讀取試題，詢問AI，儲存答案，並計算正確率"""
data = load_data("民法exam_questions.json")

start = time.time()
for item in data:
    question = item["question"]
    choices = item.get("choices", {})  # 確保選項存在
    formatted_choices = "\n".join([f"{value}" for key, value in choices.items()])

    full_prompt = f"根據台灣法律，請回答以下問題：【請務必根據台灣法條回答，不要編造或推測】問題：{question}\n請從以下選項選擇：\n{formatted_choices}"
    ai_answer = ask_gpt(full_prompt)
    item["deepseek_answer"] = ai_answer  
    print(ai_answer)
    save_data(data, "updated_deepseek_r1_" + "民法exam_questions.json")


end = time.time()
print("✅✅✅運行時間: %s Seconds" % (end - start))

with open("updated_deepseek_r1_民法exam_questions.json", "r", encoding="utf-8") as f:
    k = json.load(f)
correct = 0
total = len(k)
for item in k:
    gpt = item["deepseek_answer"].replace("(", "").replace(")", "")
    answer_str = str(item["answer"]).strip()
    answer_map = {"1": "A", "2": "B", "3": "C", "4": "D"}
    correct_answer = answer_map.get(answer_str, answer_str)

    if correct_answer.upper() == gpt.upper():
        correct += 1
    else:
        print(item)
        print(correct_answer, gpt)

    accuracy = (correct / total) * 100 if total > 0 else 0
print(f"✅ DS 正確率: {accuracy:.2f}% ({correct}/{total})")
