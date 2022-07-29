# Quick Start

1. Put the solutions into the **solutions/** directory in the proper formats (explained below).

2. Use the **zip-autograder.sh** script from this directory to zip up the autograder in the proper format.

3. Upload to Gradescope.

# Solution Formats

The solution files take different forms depending on the type of problem being graded. Each filename starts with `<problem-id>`, and the student submissions are assumed to use the same id. For example, if the problem id is `problem1a` and it is a DFA construction problem, then the solution might be named `problem1a.1.dfa` and the student submission should be named `problem1a.dfa`.

## Regular Language Solutions

The filename format is `<problem-id>.<point-value>.{dfa,nfa,re}`, where the problem id is any string that doesn't contain `.`, the point value is the number of points this problem is worth (an integer value), and the suffix says whether the solution file contains a Mentor DFA, NFA, or regular expression description.

EXAMPLE: `p1.5.nfa` is the solution for problem `p1`, worth 5 points, and in the form of an NFA.

## Context-Free Language Solutions

The filename format is `<problem-id>.<point-value>.<num-words>.{cfg,pda}`, where the problem id is any string that doesn't contain `.`, the point value is the number of points this problem is worth (an integer value), `<num-words>` is the number of words that should be used to check the student submission against the solition (an integer value), and the suffix says whether the solution file contains a Mentor CFG or PDA description.

EXAMPLE: `p2.1.1000.cfg` is the solution for problem `p2`, worth 1 point, using 1000 words to compare the solution against the submission, and in the form of a CFG.

Optionally, there can be a second solution file named `<problem-id>.{cfg,pda}.wordlist` which contains a pre-generated list of words from the solution. If present the autograder will use that pre-generated list instead of generating it from the solution every time. Note that this file must be _in addition to_ the actual solution, not instead of.

EXAMPLE: `p2.cfg.wordlist` would contain the words for `p2.1.1000.cfg` pre-generated from that solution.

## Unrestricted Language Solutions.

The filename format is `<problem-id>.<point-value>.<max-steps>.{tm,htm}.wordlist`, where the problem id is any string that doesn't contain `.`, the point value is the number of points this problem is worth (an integer value), `<max-steps>` is the maximum number of computation steps the student submission is allowed to run before being forced to terminate (an integer value), and the suffix (before `wordlist`) says whether the problem is for Turing machines or hierarchical Turing machines.

Unlike the regular and context-free solution files, the unrestricted solution files do not contain a Turing machine or hierarchical Turing machine description. Instead, they contain (1) a list of words that the student submission should accept; and (2) a list of words that the student submission should reject. The file format is:

> ```text
> ## ACCEPT ##
> <list of words separated by newlines>
> ## REJECT ##
> <list of words separated by newlines>
> ```

Note that an empty line corresponds to an empty string input. Both headers must be present even if their respective word list is empty.

EXAMPLE: `p3.10.10000.tm.wordlist` is the solution for problem `p3`; it should contain a list of words to accept/reject by the student submission (a Turing machine), and the grader will run the student submission on each word for no more than 10000 steps. The contents of the file might be:

> ```text
> ## ACCEPT ##
>
> 012
> 001122
> ## REJECT ##
> 01
> 00112
> 01122
> ```

(Note that the blank line after `## ACCEPT ##` means that the empty string should be accepted.)

# More Details

Some useful things to know about how the grader works.

## Cooldown

The autograder rate-limits student submissions per-problem. The default cooldown period is 30 minutes: for each problem, the student cannot submit that problem for feedback more than once every 30 minutes. The cooldown period can be adjusted by changing the 'cooldown' value in grader.py.

Students often ask for the cooldown period to be lowered or removed. We tell our students that the intent is for them to use the command-line Mentor executable to test their submissions (just like they would test a regular programming assignment) rather than try to use the autograder in a debugging loop. This forces the students to think about test cases and how their solution works rather than engage in "voodoo debugging" behavior.

While that's our philosophy, obviously other approaches are also valid. It is easy to remove the cooldown altogether if that is preferred.

## Assigning Points to a Student Submission

The autograder assigns either full credit (the student submission has no errors) or no credit (the student submission has at least one error). It might be nice to assign partial credit, but it isn't clear what that means for these kinds of problems. Consider a CFG construction problem: what does it mean for the student submission to be "almost" correct? The submission could be just a small edit distance away from a fully correct answer but still generate a very different list of words than the correct solution; alternatively a solution could exhibit a fundamental misunderstanding and still generate many of the right words.

Our experience is that since we give students immediate feedback on their submissions and let them resubmit as many times as they want (subject to the cooldown period), giving all-or-nothing credit works fine. In fact, having Mentor and the autograder available makes it feasible to assign more problems (and thus lower the impact of getting one of them wrong) than one otherwise might assign if they were going to be graded by hand.

## Student Feedback

For an incorrect submission, the autograder provides student feedback in the form of (1) a word in the desired language that the student submission fails to accept; and/or (2) a word not in the desired language that the student submission fails to reject.

This feedback, in our experience, strikes a good balance between being useful (providing the student with something concrete to investigate) but not revealing too much.

## Grading Regular Language Problems

Regular languages can be directly compared for equality. Thus, given an instructor solution the autograder determines using Mentor whether the student submission is fully equivalent to the solution or not.

## Grading Context-Free Language Problems

Context-free languages cannot be directly compared for equality (as is usually proven at some point in this course). To judge a student submission, the autograder generates the first N words of the language in shortlex order for both the student submission and the instructor solution and then compares them. There is a balance between performance and number of generated words, but we advise generating at least 1,000 words for comparison otherwise for some languages there may not be enough words to expose student errors.

There is one subtlety that the autograder needs to contend with due to this strategy of comparing the first N words. Suppose the student solution is incorrect in one of the following ways:

- It generates a proper subset of the desired language. Then the first N words may contain words that do belong to the desired language but are not present in the instructor solution (because they shouldn't actually be in the first N words). These words look like incorrect words to the autograder because they aren't in the solution's wordlist, but it would be incorrect to flag them as wrong to the student.

- It generates a proper superset of the desired language. Then the first N words may be missing words that belong to the desired language, but the student submission would actually generate those words eventually. These words look like the student submission is missing them to the autograder because they are in the solution's wordlist but not the submission's wordlist, but it would be incorrect to flag them as missing to the student.

To account for this issue, the autograder checks each "extra" word from the student submission against the instructor solution (not the wordlist but the actual solution) to see if the "extra" word is actually in the desired language; if so then the autograder won't flag it as wrong. It also checks each "missing" word from the solution's wordlist against the student submission (again, the actual submission not the wordlist) to see if it is actually in the submission's language; if so then the autograder won't flag it as missing. Note that if this issue comes up it means the student submission is definitely incorrect and contains at least one extra and/or missing word, all of this machinery is just to make sure that we give the _right_ words as feedback to the student.

## Grading Unrestricted Language Problems

Unrestricted languages cannot be directly compared for equality nor can we generate words from the language description. Instead, we have the instructor prepare (1) a list of words that should be accepted; and (2) a list of words that should be rejected. The idea is that the instructor would program something in their favorite language that can easily generate such words, rather than come up with them manually (though it might not be a bad idea to manually add some interesting edge cases). Then the autograder gives each word as input to the student submission and checks whether it accepts or rejects the word as appropriate. The autograder also gives each computation a maximum number of steps to complete (a "timeout" threshold) and treats a timeout as an error. If there are too many timeouts (configurable in grader.py) then the autograder will stop trying to grade the submission altogether and just return a timeout error.

# Testing the Autograder

If you change the grader script `grader.py` you'll probably want to test it. The **grader-tests/README.md** file contains some examples and tips on how to test the grader.
