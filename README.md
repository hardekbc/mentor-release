# Introduction

This is the release of the Mentor educational tool for automatically grading and giving student feedback for problems in a Computer Science course on Automata and Formal Languages. It handles deterministic and nondeterministic finite automata, regular expressions, context-free grammars, pushdown automata, Turing machines, and hierarchical Turing machines. See **docs/** for more information on its capabilities and how to use it.

Why no source code? The Mentor code implements a number of algorithms that are taught during a course on Automata and Formal Languages (e.g., NFA to DFA conversion, DFA minimization, PDA to CFG conversion, etc). Instructors often use these algorithms as the subject of homework and exam questions, and so we feel that releasing the source code would be doing those instructors a disservice. If you are a Computer Science educator who is interested in contributing to the Mentor codebase, please contact [Prof. Ben Hardekopf](https://hardekbc.github.io).

# Student-Facing Executable

In order for students to be able to use the Mentor executable (currently available for x86 Linux boxes), simply copy the contents of the **app/** directory somewhere that the students have executable access and have them run the **app/mentor** script. The **app/lib** directory contains several shared libraries that the Mentor executable depends on, and the **app/mentor** script puts those libraries in LD_LIBRARY_PATH before running the executable. If your platform already has those libraries available then all you need is the actual Mentor executable **app/bin/mentor-cli**.

Running mentor without any arguments will output a usage message. You also probably want to make the Mentor documentation in **docs/** available to the students.

# Gradescope Autograder

The **autograder/** directory contains a complete Gradescope autograder setup. Instructors simply put problem solutions in the **solutions/** directory and upload the autograder to Gradescope. Students then get immediate feedback about their submissions each time they submit (with a default 30-minute per-problem cooldown period between submissions).

The details for how to use the autograder are in **autograder/README.md**.

# Contributors

Mentor is the brainchild of [Prof. Ben Hardekopf](https://hardekbc.github.io) and the UC Santa Barbara Computer Science Department's Programming Languages Lab. Several graduate and undergraduate students have contributed over the years (in alphabetical order by last name):

- Ben Darnell
- William Eiers
- Mehmet Emre
- Jacqueline Mai
- Zach Sisco
- Rory Zahedi
