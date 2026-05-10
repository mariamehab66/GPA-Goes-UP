-- Create Database
CREATE DATABASE IF NOT EXISTS gpa_goes
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- Use Database
USE gpa_goes;

-- 1. STUDENT Table
CREATE TABLE Student (
    ID INT PRIMARY KEY AUTO_INCREMENT,
    CGPA DECIMAL(5,3),
    Program VARCHAR(100),
    Earned_Hours INT,
    Last_Semester_GPA DECIMAL(5,3),
    Level INT,
    Admission_Year INT
);

-- 2. COURSE Table (Updated with Course_Name, Level, and Semester)
CREATE TABLE Course (
    Code VARCHAR(20) PRIMARY KEY,
    Type VARCHAR(10),
    Course_Name VARCHAR(200),
    Credit_Hours DECIMAL(4,2),
    Is_elective BOOLEAN DEFAULT FALSE,
    Is_practical BOOLEAN DEFAULT FALSE,
    Level INT,
    Semester VARCHAR(20) DEFAULT 'both'
);

-- 3. ENROLLMENT Table
CREATE TABLE Enrollment (
    Enrollment_ID INT PRIMARY KEY AUTO_INCREMENT,
    Course_GPA DECIMAL(5,3),
    Course_Code VARCHAR(20),
    Grade VARCHAR(5),
    Marks DECIMAL(6,2),
    Student_ID INT,
    Year VARCHAR(15),
    Semester VARCHAR(20),

    FOREIGN KEY (Course_Code) REFERENCES Course(Code) ON DELETE RESTRICT,
    FOREIGN KEY (Student_ID) REFERENCES Student(ID) ON DELETE CASCADE
);

-- 4. PREREQUISITE Table
CREATE TABLE Prerequisite (
    Course_Code VARCHAR(20),
    Prerequisite_Course_Code VARCHAR(20),

    PRIMARY KEY (Course_Code, Prerequisite_Course_Code),

    FOREIGN KEY (Course_Code) REFERENCES Course(Code) ON DELETE RESTRICT,
    FOREIGN KEY (Prerequisite_Course_Code) REFERENCES Course(Code) ON DELETE RESTRICT
);
