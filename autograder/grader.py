#!/usr/bin/env python3

import re
import json
import subprocess
import os.path
import numpy as np
from datetime import datetime
from os import listdir
from os.path import isfile, join
from typing import Dict, List, TextIO, Any, Tuple

# the output that the grader needs to create, and where the grader output needs
# to go for gradescope to see. format (ignoring optional fields that we don't
# need):
#
# {
#   'tests': [
#     {
#       'name': <problem-id>,
#       'score': <score>,
#       'output': <message to student>,
#       'extra_data': { 'graded': <bool> } // was this actually graded?
#     },
#     ...
#   ]
# }
#
# each test case corresponds to one homework problem.
results_file = "/autograder/results/results.json"

# where the student's submitted files are located, provided by gradescope. not
# all files need to be submitted every time; if a file is missing then we re-use
# its previous score (or 0 if it hasn't been previously submitted).
#
# submitted files are assumed to be named "<problem-id>.{dfa, nfa, re, cfg, pda,
# tm, htm}", where <problem-id> should not contain any '.'.
student_submission_dir = "/autograder/submission/"

# where the homework problem solutions are located, provided by the instructors.
# there should be one file per problem, named using one of the following formats
# (where <problem-id> should not contain any '.'):
#
# 1. <problem-id>.<point-value>.{dfa, nfa, re}
# 2. <problem-id>.<point-value>.<num-words>.{cfg, pda}
# 3. <problem-id>.{cfg, pda}.wordlist
# 4. <problem-id>.<point-value>.<max-steps>.{tm, htm}.wordlist
#
# within a language class the type of solution does not need to match the type
# of the student submission; that is, for regular languages the solution can be
# any of {dfa, nfa, re}, for context-free languages the solution can be any of
# {cfg, pda}, and for unrestricted languages the solution can be any of {tm,
# htm}, regardless of what the students are supposed to turn in.
#
# all formats except format (3)---to be discussed below---contain <point-value>
# (assumed to be an integer) that sets the point value for <problem-id>.
#
# format (1) is for regular language problems. regular languages can be directly
# compared for equality, so the grader checks whether the submission and
# solution are equivalent.
#
# formats (2) and (3) are for context-free language problems. context-free
# languages cannot be compared for equality, instead we generate the first N
# words in the language (in shortlex order) for the solution and for the student
# submission and compare them. format (2) contains <num-words> (assumed to be an
# integer) which tells the autograder how many words to generate. in order to
# avoid having to generate the solution wordlist over and over again, we can
# optionally have an additional file in format (3) that contains a pre-generated
# wordlist. This must be in addition to the actual CFG/PDA in format (2), not
# instead of (because we need the actual solution to correctly provide feedback
# for an incorrect student submission). If the format (2) file specifies a
# different number of words than given in the format (3) file, the grader will
# use the number of words in the format (3) file.
#
# format (4) is for unrestricted language problems, which also cannot be
# compared for equality nor can they generate words. instead, the solution file
# contains the following contents:
#
#    ## ACCEPT ##
#    <list of inputs that should be accepted, separated by newlines>
#    ## REJECT ##
#    <list of inputs that should be rejected, separated by newlines>
#
# the header lines must be exactly "## ACCEPT ##" and "## REJECT ##" with no
# additional whitespace, and there should not be any blank lines between the end
# of the accept list and the header for the reject list. both headers must be
# present even if one of the lists is empty.
#
# format (4) contains <max-steps> (assumed to be an integer) which is the number
# of computational steps to allow before timeout. the autograder checks each
# provided input on the student submission to see if the submission gives the
# appropriate result.
solution_dir = "/autograder/source/solutions/"

# metadata about the student's submissions, provided by gradescope. format
# (ignoring fields we don't care about):
#
# {
#   'created_at': "2018-07-01T14:22:32.365935-07:00", // submission time
#   'previous_submissions': [
#     {
#       'submission_time': "2017-04-06T14:24:48.087023-07:00", // previous submission time
#       'results': { ... } // previous submission results object
#     },
#     ...
#   ]
# }
submission_metadata_file = "/autograder/submission_metadata.json"

# the mentor executable, provided by the instructors.
mentor = "/autograder/source/mentor"

# the desired cooldown period between allowed submissions (per homework
# problem), in minutes.
cooldown = 30

# the submitted files in 'student_submission_dir'.
submitted_files = [file for file in listdir(student_submission_dir) if
                   isfile(join(student_submission_dir, file))]

# the solutions present in 'solution_dir'.
solution_files = [file for file in listdir(solution_dir) if
                  isfile(join(solution_dir, file))]

