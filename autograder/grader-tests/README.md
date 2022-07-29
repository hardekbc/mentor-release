# To Test the Autograder

1. Create the autograder using **test-solutions/*** as the contents of **solutions/**.

2. Create an assignment on Gradescope using that autograder.

3. Submit everything in **test-submissions/***.

4. Compare the actual results against the expected results below (a crash is never expected and indicates a problem in the grader script).

5. The above steps won't test how the grader script handles the cooldown period. To test that, within the cooldown period after step (3) submit everything in **test-later-submissions/***. Expected results:

   - test1 should come back with a cooldown error.
   - test3 should be graded as correct (because it had a syntax error in the previous version which has now been fixed, and erroneous submissions don't count against the cooldown).
   - test2, test4, test5, test6, test8, test9, test10, test11, test15 should all come back graded as correct/incorrect as before (because if a test wasn't submitted this time but was previously graded without errors, the grader re-uses the previous results).

6. After the cooldown period from step (3) is over but before the cooldown period for step (5) is over, submit test1.dfa again. Expected results:

   - test1 should come back graded as correct (because submitting again during the cooldown period shouldn't reset the cooldown).

# Tip For Debugging the Grader Script

If you're getting a lot of Python script errors, running it through Gradescope every time can be a huge pain. Instead, you can copy 'grader.py' to this directory (rename it 'test-grader.py' to avoid confusion) and make the following changes:

1. Change the value of 'result_file' to "./results.json"
2. Change the value of 'student_submission_dir' to "./test-submissions/"
3. Change the value of 'solution_dir' to "./test-solutions/"
4. Change the value of 'mentor' to "../mentor"
5. Change the value of 'metadata' to {'created_at': "2018-07-01T14:22:32.365935-07:00", 'previous_submissions': []}

Now run ./test-grader.py and debug until it works without script errors, then import those bug fixes to the actual 'grader.py' (deleting 'test-grader.py' to avoid future confusion) and go back to testing on Gradescope.

# Expected Results For Steps 1--4

These tests should be graded as correct:

- test1
- test4
- test8
- test9
- test15
- test17

These tests should graded as incorrect:

- test2
- test5
- test6
- test10
- test11

These tests should yield an error message about the submitted file:

- test3
- test7
- test12
- test13
- test14
- test16
- test19

These tests should yield an error message about the solution file:

- test18
- test20
- test21
- test22
- test23
- test24
- test25
- test26

# Test Descriptions

### DFA/NFA/RE

- TEST1 correct submission
- TEST2 incorrect submission
- TEST3 mentor error

### CFG/PDA

- TEST4 correct submission
- TEST5 incorrect submission, false positives
- TEST6 incorrect submission, false negatives
- TEST7 mentor error (student)
- TEST20 mentor error (solution)

### TM/HTM

- TEST8 correct submission
- TEST9 correct submission, testing empty string input
- TEST10 incorrect submission (including timeout)
- TEST11 max timeouts
- TEST12 mentor error (student)
- TEST15 solution with empty accept, empty reject
- TEST21 invalid solution format

### MISC

- TEST13 invalid submission filename
- TEST14 invalid submission filetype
- TEST16 submission with no matching solution
- TEST17 submission for cfg/pda with two solutions in different formats
- TEST18 submission with multiple matching solutions
- TEST19 mismatching language classes
- TEST22--25 invalid solution filename (one per format)
- TEST26 invalid solution filetype
