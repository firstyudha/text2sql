from langchain_experimental.sql import SQLDatabaseChain
from langchain_ollama import OllamaLLM
from langchain_community.utilities import  SQLDatabase
import streamlit as st

def sql_to_text(sql_url: str, method: str, question: str, model_input: str, api_key: str | None = None) -> str:
    """
    Converts an input question into a SQL query, executes the query on a database, and returns the answer.

    Args:
        sql_url (str): The URL of the SQL database.
        method (str): The method to use for language model. Possible values are "ollama" or "groq".
        question (str): The input question.
        model_input (str): The model input to use for the language model.
        api_key (str | None, optional): The API key for the "groq" method. Defaults to None.

    Returns:
        str: The final answer.

    Raises:
        Exception: If the specified model is not found.

    """
    

    # setup llm
    try:
        if method == "ollama":
            llm = OllamaLLM(temperature=0, model=model_input)
    except:
        st.error("Model not found, please try again")
        st.stop()

    # Create db chain
    QUERY = """
    Given an input question, first create a syntactically correct postgresql query to run, then look at the results of the query and return the answer.
    Use the following format:

    "Question": "Question here"
    "SQLQuery": "SQL Query to run"
    "SQLResult": "Result of the SQLQuery"
    "Answer": "Final answer here"

    "Command: {question}"
    """
    # setup database
    db = SQLDatabase.from_uri(sql_url)
    # Setup the database chain
    # db_chain = SQLDatabaseChain(llm=llm, database=db, verbose=False)
    db_chain = SQLDatabaseChain(llm=llm, database=db, verbose=True, return_intermediate_steps=True)

    # input prompt
    question = QUERY.format(question=question)
    result = db_chain(question)

    # Extract SQL query from intermediate steps
    final_answer = result.get("result","No Result")
    sql_query = result.get("intermediate_steps", [{}])[1]
    sql_result = result.get("intermediate_steps", [{}])[3]

    st.write("### SQL Query:")
    st.code(sql_query, language="sql")

    st.write("### Query Result:")
    st.code(sql_result, language="sql")

    st.write("### Final Answer:")
    st.write(final_answer)


st.title("SQL Database Chain")
st.write("Please input your question below:")

model_provider = st.sidebar.selectbox("Model Provider", ("ollama"))
if model_provider == "ollama":
    st.sidebar.write("Please input the model below:")
    model = st.sidebar.selectbox("Model",("sqlcoder"))
if not model_provider:
    st.sidebar.info("Please select a model provider")

if model_provider == "ollama" and not model:
    st.sidebar.info("Please enter a model")
if not model_provider:
    st.sidebar.info("Please select a model provider")
sql_url = st.sidebar.text_input("SQL URL", "postgresql+psycopg2://postgres:123@localhost:5432/postgres")

with st.form("question_form",clear_on_submit= False):
    question = st.text_input("Question")
    submit_button = st.form_submit_button("Submit")
    try:
        if not question:
            st.info("Please enter a question")
    except:
        st.info("try again")
        pass
    if submit_button:  
        if model_provider == "ollama":
            sql_to_text(sql_url, model_provider, question, model)
