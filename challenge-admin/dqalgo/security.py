# -*- coding: utf-8 -*-
__author__ = 'n2m'

r_algo = """
sec_pwd_share_me <- sec_pwd_share_a + rowSums(cbind(sec_pwd_share_b_1, sec_pwd_share_b_2, sec_pwd_share_b_3, sec_pwd_share_b_4, sec_pwd_share_b_5, sec_pwd_share_b_6, sec_pwd_share_b_7))
sec_pwd_know <- rowMeans(cbind( sec_pwd_know_1, sec_pwd_know_2, sec_pwd_know_3, sec_pwd_know_4, sec_pwd_know_5, sec_pwd_know_6))

sec_cyberthreats_know <- rowMeans(cbind( sec_cyberthreats_know_1, sec_cyberthreats_know_2, sec_cyberthreats_know_3, sec_cyberthreats_know_4, sec_cyberthreats_know_5, sec_cyberthreats_know_6, sec_cyberthreats_quiz_1, sec_cyberthreats_quiz_2, sec_cyberthreats_quiz_3, sec_cyberthreats_quiz_4, sec_cyberthreats_quiz_5, sec_cyberthreats_quiz_6, sec_cyberthreats_quiz_7, sec_cyberthreats_quiz_8, sec_cyberthreats_quiz_9, sec_cyberthreats_quiz_10, sec_cyberthreats_quiz_11, sec_cyberthreats_quiz_13))

sec_mob_safe <- rowMeans(cbind( sec_mob_safe_quiz_1, sec_mob_safe_quiz_2, sec_mob_safe_quiz_3, sec_mob_safe_quiz_4, sec_mob_safe_quiz_5, sec_mob_safe_quiz_6, sec_mob_safe_quiz_7, sec_mob_safe_quiz_8))


S <- array()

S <- cbind((sec_pwd_share_me+100)/1.2, (sec_pwd_skill-1)*100/3, (sec_pwd_act-1)*25, sec_pwd_know)
colnames(S)[(ncol(S)-3):ncol(S)] <- c("sec_pwd_share_me", "sec_pwd_skill", "sec_pwd_act", "sec_pwd_know")

S <- cbind(S, sec_cyberthreats_know*100, sec_mob_safe*100, sec_scam_act*100)
colnames(S)[(ncol(S)-2):ncol(S)] <- c("sec_cyberthreats_know", "sec_mob_safe", "sec_scam_act")

S <- as.data.frame(S)


sec_score <- S$sec_pwd_share_me*0.1 +
            S$sec_pwd_skill*0.05 +
            S$sec_pwd_act*0.05 +
            S$sec_pwd_know*0.1 +
            S$sec_cyberthreats_know*0.5 +
            S$sec_scam_act*0.1 +
            S$sec_mob_safe*0.1
"""