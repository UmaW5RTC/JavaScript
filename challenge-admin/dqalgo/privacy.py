# -*- coding: utf-8 -*-
__author__ = 'n2m'

r_algo = """
pri_pi_beh <- 12 + as.numeric(pri_pi_beh_12==1) + as.numeric(pri_pi_beh_12!=1) * (rowSums(cbind(pri_pi_beh_1, pri_pi_beh_2, pri_pi_beh_3, pri_pi_beh_4, pri_pi_beh_5, pri_pi_beh_6, pri_pi_beh_7, pri_pi_beh_8, pri_pi_beh_9, pri_pi_beh_10, pri_pi_beh_11, pri_pi_beh_13))*(-1))
pri_pi_att <- rowMeans(cbind(pri_pi_att_2, pri_pi_att_3))
pri_pi_skill <- rowMeans(cbind(pri_pi_skill_1, pri_pi_skill_2, pri_pi_skill_3, pri_pi_skill_4, pri_pi_skill_5, pri_pi_skill_6))

pri_other_pwd_know <- as.numeric(pri_other_pwd_a_8==0) * rowSums(cbind(pri_other_pwd_a_1, pri_other_pwd_a_2, pri_other_pwd_a_3, pri_other_pwd_a_4, pri_other_pwd_a_5, pri_other_pwd_a_6, pri_other_pwd_a_7)) + as.numeric(pri_other_pwd_a_8!=0)*10 + 26
pri_other_post <- pri_other_post_1 * pri_other_post_2

pri_quiz <- rowMeans(cbind( pri_quiz_1, pri_quiz_2, pri_quiz_3, pri_quiz_4, pri_quiz_5, pri_quiz_6, pri_quiz_8, pri_quiz_9, pri_quiz_10, pri_quiz_11, pri_quiz_12, pri_quiz_13, pri_quiz_14, pri_quiz_15, pri_quiz_16 )) #removed pri_quiz_7
pri_other_pwd_intent <- (-10)*(sec_pwd_share_d*sec_pwd_share_e*sec_pwd_share_f) +  30


S <- array()

S <- cbind(sc_func(pri_pi_beh,c(0,5,9,12,13), c(0,25,50,75,100)), (pri_pi_att-1)*25, (pri_pi_skill)*100/5)
colnames(S)[(ncol(S)-2):ncol(S)] <- c("pri_pi_beh", "pri_pi_att", "pri_pi_skill")

S <- cbind(S, sc_func(pri_other_pwd_know,c(0,15,18,21,36),c(0,20,40,60,100)), pri_other_pwd_intent*10/3, (pri_other_post-1)*20, pri_quiz*100)
colnames(S)[(ncol(S)-3):ncol(S)] <- c("pri_other_pwd_know", "pri_other_pwd_intent", "pri_other_post", "pri_quiz")

S <- as.data.frame(S)

pri_pi_mgmt_score <- S$pri_pi_beh*0.2 +
                     S$pri_pi_att*0.05 +
                     S$pri_pi_skill*0.15 +
                     S$pri_other_pwd_know*0.2/3 +
                     S$pri_other_pwd_intent*0.2/3 +
                     S$pri_other_post*0.2/3 +
                     S$pri_quiz*0.4
"""