# the submission metadata from 'submission_metadata_file'.
metadata = json.loads(open(submission_metadata_file).read())

# the metadata for previous submissions can have submissions in an arbitrary
# order (i think), and some of those submission may have results for a problem
# that wasn't actually graded (e.g., it automatically got a 0 because the
# student didn't submit that particular problem). to make things easier, we'll
# process the metadata into a format that summarizes everything necessary and is
# easily accessible by problem-id:
#
# {
#   <problem-id>: {
#     'elapsed-time': <minutes> // minutes since this problem was last graded
#     'previous-score': <score> // previous score
#   },
#   ...
# }
#
# if a problem was not graded in some previous submission then an entry for its
# problem id won't exist in previous_info.
previous_info: Dict[str, Dict[str, int]] = {}

# stores the results of grading in a way that makes it easy to look up by
# problem-id. format:
#
# { <problem-id>: {
#     'score': <int>,
#     'output': <message to student>
#     'graded': <bool>
#   },
#   ...
# }
grades = {}

# convert a string containing time information into a datetime object. the
# expected format is as given in the second argument to strptime.
def GetTimeFromString(time_string) -> datetime:
    return datetime.strptime(time_string.split('.')[0], "%Y-%m-%dT%H:%M:%S")


# return the solution filename matching the given problem id. if there is no
# matching solution returns "no matching solution". if there are two matching
# files, one in format (2) and one in format (3), returns the one in format (2).
# other than that case, if there are multiple matching files returns "multiple
# matching solutions".
def FindMatchingSolutionFile(problem_id: str) -> str:
    solutions = [soln for soln in solution_files if soln.split('.')[0] == problem_id]
    if len(solutions) == 0: return "no matching solution"
    if len(solutions) == 1: return solutions[0]
    if len(solutions) == 2:
        if "wordlist" in solutions[0]: return solutions[1]
        return solutions[0]
    return "multiple matching solutions"


# return the language class of the give file type: regular, context-free, or
# unrestricted.
def LanguageClass(file_type: str) -> str:
    regular = ["dfa", "nfa", "re"]
    context_free = ["cfg", "pda"]
    unrestricted = ["tm", "htm"]
    if file_type in regular: return "regular"
    if file_type in context_free: return "context-free"
    if file_type in unrestricted: return "unrestricted"
    return "unknown"


# parse the name of the problem file to retrieve its embedded information.
# Returns a record in the format:
#
# { 'file': "</path/to/file>"
#   'file-type': "<{dfa, nda, re, cfg, pda, tm, htm}>"
#   'id': "<problem-id>"
# }
#
# returns an empty dictionary {} if the filename was not in the correct format
# or it couldn't read the file.
def GetProblemInfo(problem_file: str):
    pieces = problem_file.split('.')
    if len(pieces) != 2: return {}
    return {'file': student_submission_dir + problem_file,
            'file-type': pieces[1], 'id': pieces[0]}


# parse the name of the solution file to retrieve its embedded information and
# read the contents of the solution file if necessary. Returns one of three
# record formats:
#
# { 'file': "</path/to/file>"
#   'file-type': "<{dfa, nfa, re}>",
#   'point-value': <int>,
# }
#
# { 'file': "</path/to/file>"
#   'file-type': "<{cfg, pda}>",
#   'point-value': <int>,
#   'num-words': <int>,
#   'wordlist': "<list of words>" // present only if solution is a wordlist.
# }
#
# { 'file': "</path/to/file>"
#   'file-type': "<{tm, htm}>",
#   'point-value': <int>,
#   'max-steps': <int>,
#   'accept': <list of inputs to accept>,
#   'reject': <list of inputs to reject>
# }
#
# returns an empty dictionary {} if the filename was not in the correct format
# or it couldn't read the file.
def GetSolutionInfo(solution_file: str):
    pieces = solution_file.split('.')

    # <problem-id>.<point-value>.{dfa, nfa, re}
    if len(pieces) == 3 and LanguageClass(pieces[2]) == "regular":
        if not pieces[1].isdigit(): return {}
        return {'file': solution_dir + solution_file, 'file-type': pieces[2],
                'point-value': int(pieces[1])}

    # <problem-id>.<point-value>.<num-words>.{cfg, pda}
    if len(pieces) == 4 and LanguageClass(pieces[3]) == "context-free":
        if not pieces[1].isdigit() or not pieces[2].isdigit(): return {}
        info = {'file': solution_dir + solution_file, 'file-type': pieces[3],
                'point-value': int(pieces[1]), 'num-words': int(pieces[2])}

        # see if there is a wordlist available (if there is more than one, just
        # ignore them all). if the wordlist has a different number of words than
        # specified by <num-words>, that overrides the specified value.
        files = [f for f in solution_files if f.split('.')[0] == pieces[0]
                    and f.endswith(".wordlist")]
        if len(files) == 1:
            with open(solution_dir + files[0], 'r') as handle:
                words = handle.read()
            info['wordlist'] = words.splitlines()
            info['num-words'] = len(info['wordlist'])

        return info

    # <problem-id>.<point-value>.<max_steps>.{tm, htm}.wordlist
    if len(pieces) == 5 and LanguageClass(pieces[3]) == "unrestricted":
        if not pieces[1].isdigit() or not pieces[2].isdigit() or \
           pieces[4] != "wordlist": return {}

        # get wordlist from file.
        words = ""
        with open(solution_dir + solution_file, 'r') as handle:
            words = handle.read()
        wordlist = words.splitlines()

        # sanity checks.
        if not wordlist or wordlist[0] != "## ACCEPT ##" or \
           "## REJECT ##" not in wordlist: return {}
        wordlist = wordlist[1:]

        # split into separate accept and reject lists.
        reject_hdr_idx = wordlist.index("## REJECT ##")
        accept = wordlist[:reject_hdr_idx]
        reject = wordlist[reject_hdr_idx+1:]

        return {'file': solution_dir + solution_file, 'file-type': pieces[3],
                'point-value': int(pieces[1]), 'max-steps': int(pieces[2]),
                'accept': accept, 'reject': reject}

    # no pattern matched.
    return {}


