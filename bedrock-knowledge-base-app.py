"""
##### IMPORTANT NOTES #####
1. Edit setup-environment.sh as you may have to remove the "3" in python3 and pip3 depending on your system
2. Run "chmod +x setup-environment.sh" in your terminal
3. Run "source ./setup-environment.sh" in your terminal
4. Authenticate with AWS and then run "streamlit run [PYTHON-APP-FILE-NAME].py" in your terminal.  A browser window/tab will appear with the application.
#####
"""

import boto3
import io
import json
import pandas
import streamlit as st
import uuid

# Set Streamlit page configuration
st.set_page_config(page_title="Amazon Bedrock Knowledge Bases", layout="wide")
st.title("🤖 Amazon Bedrock Knowledge Bases")

KNOWLEDGE_BASE_ID = "ABCDEFGHIJ"

# A good example format of a foundation model arn can be found at the link.  Look at the format of the "Resource" arn.  You would replace the * with the desired region, ex: us-west-2.
# https://docs.aws.amazon.com/bedrock/latest/userguide/security_iam_id-based-policy-examples.html#security_iam_id-based-policy-examples-deny
# Model IDs: https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
AMAZON_BEDROCK_FOUNDATION_MODEL_ARN = (
    "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-instant-v1"
)


session = boto3.Session()
bedrock_runtime = session.client("bedrock-runtime")
# knowledge base actions fall under the agent runtime
bedrock_agent_runtime = session.client("bedrock-agent-runtime")


def build_citation_html(citations):
    citation_html = ""

    citation_html = '<div id="top-three-sources-container">'
    citation_html += "<ol>"

    for citation in citations:
        citation_html += "<li>"
        # citation_html +=f"""<p><span class="result-title">{citation['source_generated_summary'][0:10]}</span></p>"""
        citation_html += f"""<p><span class="result-preview">{citation['source_generated_summary']}</span></p>"""
        citation_html += f"""<p><span class="result-kb_location"><a href="{citation['source_location_origin']}">KnowledgeBase S3 Source Document (Just for reference, this link won't work with proper S3 security in place.)</a></span></p>"""
        citation_html += "</li>"

    citation_html += "</ol>"
    st.session_state.answer_sources = citation_html
    return citation_html


def build_citations_object(kb_response):

    i = 0
    reference_bank: list = []
    for citation in kb_response["citations"]:
        super_reference = {}

        super_reference["source_generated_summary"] = citation["generatedResponsePart"][
            "textResponsePart"
        ]["text"]
        super_reference["source_citation_offset_start"] = citation[
            "generatedResponsePart"
        ]["textResponsePart"]["span"]["start"]
        super_reference["source_citation_offset_end"] = citation[
            "generatedResponsePart"
        ]["textResponsePart"]["span"]["end"]

        for source_reference in citation["retrievedReferences"]:
            super_reference["source_type"] = source_reference["location"]["type"]
            super_reference["source_location_origin"] = source_reference["location"][
                "s3Location"
            ]["uri"]
            super_reference["source_text"] = source_reference["content"]["text"]

        reference_bank.append(super_reference)

        return reference_bank


def retrieve_and_generate(query):
    response = bedrock_agent_runtime.retrieve_and_generate(
        input={"text": query},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                "modelArn": AMAZON_BEDROCK_FOUNDATION_MODEL_ARN,
            },
        },
    )
    with output_container:
        citations = build_citations_object(response)
        st.markdown(build_citation_html(citations), unsafe_allow_html=True)


input_container = st.container()
output_container = st.container()
with input_container:
    search_query_try = st.text_input(
        label="Enter your query",
        key="search_query_try",
    )
    search_query_submit = st.button(label="Submit Query", key="search_query_submit")

    if search_query_submit:
        results = retrieve_and_generate(search_query_try)
