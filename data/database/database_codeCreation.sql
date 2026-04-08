-- Create Database
CREATE DATABASE gpa_goes_database;

-- Use Database
USE gpa_goes_database;

-- STUDENT Table
CREATE TABLE Student (
    ID INT PRIMARY KEY,
    CGPA FLOAT,
    Program VARCHAR(100),
    Earned_Hours INT,
    Last_Semester_GPA FLOAT,
    Level INT,
    Admission_Year INT
);

-- COURSE Table
CREATE TABLE Course (
    Code VARCHAR(20) PRIMARY KEY,
    Type VARCHAR(10),
    Credit_Hours INT,
    Is_elective VARCHAR(20),
    Is_practical VARCHAR(20)
);

-- ENROLLMENT Table
CREATE TABLE Enrollment (
    Enrollment_ID INT PRIMARY KEY,
    Course_GPA FLOAT,
    Course_Code VARCHAR(20),
    Student_ID INT,
    Year INT,
    Semester VARCHAR(20),

    FOREIGN KEY (Course_Code) REFERENCES Course(Code),
    FOREIGN KEY (Student_ID) REFERENCES Student(ID)
);

-- PREREQUISITE Table
CREATE TABLE Prerequisite (
    Course_Code VARCHAR(20),
    Prerequisite_Course_Code VARCHAR(20),

    PRIMARY KEY (Course_Code, Prerequisite_Course_Code),

    FOREIGN KEY (Course_Code) REFERENCES Course(Code),
    FOREIGN KEY (Prerequisite_Course_Code) REFERENCES Course(Code)
);