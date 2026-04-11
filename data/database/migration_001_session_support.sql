-- migration_001_session_support.sql
-- Required for feature 001-pdf-transcript-parsing: session-scoped storage.
-- Run AFTER database_codeCreation.sql.

USE gpa_goes_database;

-- Add AUTO_INCREMENT and session tracking to Student
ALTER TABLE Student
    MODIFY COLUMN ID INT NOT NULL AUTO_INCREMENT,
    ADD COLUMN session_id VARCHAR(64) NULL AFTER Admission_Year;

-- Add AUTO_INCREMENT and Course_Grade to Enrollment
ALTER TABLE Enrollment
    MODIFY COLUMN Enrollment_ID INT NOT NULL AUTO_INCREMENT,
    ADD COLUMN Course_Grade VARCHAR(10) NULL AFTER Course_Code;

-- Index for fast session-scoped cleanup
CREATE INDEX idx_student_session ON Student(session_id);
