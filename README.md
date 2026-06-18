# study-pal

WEBSITE -https://study-pal.streamlit.app/

It’s a Streamlit web app that helps students study smarter using artificial 
intelligence. You can chat with it, summarize your notes, and even take 
automatically generated quizzes — all powered by Google’s Gemini API.”

Overview of Tools & Modules
-     Python and Streamlit for the interface. 
-     google.genai library to connect to the Gemini API
-     Python built-in modules, re & json.

When you run it, the sidebar lets you switch between three pages: 

1. The Chat page — where you can ask any study question and get AI-generated explanations. 

2. The Summarize Notes page — you can upload your notes or a PDF, and 
it summarizes them neatly using the Gemini model. 

3. Quiz Me page —  Paste your notes, or just write the topic, click Generate Quiz, and it creates multiple-choice questions automatically. Then, after answering, you get your score instantly.

To run the project 
- clone the repo
- to the file .streamlit/secrets.toml add the line
     GEMINI_API_KEY="YOUR GEMINI KEY" #replace "YOUR GEMINI KEY" with your GEMINI API KEY 
- run command in terminal
streamlit run project.py

<img width="1365" height="630" alt="image" src="https://github.com/user-attachments/assets/c5f05b00-817e-44c9-b563-9f6f7ddd3328" />
<img width="1326" height="545" alt="image" src="https://github.com/user-attachments/assets/49818594-8692-4b97-88be-6376115548c4" />
<img width="1025" height="514" alt="image" src="https://github.com/user-attachments/assets/2907849a-aeef-433a-98fd-16391aa7a267" />

