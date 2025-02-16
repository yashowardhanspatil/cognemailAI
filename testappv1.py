import re
import streamlit as st
from serpapi import Client
from groq import Groq
import pandas as pd

# load_dotenv()
# SERPAPI_KEY = os.getenv("SERPAPI_KEY")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def search_web_with_serpapi(query):
    try:
        client = Client(api_key=SERPAPI_KEY)
        result = client.search(q=query, hl="en", gl="in", safe="active")

        if "error" in result:  # Check for API errors
            st.error(f"SerpAPI Error: {result['error']}")
            return []

        return result.get("organic_results", [])

    except Exception as e:
        st.error(f"An error occurred while fetching data from SerpAPI: {str(e)}")
        return []

def extract_emails_from_snippets(snippets):
    text = " ".join(snippets)
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return emails[0] if emails else None

def extract_email_with_groq(snippets, entity):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        combined_snippets = " ".join(snippets)

        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Extract only official, verified email addresses related to {entity} from the text below.\n"
                        f"Ignore any personal, spam, or unrelated emails.\n\n"
                        f"{combined_snippets}\n\n"
                        "Provide only the valid email(s) along with their source (if available)."
            }],
            model="llama3-8b-8192",
        )

        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        st.error(f"Error occurred while processing with Groq LLM: {str(e)}")
        return None

def is_unethical_query(query):
    unethical_keywords = ["porn", "hack", "crack", "drugs", "violence", "illegal", "scam", "terrorism", "adult", "carding", "phishing", "sex", "spam", "weapons"]
    return any(keyword in query.lower() for keyword in unethical_keywords)

st.image("Cognemail AI new.png")
st.markdown("### Intelligent Email Discovery, Powered by AI. :e-mail:")
with st.expander("Optional: Enter your API Keys for better performance !"):
    serpkey = st.text_input("SerpAPI key :key: // [Create one here](https://serpapi.com/)", type="password")
    groqkey = st.text_input("GroqLLM API key :key: // [Create one here](https://console.groq.com/playground)", type="password")

SERPAPI_KEY = serpkey if serpkey else st.secrets["SERPAPI_KEY"]
GROQ_API_KEY = groqkey if groqkey else st.secrets["GROQ_API_KEY"]

if not SERPAPI_KEY or not GROQ_API_KEY:
    st.warning("Using default API keys.")

st.write("### Enter the name of the entity to find an email for")
user_query = st.text_area("Example : Enter any desired company, organisation. ")

if st.button("Find Email"):
    if not user_query.strip():
        st.warning("Please enter a valid term.")
    elif is_unethical_query(user_query):
        st.error("Search contains unethical terms, Please enter a valid query.")
    else:
        st.write("Searching... Please wait.")
        results = []

        query = f"{user_query} contact email"

        try:
            search_results = search_web_with_serpapi(query)
            snippets = [result.get("snippet","") for result in search_results]

            if not search_results:
                st.warning(f" No direct results found for '{user_query}'. Trying AI-based extraction...")
            
            extracted_email = extract_emails_from_snippets(snippets)

            if not extracted_email:
                extracted_email = extract_email_with_groq(snippets, user_query)

            if extracted_email:
                st.success(f"✅ Email found: **{extracted_email}**")
                results.append({"Entity":user_query, "Extracted Email": extracted_email})
            else:
                st.error(f"❌ Could not extract an email for '{user_query}'. Try again later.")
        except Exception as e:
            st.error(f"Error: {str(e)}. Please try again later.")

        if results: 
            output_df = pd.DataFrame(results)
            st.write("### 📋 Extracted Information")
            st.table(output_df)


