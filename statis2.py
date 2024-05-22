import json
import streamlit as st
import pandas as pd
import replicate

# Custom CSS for styling
st.markdown("""
    <style>
        .centered {
            display: flex;
            justify-content: center;
            align-items: center;
            height: full;
            font-size: 1.5em;
            color: yellow;
        }
        .yellow-text {
            color: yellow;
        }
        .sidebar-title {
            color: yellow;
            font-size: 2em;
            text-align: center;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# Function to stream generated code directly from Replicate
def stream_data(input_data):
    code_events = []
    for event in replicate.stream(
        "snowflake/snowflake-arctic-instruct",
        input=input_data
    ):
        code_events.append(event.data)

    # Join all events into a single string
    formatted_text = "".join(code_events)

    # Find the index of the code block
    start_idx = formatted_text.find("```python")
    end_idx = formatted_text.find("```", start_idx + 1)

    # Extract text and code parts
    if start_idx != -1 and end_idx != -1:
        text_part = formatted_text[:start_idx]
        code_part = formatted_text[start_idx + len("```python"):end_idx]
    else:
        text_part = formatted_text
        code_part = ""

    return text_part, code_part

def stream_data_sql(input_data):
    code_events = []
    for event in replicate.stream(
        "snowflake/snowflake-arctic-instruct",
        input=input_data
    ):
        code_events.append(event.data)

    # Join all events into a single string
    formatted_text = "".join(code_events)

    # Find the index of the code block
    start_idx = formatted_text.find("```sql")
    end_idx = formatted_text.find("```", start_idx + 1)

    # Extract text and code parts
    if start_idx != -1 and end_idx != -1:
        text_part = formatted_text[:start_idx]
        code_part = formatted_text[start_idx + len("```sql"):end_idx]
    else:
        text_part = formatted_text
        code_part = ""

    return text_part, code_part

# Function to get prompt suggestions from Replicate
def get_prompt_suggestions(data_columns, task_type):
    input_data = {
        "prompt": f"Suggest 3 {task_type} prompts (only prompts no code in json format only) for data analysis with columns: {data_columns} in JSON format only",
        "temperature": 0.2,
    }

    suggestions = []
    for event in replicate.stream(
        "snowflake/snowflake-arctic-instruct",
        input=input_data
    ):
        suggestions.append(event.data)

    suggestions_text = "".join(suggestions)

    # Parse the suggestions
    parsed_suggestions = []
    lines = suggestions_text.split('\n')
    for line in lines:
        line = line.strip()
        if line and line[0].isdigit() and line[1] in '. ':
            parsed_suggestions.append(line[2:].strip())

    return parsed_suggestions

# Streamlit interface
st.sidebar.markdown("<div class='sidebar-title'>STATIS AI</div>", unsafe_allow_html=True)

# Sidebar for layout selection and settings
st.sidebar.header("Python/SQL code generation with natural language")
layout = st.sidebar.selectbox("Select Layout", ["Python Data Visualization", "SQL Generation"])
temperature = st.sidebar.slider("Model Temperature", 0.0, 1.0, 0.2)

# Sidebar for file upload
uploaded_file = st.sidebar.file_uploader("Upload your CSV or Excel file", type=['csv', 'xlsx'])

if uploaded_file:
    # Read data into a DataFrame
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.write("Data Preview:")
    st.write(df.head())

    # Get prompt suggestions
    columns = df.columns.tolist()
    task_type = "SQL query" if layout == "SQL Generation" else "Python code"
    prompt_suggestions = get_prompt_suggestions(columns, task_type)

    st.write("Prompt Suggestions:")
    for suggestion in prompt_suggestions:
        if suggestion.strip():
            if st.button(suggestion):
                st.session_state['query'] = suggestion


    # Display layout based on selection
    if layout == "Python Data Visualization":
        st.header("Python Data Visualization")
        st.write("Use this layout to generate Python code for data analysis and visualization.")

        query_input_placeholder = st.empty()
        if 'query' in st.session_state:
            query_input = query_input_placeholder.text_input("Enter your query:", value=st.session_state['query'])
        else:
            query_input = query_input_placeholder.text_input("Enter your query:")


        if st.button("Analyze"):
            input_data = {
                "prompt": f"Generate a Python code (in ```python (code goes here..) ``` format) (do not give or mention any sample data in code. I have my own data with name: {uploaded_file.name}) for the following data analysis task: {query_input}\n\nColumns:\n{columns}\n NO step by step guide, some text before code explaning it and then the code itself",
                "temperature": temperature,
            }

            text_part, code_part = stream_data(input_data)
            st.markdown(text_part)

            if code_part:
                st.code(code_part, language='python')

    elif layout == "SQL Generation":
        st.header("SQL Generation")
        st.write("Use this layout to generate SQL queries based on your data.")

        query_input_placeholder = st.empty()
        if 'query' in st.session_state:
            query_input_1 = query_input_placeholder.text_input("Enter your query:", value=st.session_state['query'])
        else:
            query_input_1 = query_input_placeholder.text_input("Enter your query:")

        if st.button("Generate SQL Query"):
            input_data = {
                "prompt": f"Generate an SQL query (in ```sql (query goes here..) ``` format) for the following task: {query_input_1}\n\n for the table with Columns:\n{columns}\n NO step by step guide, some text before query explaning it and then the query itself",
                "temperature": temperature,
            }

            text_part, sql_query = stream_data_sql(input_data)
            st.markdown(text_part)

            if sql_query:
                st.code(sql_query, language='sql')

else:
    st.markdown("<div class='centered'>Please upload a CSV or Excel file to begin.</div>",unsafe_allow_html=True)