# store the result for a problem id in 'grades'.
def StoreGrade(problem_id: str, score: int, msg: str, graded: bool) -> None:
    # verify that this problem id hasn't already had a grade stored.
    assert not problem_id in grades
    grades[problem_id] = {'score': score, 'output': msg, 'graded': graded}


# run the given mentor command. returns a pair s.t. the boolean indicates
# whether the command terminated normally (True) or not (False) and the string
# contains the output of the command. if the command did not terminate normally,
# it stores an appropriate grade for the problem id.
def RunMentor(problem_id: str, mentor_cmd: List[str]) -> Tuple[bool, str]:
    proc = subprocess.run(mentor_cmd, stdout = subprocess.PIPE, \
                          stderr = subprocess.PIPE)
    output = (proc.stdout + b'\n' + proc.stderr).decode('utf-8')
    if proc.returncode != 0: # error
        StoreGrade(problem_id, 0, f"Mentor terminated abnormally on command '{mentor_cmd}':\n{output}", False)
        return (False, output)
    else:
        return (True, output)


# grade a problem involving regular languages. fills in an appropriate entry in
# 'grades' for the given problem id. assumes problem_info comes from
# GetProblemInfo() and solution_info comes from GetSolutionInfo(), and hence are
# in the expected formats.
def GradeRegular(problem_info, solution_info) -> None:
    assert LanguageClass(problem_info['file-type']) == "regular" and \
        LanguageClass(solution_info['file-type']) == "regular"

    problem_id = problem_info['id']
    ok, output = RunMentor(problem_id, [mentor, problem_info['file'], "compare",
                                        solution_info['file']])

    if ok and "The languages are equivalent" in output:
        StoreGrade(problem_info['id'], solution_info['point-value'],
                   f"Correct (points = {solution_info['point-value']})", True)
    elif ok:
        StoreGrade(problem_info['id'], 0, "Incorrect (points = 0):\n" + output, True)


