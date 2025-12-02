import streamlit as st
from streamlit_ace import st_ace
import subprocess
import os
from groq import Groq

# -------------------- API KEY --------------------
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# -------------------- Default code per language --------------------
default_code = {
    "Java": """public class UserCode {
    public static void main(String[] args) {
        System.out.println("Hello World!");
    }
}""",

    "Python": """print("Hello World!")""",

    "C": """#include <stdio.h>

int main() {
    printf("Hello World!");
    return 0;
}""",

    "C++": """#include <iostream>
using namespace std;

int main() {
    cout << "Hello World!";
    return 0;
}""",

    "JavaScript": """console.log("Hello World!");"""
}

# -------------------- ERROR EXPLAINER --------------------
def explain_error(language, code, error):
    prompt = f"""
Explain this {language} error:
Code:
{code}

Error:
{error}

Explain in:
- Simple English
- Why it happened
- How to fix it
- Show corrected code
"""
    try:
        resp = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
    except:
        return "AI explanation unavailable."

# -------------------- UI --------------------
st.set_page_config(page_title="AI Code Debugger", layout="wide")

st.markdown("<h1 style='text-align:center;'>Compiler & AI Debugger</h1>",
            unsafe_allow_html=True)

languages = ["Java", "Python", "C", "C++", "JavaScript"]
lang = st.selectbox("Choose Language", languages)

theme = st.selectbox("Editor Theme",
                     ["monokai", "dracula", "solarized_dark", "solarized_light", "github", "xcode"])

if "editor_content" not in st.session_state:
    st.session_state.editor_content = {}

for l in default_code.keys():
    if l not in st.session_state.editor_content:
        st.session_state.editor_content[l] = default_code[l]

st.subheader("Write Your Code")

code = st_ace(
    value=st.session_state.editor_content[lang],
    language="c++" if lang=="C++" else lang.lower(),
    theme=theme,
    key=f"editor_ace_{lang}",
    font_size=16,
    tab_size=4,
    wrap=True,
    auto_update=True,
    height=300
)

st.session_state.editor_content[lang] = code

program_input = st.text_area("Program Input (optional):", height=100)

if st.button("Run Code"):
    filename = ""
    compiler = None
    run_cmd = None

    if lang == "Java":
        filename = "UserCode.java"
        compiler = ["javac", filename]
        run_cmd = ["java", "UserCode"]

    elif lang == "Python":
        filename = "user.py"
        run_cmd = ["python3", filename]

    elif lang == "C":
        filename = "user.c"
        compiler = ["gcc", filename, "-o", "user_c"]
        run_cmd = ["./user_c"]

    elif lang == "C++":
        filename = "user.cpp"
        compiler = ["g++", filename, "-o", "user_cpp"]
        run_cmd = ["./user_cpp"]

    elif lang == "JavaScript":
        filename = "user.js"
        run_cmd = ["node", filename]

    with open(filename, "w") as f:
        f.write(code)

    if compiler:
        compile_run = subprocess.run(
            compiler, capture_output=True, text=True)
        if compile_run.stderr:
            st.error("Compilation Error:")
            st.code(compile_run.stderr)
            st.subheader("AI Explanation")
            st.write(explain_error(lang, code, compile_run.stderr))
            st.stop()

    try:
        execute = subprocess.run(
            run_cmd,
            input=program_input,
            capture_output=True,
            text=True,
            timeout=10
        )

        if execute.stderr:
            st.error("Runtime Error:")
            st.code(execute.stderr)
            st.subheader("AI Explanation")
            st.write(explain_error(lang, code, execute.stderr))
        else:
            st.success("Output:")
            st.code(execute.stdout)

    except subprocess.TimeoutExpired:
        st.error("Execution timed out.")

if st.button("Suggest Corrected Code"):
    prompt = f"Fix this {lang} code:\n```{code}```"
    try:
        resp = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}]
        )
        st.subheader("Corrected Code")
        st.code(resp.choices[0].message.content)

    except:
        st.error("AI couldn't generate corrected code.")
