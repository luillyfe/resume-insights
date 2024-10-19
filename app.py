import streamlit as st
import tempfile
import random
import json

from models import JobSkill
from resume_parser import get_insights, llm


def main():
    st.set_page_config(page_title="Resume Insights", page_icon="📄")

    st.title("Resume Insights")
    st.write("Upload a resume PDF to extract key information.")

    # Show upload file control
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        if st.button("Get Insights"):
            with st.spinner("Parsing resume... This may take a moment."):
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                        temp_file_path = temp_file.name

                    st.session_state.insights = get_insights(temp_file_path)

                except Exception as e:
                    st.error(f"An error occurred while parsing the resume: {str(e)}")

        if "insights" in st.session_state:
            insights = st.session_state.insights

            st.subheader("Extracted Information")
            st.write(f"**Name:** {insights.name}")
            st.write(f"**Email:** {insights.email}")
            st.write(f"**Age:** {insights.age}")

            display_skills(insights.skills)

    else:
        st.info("Please upload a PDF resume to get started.")

    # App information
    st.sidebar.title("About")
    st.sidebar.info(
        "This app uses LlamaIndex and Gemini to parse resumes and extract key information. "
        "Upload a PDF resume to see it in action!"
    )


def display_skills(skills):
    if skills:
        st.subheader("Top Skills")

        # Custom CSS for skill bars
        st.markdown(
            """
        <style>
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #4CAF50, #8BC34A);
        }
        .skill-text {
            font-weight: bold;
            color: #1E1E1E;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Display skills with progress bars and hover effect
        for skill in skills:
            col1, col2 = st.columns([3, 7])
            with col1:
                st.markdown(
                    f"<p class='skill-text'>{skill}</p>", unsafe_allow_html=True
                )
            with col2:
                # Generate a random proficiency level for demonstration
                proficiency = random.randint(60, 100)
                st.progress(proficiency / 100)

        # Expandable section for skill details
        job_position = st.selectbox(
            "Select a job position:",
            [
                "Founding AI Data Engineer",
                "Founding AI Engineer",
                "Founding AI Engineer, Backend",
                "Founding AI Solutions Engineer",
            ],
            on_change=lambda: st.session_state.pop("job_matching_skills", None),
        )
        company = "LlamaIndex"

        st.subheader(
            f"How relevant are the skills for {job_position} Position at {company}?"
        )

        with st.spinner("Matching candidate's skills to job position..."):
            skills_job_prompt = [
                f"""Given this skill: {skill}, please provide your reasoning for why this skill 
                    matter to the follloging job position: {job_position} at {company}.
                    if the skill is not relevant please say so.
                    Use system thinking level 3 to accomplish this task"""
                for skill in skills
            ]

            skills_job_prompt = f"""{", ".join(skills_job_prompt)}
                output shema: {JobSkill().model_dump_json()}
                Provide the result in a structured JSON format. Please remove any ```json ``` characters from the output.
                """

            if "job_matching_skills" not in st.session_state:
                output = llm.complete(skills_job_prompt)
                st.session_state.job_matching_skills = json.loads(output.text)
            else:
                with st.expander("Skill Relevance"):
                    for (
                        _,
                        props,
                    ) in enumerate(st.session_state.job_matching_skills["results"]):
                        st.write(f"**{props["skill"]}**: {props["relevance"]}")

        # Interactive elements
        selected_skill = st.selectbox(
            "Select a skill to highlight:",
            map(
                lambda props: props["skill"],
                st.session_state.job_matching_skills["results"],
            ),
        )
        st.info(
            f"{[skill["reasoning"] for skill in st.session_state.job_matching_skills["results"] if skill["skill"] == selected_skill][0]}"
        )


if __name__ == "__main__":
    main()
