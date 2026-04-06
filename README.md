# 🎓 Smart Academic Advisor System (GPA Goes Up)

## 📌 Overview

The **Smart Academic Advisor System** is an intelligent web-based platform designed to help university students make optimal academic decisions.
It analyzes a student's academic record, applies official university regulations, and provides personalized course recommendations to maximize GPA and achieve academic goals efficiently.

The system combines:

* 📊 Rule-based academic logic (university regulations)
* 🤖 Machine Learning predictions
* 💬 AI-powered chatbot assistance
* 📈 Interactive data visualization

---

## 🎯 Problem Statement

Students often struggle with:

* Choosing the right courses each semester
* Understanding prerequisites and academic rules
* Improving their GPA efficiently
* Planning long-term academic goals

This system solves these problems by providing **data-driven, personalized recommendations**.

---

## 🚀 Key Features

### 1. 📂 Academic Record Processing

* Upload academic record as **PDF (Arabic)**
* Extract:

  * Courses
  * Grades
  * GPA
  * Credit hours
* Convert data into structured format for analysis

---

### 2. ⚙️ Rule-Based Academic Engine

Implements official university regulations such as:

* Prerequisites handling
* Credit hour limits based on GPA
* Retake courses policies
* Course eligibility determination

---

### 3. 🎯 Course Recommendation System

After processing the student record, the system:

* Suggests **recommended courses**
* Provides **alternative options**
* Assigns a **score for each course** based on:

  * Student performance
  * Course difficulty
  * Similar students' history

---

### 4. 📊 GPA Calculator

#### 🔹 Semester GPA Calculator

* Input courses, grades, and credit hours
* Calculate semester GPA instantly

#### 🔹 Cumulative GPA Calculator

* Combine previous GPA with current semester
* Compute updated CGPA

---

### 5. 📈 GPA Simulator

* Visualizes GPA progression across semesters
* Displays trend line of academic performance
* Predicts future GPA based on selected courses
* Allows students to:

  * Modify course selection
  * See impact on GPA in real-time

---

### 6. 🎯 Target GPA Predictor

* Input desired GPA target
* System calculates:

  * Required GPA per semester
  * Number of semesters needed
  * Suggested credit load per semester

---

### 7. 🤖 AI Chatbot Assistant

Provides:

* Explanation of recommendations
* Academic advice
* Suggested questions
* Interactive support for decision-making

---

### 8. 📊 Data Visualization

* GPA trends over semesters
* Performance insights
* Future projections

---

## 🤖 Machine Learning Components

The system uses ML to:

### ✔️ Course Scoring

Predict how suitable each course is for the student based on:

* Academic history
* Performance in similar subjects
* Patterns from similar students

---

### ✔️ GPA Prediction

Estimate expected GPA for:

* Selected courses
* Future semesters

---

### ✔️ Student Pattern Analysis

* Identify similar student profiles
* Use historical patterns of the student to improve recommendations

---

## 🧠 Data Strategy

Due to limited real student data:

* Data of courses and prerequests courses is used as base
* Small real student data is used
* Synthetic data is generated to simulate large-scale student data to use to train the machien learning
* ML models are trained on this enriched dataset

---

## ⚙️ System Workflow

1. Student uploads academic record (PDF)
2. System extracts and processes data
3. Rule Engine determines:

   * Eligible courses
   * Credit limits
4. ML model scores and ranks courses
5. System displays:

   * Recommended courses
   * Alternatives
   * Scores
6. Student can:

   * Use GPA tools
   * Simulate outcomes
   * Set GPA targets
   * Ask chatbot for explanations

---

## 🖥️ User Interface Flow

### 🟢 Step 1:

* Upload academic record (PDF)
* Select semester

### 🟢 Step 2:

* View recommended courses + scores
* See alternatives

### 🟢 Step 3:

Choose one of:

* GPA Calculator
* GPA Simulator
* Target GPA

### 🟢 Step 4:

* Use chatbot for explanations (“Explain Results”)

---


## 📌 Future Improvements

* Integration with real university systems
* More accurate ML models with real data
* Personalized academic planning dashboards

---

## 🎯 Target Users

* University students (credit hour systems)
* Especially students aiming to:

  * Improve GPA
  * Plan academic paths
  * Optimize course selection

---

## 💡 Project Vision

To build a **smart academic assistant** that transforms complex academic decisions into simple, data-driven recommendations — helping students achieve their goals faster and more efficiently.

---
