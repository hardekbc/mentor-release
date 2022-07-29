// Decides L = { 0{n}1{n}2{n} | n >= 0 }
alphabet: {0, 1, 2, x}
start: q0
q0 (0 -> _,R q1) (x -> x,R q4) (_ -> _,L accept)
q1 (0 -> 0,R q1) (x -> x,R q1) (1 -> x,R q2)
q2 (x -> x,R q2) (1 -> 1,R q2) (2 -> x,L q3)
q3 (x -> x,L q3) (0 -> 0,L q3) (1 -> 1,L q3) (_ -> _,R q0)
q4 (x -> x,R q4) (_ -> _,L accept)
