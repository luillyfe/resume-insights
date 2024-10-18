import streamlit as st
import tempfile
import random
import json

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
        st.subheader(
            "How relevant are the skills for Founding AI Data Engineer Position at LlamaIndex?"
        )
        with st.expander("Skill Relevance"):
            skills_job_prompt = [
                f"""Given this skill: {skill}, please provide your reasoning for why this skill 
                matter to the follloging job position: Founding AI Data Engineer at LlamaIndex.
                if the skill is not relevant please say so."""
                for skill in skills
            ]

            skills_job_prompt = f"""{", ".join(skills_job_prompt)}
                Provide the result in a structured JSON format. Please remove any ```json ``` characters from the output.
                """

            if "job_matching_skills" not in st.session_state:
                output = llm.complete(skills_job_prompt)
                st.session_state.job_matching_skills = json.loads(output.text)

            else:
                for skill, reasoning in st.session_state.job_matching_skills.items():
                    st.write(f"**{skill}**: {reasoning['relevance']}")

        # Interactive elements
        selected_skill = st.selectbox(
            "Select a skill to highlight:", st.session_state.job_matching_skills.keys()
        )
        st.info(f"{st.session_state.job_matching_skills[selected_skill]['reasoning']}")


if __name__ == "__main__":
    main()
