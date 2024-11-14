import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def call_gemini_api(prompt):
    """
    Calls the Gemini API with a specified prompt.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Print the full response object for inspection
        print("Full Response:", response)
        
        # Check if 'text' is in response; return error if missing
        if hasattr(response, 'text'):
            return response.text
        else:
            return '{"answer": "Unexpected response structure from the Gemini API."}'
    except Exception as e:
        print(f"Request failed: {e}")
        return '{"answer": "An error occurred while contacting the Gemini API."}'

def csv_tool(file) -> pd.DataFrame:
    """
    Reads a CSV file and returns it as a DataFrame.
    """
    df = pd.read_csv(file)
    return df

def ask_agent(df, query):
    """
    Creates a prompt, sends it to the Gemini API, and decodes the response.
    """
    prompt = (
        """
        Let's decode the way to respond to the queries. The responses depend on the type of information requested in the query. 

        1. If the query requires a table, format your answer like this:
           {"table": {"columns": ["column1", "column2", ...], "data": [[value1, value2, ...], [value1, value2, ...], ...]}}

        2. For a bar chart, respond like this:
           {"bar": {"columns": ["A", "B", "C", ...], "data": [25, 24, 10, ...]}}

        3. If a line chart is more appropriate, your reply should look like this:
           {"line": {"columns": ["A", "B", "C", ...], "data": [25, 24, 10, ...]}}

        4. For a plain question that doesn't need a chart or table, your response should be:
           {"answer": "Your answer goes here"}

        5. If the answer is not known or available, respond with:
           {"answer": "I do not know."}
        Example output: {"columns": ["Products", "Orders"], "data": [["51993Masc", 191], ["49631Foun", 152]]}

        Here's the query to work on: 
        """ + query
    )

    response_text = call_gemini_api(prompt)
    return str(response_text)
    

def decode_response(response: str) -> dict:
    """
    Decodes the response into a dictionary.
    """
    try:
        # If response is a plain string, return it directly as an answer
        if isinstance(response, str) and not response.startswith('{'):
            
            return json.loads(response)
        # If it's JSON, parse it
        return {"answer": response}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}, Response content: {response}")
        return {"answer": "Invalid response format from the Gemini API."}

def write_answer(response_dict: dict):
    """
    Write a response from an agent to a Streamlit app.

    Args:
        response_dict: The response from the agent.

    Returns:
        None.
    """
    if "answer" in response_dict:
        st.write(response_dict["answer"])

    # Check if the response contains a table
    if "table" in response_dict:
        try:
            columns = response_dict["table"]["columns"]
            data = response_dict["table"]["data"]
            df = pd.DataFrame(data, columns=columns)
            st.write("Generated Table:")
            st.table(df)
        except Exception as e:
            st.write(f"Error displaying table: {e}")
            print(f"Error creating table: {e}")

    # Check if the response is a bar chart
    if "bar" in response_dict:
        try:
            data = response_dict["bar"]
            df_data = {
                col: [x[i] for x in data['data']] for i, col in enumerate(data['columns'])
            }
            df = pd.DataFrame(df_data)
            df.set_index(df.columns[0], inplace=True)  # Automatically set the first column as index
            st.write("Generated Bar Chart:")
            st.bar_chart(df)
        except Exception as e:
            st.write(f"Error creating bar chart: {e}")
            print(f"Error creating bar chart: {e}")

    # Check if the response is a line chart
    if "line" in response_dict:
        try:
            data = response_dict["line"]
            df_data = {
                col: [x[i] for x in data['data']] for i, col in enumerate(data['columns'])
            }
            df = pd.DataFrame(df_data)
            df.set_index(df.columns[0], inplace=True)  # Automatically set the first column as index
            st.write("Generated Line Chart:")
            st.line_chart(df)
        except Exception as e:
            st.write(f"Error creating line chart: {e}")
            print(f"Error creating line chart: {e}")

# Streamlit App Layout
st.set_page_config(page_title="👨‍💻 Talk with your CSV")
st.title("----CSV Query Bot----")
st.write("Please upload the CSV file below.")

data = st.file_uploader("Upload a CSV", type="csv")
query = st.text_area("Send a Message")

if st.button("Submit Query", type="primary"):
    if data:
        df = csv_tool(data)
        response = ask_agent(df, query)
        # Decode the response.
        decoded_response = decode_response(response)

    # Write the response to the Streamlit app.
        write_answer(decoded_response)
        
    else:
        st.write("Please upload a CSV file.")
