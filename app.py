from flask import Flask, render_template, request, jsonify
from langchain_groq import ChatGroq
from datetime import datetime
import json

app = Flask(__name__)

groq_api_key = """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"""

llm = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name="gemma2-9b-it")

def extract_json(response_text):
    """Extracts and parses JSON from LLM response, handling errors."""
    try:
        # Find the JSON part in the response
        start_index = response_text.find("{")  # Find first `{`
        end_index = response_text.rfind("}")   # Find last `}`

        if start_index == -1 or end_index == -1:
            raise ValueError("No valid JSON found.")

        json_text = response_text[start_index:end_index + 1]  # Extract JSON
        return json.loads(json_text)  # Convert to dictionary
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Could not parse JSON response. Details: {e}")
        return {}  # Return empty dictionary on failure


def get_folder(question):
    prompt = f"""You are an expert in calculating dates.
    
    **Current Date:** {datetime.now().date()}  

    **User Question:**  
    {question}

    **Expected JSON Format:**  
    {{"dates": ["YYYY-MM-DD", "YYYY-MM-DD", ...]}}

    **Instructions:**  
    - Provide exact dates based on the user question.  
    - If no specific range is mentioned, return today's date.  
    - Output JSON only. No extra text.
    """

    content = llm.invoke(prompt).content
    return extract_json(content)


def get_file_name(question):
    prompt = f"""
    You are an expert in selecting the most relevant files for the user's question.

    **Available Files:**  
    ['eng.chinamil.com.cn.txt', 'eng.chinamil.com.cn_ARMEDFORCES_index.html.txt', 'eng.chinamil.com.cn_BILINGUAL_News_209203_index.html.txt', 'eng.chinamil.com.cn_BILINGUAL_Opinions_209205_index.html.txt', 'eng.chinamil.com.cn_CHINA_209163_Exchanges_index.html.txt', 'eng.chinamil.com.cn_CHINA_209163_Exercises_index.html.txt', 'eng.chinamil.com.cn_CHINA_209163_Features_209191_index.html.txt', 'eng.chinamil.com.cn_CHINA_209163_MOOTW_index.html.txt', 'eng.chinamil.com.cn_CHINA_209163_Other_index.html.txt', 'eng.chinamil.com.cn_CHINA_209163_SpecialReports_209190_index.html.txt', 'eng.chinamil.com.cn_CHINA_209163_TopStories_209189_index.html.txt', 'eng.chinamil.com.cn_CHINA_209163_WeaponryEquipment_index.html.txt', 'eng.chinamil.com.cn_CMC_Departments_index.html.txt', 'eng.chinamil.com.cn_CMC_Leaders_index.html.txt', 'eng.chinamil.com.cn_CMC_News_209224_index.html.txt', 'eng.chinamil.com.cn_INTERNATIONALREPORTS_209193_InternationalMediaReportsonChina_index.html.txt', 'eng.chinamil.com.cn_INTERNATIONALREPORTS_209193_InternationalMilitariesReportsonChina_index.html.txt', 'eng.chinamil.com.cn_OPINIONS_209196_index.html.txt', 'eng.chinamil.com.cn_VOICES_MilitaryServices_index.html.txt', 'eng.chinamil.com.cn_VOICES_MinistryofForeignAffairs_index.html.txt', 'eng.chinamil.com.cn_VOICES_MinistryofNationalDefense_209794_index.html.txt', 'eng.chinamil.com.cn_VOICES_OtherSources_index.html.txt', 'eng.chinamil.com.cn_WORLD_209198_WorldMilitaryAnalysis_index.html.txt', 'eng.chinamil.com.cn_WORLD_209198_WorldMilitaryNews_index.html.txt']

    **User Query:**  
    {question}

    **Expected JSON Format:**  
    {{"file_names": ["file1.txt", "file2.txt"]}}

    **Instructions:**  
    - Choose the most relevant files from the provided list.  
    - Output JSON only. No extra text.
    """

    content = llm.invoke(prompt).content
    return extract_json(content)

def get_answer(question, folders_data, files_data):    
    answer_dict = {}
    for date in folders_data["dates"]:
        for file in files_data["file_names"]:
            with open(f"./{date}/{file}", "r", encoding="utf-8") as f:
                content = f.read()
            prompt = f"""
            You are an expert in answering the user question from the below text provided

            **text**
            {content}

            **user question**
            {question}

            **IMPORTANT**
            - Answer the question only from the text provided. Try to keep in points if possible, it should be professional.
            """

            content = llm.invoke(prompt).content

            content = content.replace("*","")

            answer_dict[f"{date} - {file}"] = content

    return answer_dict

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    
    folders_data = get_folder(user_input)
    files_data = get_file_name(user_input)
    answer_dict = get_answer(user_input, folders_data, files_data)
    
    return jsonify({"answer_dict": answer_dict, "user_input": user_input})

if __name__ == '__main__':
    app.run(debug=True)