# grade a problem involving context-free languages. fills in an appropriate
# entry in 'grades' for the given problem id. assumes problem_info comes from
# GetProblemInfo() and solution_info comes from GetSolutionInfo(), and hence are
# in the expected formats.
def GradeContextFree(problem_info, solution_info) -> None:
    assert LanguageClass(problem_info['file-type']) == "context-free" and \
        LanguageClass(solution_info['file-type']) == "context-free"

    # get student wordlist.
    problem_id = problem_info['id']
    ok, output = RunMentor(problem_id, [mentor, problem_info['file'], "gen_words",
                                        str(solution_info['num-words'])])
    if not ok: return
    student_wordlist = output.splitlines()

    # get solution wordlist.
    if 'wordlist' in solution_info:
        solution_wordlist = solution_info['wordlist']
    else:
        ok, output = RunMentor(
            problem_id, [mentor, solution_info['file'], "gen_words",
                         str(solution_info['num-words'])])
        if not ok: return
        solution_wordlist = output.splitlines()

    # compute differences between student and solution. false positives are
    # words in the student list that aren't in the solution; false negatives are
    # words in the solution that aren't in the student list.
    false_positives = np.setdiff1d(student_wordlist, solution_wordlist)
    false_negatives = np.setdiff1d(solution_wordlist, student_wordlist)

    # student solution is exactly correct.
    if len(false_positives) == 0 and len(false_negatives) == 0:
        StoreGrade(problem_info['id'], solution_info['point-value'],
                   f"Correct (points = {solution_info['point-value']})", True)
        return

    # because we're only checking up to N words we have to account for some
    # potential weirdness. if the student submission generated incorrect words
    # it may have pushed some correct words outside the N-limit and hence it
    # looks like they are false negatives but really aren't. similarly, if the
    # student submission didn't generate some correct words it may have pulled
    # some other correct words inside the N-limit and hence it looks like they
    # are false positives but really aren't. we're guaranteed that at least one
    # word in one of false_positives/false_negatives is incorrect, but we have
    # to search through them all to see which ones are really incorrect.

    # find the first false positive that's really a false positive (if any). we
    # verify this by calling mentor again and asking whether the solution
    # accepts the word; if so then it isn't really a false positive.
    real_false_positive = None
    for word in false_positives:
        ok, output = RunMentor(problem_id, [mentor, solution_info['file'],
                                            "accept", word])
        if not ok: return
        if "Input is not accepted" in output:
            real_false_positive = word if word != "" else "ε"
            break;

    # find the first false negative that's really a false negative (if any). we
    # verify this by calling mentor again and asking whether the student
    # submission accepts the word; if so then it isn't really a false negative.
    real_false_negative = None
    for word in false_negatives:
        ok, output = RunMentor(problem_id, [mentor, problem_info['file'],
                                            "accept", word])
        if not ok: return
        if "Input is not accepted" in output:
            real_false_negative = word if word != "" else "ε"
            break;

    # construct the feedback to the student and store their grade.
    msg = "Incorrect (points = 0):\n";
    if real_false_negative != None:
        msg += f"The word {real_false_negative} should be accepted.\n"
    if real_false_positive != None:
        msg += f"The word {real_false_positive} should be rejected.\n"
    StoreGrade(problem_info['id'], 0, msg, True)


# grade a problem involving unrestricted languages. fills in an appropriate
# entry in 'grades' for the given problem id. assumes problem_info comes from
# GetProblemInfo() and solution_info comes from GetSolutionInfo(), and hence are
# in the expected formats.
def GradeUnrestricted(problem_info, solution_info) -> None:
    assert LanguageClass(problem_info['file-type']) == "unrestricted" and \
        LanguageClass(solution_info['file-type']) == "unrestricted"

    problem_id = problem_info['id']

    # we have to account for timeouts too; we'll use the first timeout
    # wncountered as the student feedback. to avoid having too many timeouts
    # take up all our cycles, we'll set a limit for the number of timeouts and
    # stop grading when that limit is exceeded.
    num_timeouts = 0
    max_timeouts = 10
    timedout_word = None

    # run accept wordlist on student submission, stopping at the first mistake.
    incorrect_rejection = None
    for word in solution_info['accept']:
        ok, output = RunMentor(problem_id,
                               [mentor, problem_info['file'], "accept", word,
                                str(solution_info['max-steps'])])
        if not ok: return
        if "Computation timed out" in output:
            num_timeouts = num_timeouts + 1
            if num_timeouts > max_timeouts:
                StoreGrade(problem_info['id'], 0, f"Grading stopped: too many inputs timed out. One such input is: {timedout_word}", True)
                return
            if timedout_word == None: timedout_word = word if word != "" else "ε"
        elif "Input is not accepted" in output:
            incorrect_rejection = word if word != "" else "ε"
            break;

    # run reject worklist on student submission, stopping at the first mistake.
    incorrect_acceptance = None
    for word in solution_info['reject']:
        ok, output = RunMentor(problem_id,
                               [mentor, problem_info['file'], "accept", word,
                                str(solution_info['max-steps'])])
        if not ok: return
        if "Computation timed out" in output:
            num_timeouts = num_timeouts + 1
            if num_timeouts > max_timeouts:
                StoreGrade(problem_info['id'], 0, f"Grading stopped: too many inputs timed out. One such input is: {timedout_word}", True)
                return
            if timedout_word == None: timedout_word = word if word != "" else "ε"
        elif "Input is accepted" in output:
            incorrect_acceptance = word if word != "" else "ε"
            break;

    # compute feedback and grade.
    if incorrect_rejection == None and incorrect_acceptance == None and timedout_word == None:
        StoreGrade(problem_info['id'], solution_info['point-value'],
                   f"Correct (points = {solution_info['point-value']})", True)
    else:
        msg = "Incorrect (points = 0):\n"
        if incorrect_rejection != None:
            msg += f"The word {incorrect_rejection} should be accepted.\n"
        if incorrect_acceptance != None:
            msg += f"The word {incorrect_acceptance} should be rejected.\n"
        if timedout_word != None:
            msg += f"The word {timedout_word} exceeds the maximum number of allowed steps.\n"
        StoreGrade(problem_info['id'], 0, msg, True)


