import streamlit as st
import tempfile

from typing import Dict
from resume_insights.models import SkillDetail
from resume_insights import create_resume_insights


def main():
    st.set_page_config(page_title="Resume Insights", page_icon="📄")

    st.title("Resume Insights")
    st.write("Upload a resume PDF to extract key information.")

    # Show upload file control
    uploaded_file = st.file_uploader(
        "Select Your Resume (PDF)", type="pdf", help="Choose a PDF file up to 5MB"
    )

    if uploaded_file is not None:
        if st.button("Get Insights"):
            with st.spinner("Parsing resume... This may take a moment."):
                try:
                    # Temporary file handling
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                        temp_file_path = temp_file.name

                    # Extract the candidate data from the resume
                    st.session_state.resumeInsights = create_resume_insights(temp_file_path)
                    st.session_state.insights = (
                        st.session_state.resumeInsights.extract_candidate_data()
                    )

                except Exception as e:
                    st.error(f"Failed to extract insights: {str(e)}")

        if "insights" in st.session_state:
            insights = st.session_state.insights

            # Display candidate information in a clean format
            st.subheader("Candidate Profile")

            # Create a two-column layout for contact information
            col1, col2 = st.columns(2)
            
            # Get candidate info from session state
            insights = st.session_state.insights
            
            # Display contact information in the first column
            with col1:
                st.write(f"**Name:** {insights.name}")
                st.write(f"**Email:** {insights.email}")
                st.write(f"**Age:** {insights.age}")
                
                    
            # Display additional information in the second column
            with col2:
                if insights.phone:
                    st.write(f"**Phone:** {insights.phone}")
                if insights.location:
                    st.write(f"**Location:** {insights.location}")
                if insights.summary:
                    # Truncate summary to 200 characters if longer
                    display_summary = insights.summary[:100] + ("..." if len(insights.summary) > 200 else "")
                    st.write(f"**Summary:** {display_summary}")
                    
            # Display professional summary if available
            if insights.summary and len(insights.summary) > 100:
                with st.expander("Full Professional Summary"):
                    st.write(insights.summary)

            # Ensure skills is a dictionary before passing to display_skills
            skills = insights.skills if isinstance(insights.skills, dict) else {}
            display_skills(skills)

    else:
        st.info("Please upload a PDF resume to get started.")

    # App information
    st.sidebar.title("About")
    st.sidebar.info(
        "This app uses LlamaIndex and Gemini to parse resumes and extract key information. "
        "Upload a PDF resume to see it in action!"
    )
    
    # Add visual indicator in sidebar
    if "insights" in st.session_state and st.session_state.insights.skills:
        st.sidebar.markdown("""
        <div style="text-align: center; margin: 20px 0; padding: 10px; border-radius: 5px; background-color: #f0f9ff; border-left: 4px solid #4CAF50;">
            <p style="color: #1E6823; font-weight: bold;">⬇️ Scroll Down ⬇️</p>
            <p style="font-size: 0.9em;">Don't miss the job matching feature below the skills section!</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.sidebar.subheader("Long Rank Dependencies Limitation")
    st.sidebar.info(
        """ LlamaIndex faces challenges when it comes to handling knowledge dispersed across different sections of a document. 
        Specifically, important details like age and skills proficiency that could be inferred by calculating the number of years 
        a candidate has worked are difficult to deduce automatically."""
    )


def display_skills(skills: Dict[str, SkillDetail]):
    if skills: 
        # Skills section
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
        .experience-text {
            font-size: 0.8em;
            color: #555555;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Display skills with progress bars and hover effect
        for skill_name, skill_detail in skills.items():
            col1, col2, col3 = st.columns([3, 6, 1])
            with col1:
                st.markdown(
                    f"<p class='skill-text'>{skill_name}</p>", unsafe_allow_html=True
                )
            with col2:
                # Use the actual proficiency from the SkillDetail object
                # Default to 0 if proficiency is None
                proficiency = skill_detail.proficiency if skill_detail.proficiency is not None else 0
                st.progress(proficiency / 100)
            with col3:
                if skill_detail.years_experience:
                    st.markdown(
                        f"<p class='experience-text'>{skill_detail.years_experience:.1f} yrs</p>",
                        unsafe_allow_html=True,
                    )

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
            if "job_matching_skills" not in st.session_state:
                st.session_state.job_matching_skills = (
                    st.session_state.resumeInsights.match_job_to_skills(
                        skills, job_position, company
                    ).skills
                )
            else:
                with st.expander("Skill Relevance"):
                    for skill_name, skill_match in st.session_state.job_matching_skills.items():
                        st.write(
                            f"**{skill_name}**: {skill_match.relevance}"
                        )

        # Interactive elements
        selected_skill = st.selectbox(
            "Select a skill to highlight:",
            list(st.session_state.job_matching_skills.keys()),
        )
        st.info(f"{st.session_state.job_matching_skills[selected_skill].reasoning}")

        # Additional information about skills
        with st.expander("Skill Details"):
            selected_detail = skills.get(selected_skill)
            if selected_detail:
                st.write(f"**Category:** {selected_detail.category}")
                if selected_detail.mentions:
                    st.write("**Mentioned in:**")
                    for mention in selected_detail.mentions:
                        st.write(f"- {mention}")
                if selected_detail.related_skills:
                    st.write("**Related Skills:**")
                    st.write(", ".join(selected_detail.related_skills))


if __name__ == "__main__":
    main()


