# GCP Data Engineer Exam Preparation

A Streamlit application to help prepare for the Google Cloud Professional Data Engineer certification exam.

## Features

- **Browse Questions**: Search and filter through a comprehensive collection of exam questions
- **Practice Quiz**: Take customizable quizzes with up to 50 questions
- **Image Support**: View diagrams and images associated with questions and answers
- **Statistics Dashboard**: Analyze question distribution by topic and difficulty
- **Performance Tracking**: Review your quiz results and identify areas for improvement

## Installation

```bash
# Clone the repository
git clone https://github.com/marianreply/GCP_Data_Engineer_prep.git
cd GCP_Data_Engineer_prep

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Usage

1. **Browse Questions**: Explore the question database, search by keyword, or filter by topic
2. **Practice Quiz**: Configure a quiz with your preferred number of questions and topics
3. **Review Results**: Get immediate feedback on your answers and see detailed explanations

## Data Source

The application uses a curated JSON dataset (`clean_exam_questions.json`) containing questions, multiple-choice answers, correct answers, and associated images extracted from the official exam preparation materials.

## Note

Case study questions are not included in this exam preparation tool.

## License

This project is provided for educational purposes only. All content is intended for exam preparation.

## Acknowledgments

- Streamlit for the interactive web application framework
- Google Cloud for providing the certification and exam preparation materials 