# get the current submission time.
now = GetTimeFromString(metadata['created_at'])

# fill in 'previous_info' with the information about previous submissions.
for submission in metadata['previous_submissions']:
    # elapsed time since previous submission, in minutes.
    elapsed_time = int(
        (now - GetTimeFromString(submission['submission_time'])).total_seconds() // 60)

    if not 'tests' in submission['results']: continue

    for problem in submission['results']['tests']:
        problem_id = problem['name']
        if problem['extra_data']['graded'] != True:
            continue
        if problem_id in previous_info and \
           previous_info[problem_id]['elapsed-time'] < elapsed_time:
            continue
        previous_info[problem_id] = {'elapsed-time': elapsed_time,
                                     'previous-score': int(problem['score'])}

# the main computation loop: iterate through the submitted problems and grade
# them as appropriate.
for problem_file in submitted_files:
    problem_info = GetProblemInfo(problem_file)
    if not problem_info:
        StoreGrade(problem_file, 0, f"Invalid submitted file: {problem_file}", False)
        continue

    problem_id = problem_info['id']

    # if this problem is in cooldown, re-use the previous score instead of
    # grading it again.
    if problem_id in previous_info and \
       previous_info[problem_id]['elapsed-time'] <= cooldown:
        time_remaining = cooldown - previous_info[problem_id]['elapsed-time']
        StoreGrade(problem_id, previous_info[problem_id]['previous-score'], f"Cooldown still in effect for this problem; {time_remaining} minutes remaining.", False)
        continue

    # find the solution file for this problem (handling any errors).
    solution_file = FindMatchingSolutionFile(problem_id)
    if solution_file == "no matching solution":
        StoreGrade(problem_id, 0, "There is no matching solution for this problem", False)
        continue
    if solution_file == "multiple matching solutions":
        StoreGrade(problem_id, 0, "There are conflicting solutions for this problem", False)
        continue

    solution_info = GetSolutionInfo(solution_file)
    if not solution_info:
        StoreGrade(problem_id, 0, f"Invalid solution file: {solution_file}", False)
        continue

    # we could now check whether this problem was already graded and received
    # the maximum point-value and if so not bother grading it again, but this
    # would be a mistake. the problem occurs when the initially provided
    # solution is incorrect (which realistically does happen), the student
    # receives maximum points (incorrectly because of the wrong solution), the
    # solution is updated to be correct, and now the student needs to resubmit
    # and get an updated score. if we add this check, the student wouldn't get
    # an updated score for the updated solution.

    # verify that the submitted problem and the solution are compatible, i.e.,
    # belong to the same language class.
    problem_type = problem_info['file-type']
    solution_type = solution_info['file-type']
    if LanguageClass(problem_type) != LanguageClass(solution_type):
        StoreGrade(problem_id, 0, f"The submitted problem is type {problem_type}, but the solution is type {solution_type}", False)
        continue

    # grade the problem based on what type it is.
    if LanguageClass(problem_type) == "regular":
        GradeRegular(problem_info, solution_info)
    elif LanguageClass(problem_type) == "context-free":
        GradeContextFree(problem_info, solution_info)
    else: # must be unrestricted.
        GradeUnrestricted(problem_info, solution_info)

# if there are any problems that were previously graded but not submitted this
# time, give them their previous scores.
for problem_id in previous_info:
    if not problem_id in grades:
        StoreGrade(problem_id, previous_info[problem_id]['previous-score'],
                   f"Problem not submitted, using previous score: {previous_info[problem_id]['previous-score']}", False)

# the datastructure to be written out to 'results_file'.
results: Dict[str, List[Dict[str, Any]]] = {
  'tests': []
}

# fill in 'results' from 'grades'.
for problem_id in grades:
    results['tests'].append(
        {'name': problem_id,
         'score': grades[problem_id]['score'],
         'output': grades[problem_id]['output'],
         'extra_data': { 'graded': grades[problem_id]['graded'] }
        })

# write out the final results.
with open(results_file, 'w') as out:
    out.write(json.dumps(results))
