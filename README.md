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
  * Student data
* Convert data into structured format for analysis, put it into MYSQL's database

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
  * student's history

---

### 4. 📊 GPA Calculator

#### 🔹 Semester GPA Calculator

* Input courses, grades, and credit hours
* Calculate semester GPA instantly

#### 🔹 Cumulative GPA Calculator

* Has two options: Auto fill from acdemic records from the data base, or enter required data
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
* Select from two options: Auto fill from acdemic records from the data base, or enter required data
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

## 🤖 Machine Learning Components

The system uses ML to:

### ✔️ Course Scoring

Predict how suitable each course is for the student based on:

* Student's academic history 
* Performance in similar subjects

---

### ✔️ GPA Prediction

Estimate expected GPA for:

* Selected courses
* Future semester

---

### ✔️ Student Pattern Analysis

* Use historical patterns of the student to improve recommendations

---

## 🧠 Data Strategy


* Data of courses and prerequests courses is used as base
* Small real student data is used
* ML models are trained on this Small real student

---

## ⚙️ System Workflow

1. Student uploads academic record (PDF)
2. System extracts, processes data, and save it in session based student object
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
   * Set GPA calculator
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
