# -*- coding: utf-8 -*-
__author__ = 'n2m'

r_algo = """
emp_emp_a <- rowMeans(cbind(emp_emp_1, emp_emp_2, emp_emp_4, emp_emp_5, emp_emp_6, emp_emp_7, emp_emp_8))
emp_emp_b <- rowMeans(cbind(emp_emp_b_1, emp_emp_b_2, emp_emp_b_3, emp_om))
emp_emp_c <- emp_gr

emp_emp_d <- rowMeans(cbind(cb_up_1, cb_up_2))

emp_quiz <- rowMeans(cbind( emp_quiz_1, emp_quiz_2, emp_quiz_5, emp_quiz_6, emp_quiz_7, emp_quiz_8, emp_quiz_9, emp_quiz_10, emp_quiz_11, emp_quiz_12, emp_quiz_13, emp_quiz_14, emp_quiz_15))


S <- array()

S <- cbind((emp_emp_a-1)*100/3, (emp_emp_b-1)*50, emp_emp_c*25,(emp_emp_d-1)*100/4)
colnames(S)[(ncol(S)-3):ncol(S)] <- c("emp_emp_a", "emp_emp_b", "emp_emp_c", "emp_emp_d")

S <- cbind(S, emp_quiz)
colnames(S)[ncol(S)] <- "emp_quiz"

S <- as.data.frame(S)


emp_de_score <- S$emp_emp_a*0.5 +
                S$emp_emp_b*0.2 +
                S$emp_emp_c*0.03 +
                S$emp_emp_d*0.07+
                S$emp_quiz*0.2
"""