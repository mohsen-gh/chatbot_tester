import random
import time

from fastapi import FastAPI, HTTPException

from chatbot.schema import UserQuery, UserResponse

app = FastAPI()
print("Chatbot API is starting...")


def generate_mock_response(message: str) -> UserResponse:
    """
    Returns UserResponse(response_text, intent_string, confidence_float).
    """
    msg_lower = message.lower()
    
    # These rules are generated based on our sample input dataset just to mock the behavior of a real chatbot. 
    # They are not exhaustive and can be expanded with more patterns and responses.
    rules = [
        # 1. Programs & Admission
        (["study", "programs", "offer"], "programs_overview", "We offer many degrees including Bachelor and Master programs."),
        (["computer science", "bachelor"], "program_availability_check", "Yes, we offer a BSc in Computer Science."),
        (["admission", "requirements"], "admission_requirements", "Please review the admission documents and deadline requirements."),
        (["english", "proficiency"], "language_requirements", "We require TOEFL or IELTS for English requirements."),
        (["deadline", "winter"], "application_deadlines", "The date for the winter semester deadline is July 15th."),
        
        # 2. Tuition & Scholarships
        (["tuition", "fee", "cost"], "tuition_fees_info", "The exact cost of tuition and fees depends on your program."),
        (["international", "students"], "tuition_fees_international", "Non-EU international students have different fees than EU students."),
        (["scholarship"], "scholarship_overview", "We provide financial aid and scholarship funding."),
        (["apply", "scholarship"], "scholarship_application_process", "To apply, submit your documents meeting the requirements."),
        
        # 3. Campus & Location
        (["where", "located"], "campus_location", "Our campus is at this address location in the city center."),
        (["public transport"], "transportation_info", "You can reach us by bus, train, or tram on public transport."),
        (["campus", "tours"], "campus_tour_info", "You can visit the campus by booking a tour online."),
        (["open day"], "open_day_info", "Registration for our next open day event is open now."),
        (["buildings", "admissions"], "admissions_office_location", "The admissions office is located in the main building."),
        
        # 4. Course Catalog & Curriculum
        (["course catalog", "master"], "course_catalog_request", "The Master course catalog modules are online."),
        (["data science", "subjects"], "program_curriculum_details", "The Data Science modules and curriculum focus on ML."),
        (["thesis", "project"], "thesis_requirement_info", "Yes, a thesis project is required in your final semester."),
        
        # 5. Application Portal & Documents
        (["how", "apply"], "application_process_overview", "Follow the steps on the application portal to apply."),
        (["which documents"], "required_documents", "You need to upload your CV, passport, and transcript documents."),
        (["upload", "after"], "application_document_update_policy", "You can upload files after submission until the deadline."),
        (["mistake", "edit"], "application_editing_help", "Please contact support to change or edit your application."),
        (["log in", "portal"], "application_portal_login_issue", "If you cannot login to the portal, reset your password or ask support."),
        
        # 6. International Students & Visa
        (["visa", "support"], "visa_support_info", "We support international students with visa documents."),
        (["admission letter"], "admission_letter_request", "We can issue an official admission letter for your visa."),
        (["residence permit"], "residence_permit_guidance", "Book an appointment upon arrival for your residence permit."),
        (["international office", "contact"], "international_office_contact", "Email the international office via the contact page."),
        
        # 7. Housing & Dorms
        (["student", "dormitories"], "student_housing_overview", "We have dorm accommodation and student housing."),
        (["apply", "housing"], "housing_application_process", "Apply for housing early to get on the waitlist."),
        (["average rent"], "housing_cost_info", "The cost of rent is about 400 euros per month."),
        (["short-term"], "short_term_housing_info", "We have options for temporary and short-term stays."),
        (["guaranteed", "first-year"], "housing_guarantee_policy", "Availability is guaranteed for first-year students."),
        
        # 8. Registration & Enrollment
        (["enroll"], "enrollment_steps", "To enroll, complete the steps before the deadline."),
        (["semester contribution"], "semester_fee_payment", "Pay the semester contribution via bank transfer payment."),
        (["student id"], "student_id_info", "Your student ID card is issued after payment."),
        (["register", "courses"], "course_registration_info", "Use the portal to register for your courses."),
        
        # 9. Exams & Grading
        (["exams", "work"], "exams_overview", "We have a strict assessment schedule for exams."),
        (["exam timetable"], "exam_timetable_request", "The exam schedule and timetable are published online."),
        (["grading scale"], "grading_scale_info", "The grading scale uses points that convert to a GPA."),
        (["retake", "fail"], "exam_retake_policy", "If you fail, you have limited attempts to retake the exam."),
        (["exam review"], "exam_review_request", "You can request an inspection or appeal for an exam review."),
        
        # 10. Student Services & Library
        (["student services"], "student_services_overview", "Our services provide career support and counseling."),
        (["career support"], "career_services_internships", "We offer a CV workshop and help finding an internship for your career."),
        (["library", "online"], "library_online_access", "Login to access the library database online."),
        (["library", "hours"], "library_hours", "The library is open 24 hours a day."),
        (["mental health"], "counseling_services_info", "Book an appointment for mental health counseling."),
        (["thanks"], "thanks", "You are welcome. I am glad to help!")
    ]
    
    # 2. Find a match
    matched_intent = "unknown_intent"
    matched_response = "I am not sure how to answer that."
    
    for triggers, intent, response_text in rules:
        if all(t in msg_lower for t in triggers):  # changed to 'all' for better accuracy across topics
            matched_intent = intent
            matched_response = response_text
            break
            
    # If 'all' fails, fallback to 'any' for a looser match
    if matched_intent == "unknown_intent":
        for triggers, intent, response_text in rules:
            if any(t in msg_lower for t in triggers):
                matched_intent = intent
                matched_response = response_text
                break

    # 3. Inject LLM variability & errors to exercise the evaluator service
    rand_val = random.random()
    
    if rand_val < 0.05:
        # 5% chance: Completely wrong intent
        matched_intent = "confused_ai_intent"
    
    elif rand_val < 0.15:
        # 10% chance: Strip out expected keywords to test semantic/keyword failure
        words = matched_response.split()
        if len(words) > 3:
            matched_response = "We definitely have something like that available for you. " + words[-1]
    
    elif rand_val < 0.20:
        # 5% chance: Format issue
        matched_intent = matched_intent.replace("_", "-").upper()

    # 4. Generate confidence score
    confidence = round(random.uniform(0.85, 0.99), 2)
    if rand_val < 0.10:
        confidence = round(random.uniform(0.40, 0.60), 2)
        
    return UserResponse(response=matched_response, intent=matched_intent, confidence=confidence)

        


@app.post("/chat")
def chat(query: UserQuery) -> UserResponse:
    
    rand = random.random()
    
    # 1 percent internal server error
    if rand < 0.01:
        raise HTTPException(status_code=500, detail="Internal server error")
    
    # 2 percent timeout error (wait for 1 minute before responding)
    if rand < 0.03:
        time.sleep(60) # simulate a 1-minute delay
        raise HTTPException(status_code=504, detail="Gateway timeout")
    
    response = generate_mock_response(query.message)
    return response

