# -*- coding: utf-8 -*-
__author__ = 'n2m'

r_algo = """
df_beh <- (df_beh_1+df_beh_2+df_beh_3+df_beh_13)*1 +
          (df_beh_5+df_beh_6+df_beh_7)*2 +
          (df_beh_11+df_beh_12)*3 +
          (df_beh_4+df_beh_8+df_beh_9+df_beh_10)*4

df_aware_quiz <- rowMeans(cbind(df_nat_q_1, df_nat_q_2, df_nat_q_3, df_nat_q_4, df_df_quiz_1, df_df_quiz_2, df_df_quiz_3, df_df_quiz_4, df_df_quiz_5, df_df_quiz_6 ))

df_rep_skill <- rowMeans(cbind(df_mgmt_1, df_mgmt_2, df_mgmt_3, 6-df_mgmt_4, df_mgmt_5))

df_dp_quiz <- rowMeans(cbind(df_dp_quiz_1, df_dp_quiz_2, df_dp_quiz_3, df_dp_quiz_4, df_dp_quiz_5, df_dp_quiz_6, df_dp_quiz_7, df_dp_quiz_8, df_dp_quiz_9, df_dp_quiz_10, df_dp_quiz_11, df_dp_quiz_12))


S <- array()

S <- cbind(S, (df_beh-32)/1.28)
colnames(S)[ncol(S)] <- "df_beh"

S <- cbind(S, df_aware_quiz*100)
colnames(S)[ncol(S)] <- "df_aware_quiz"

S <- cbind(S, (df_rep_skill-1)*25)
colnames(S)[ncol(S)] <- "df_rep_skill"

S <- cbind(S, df_dp_quiz*100)
colnames(S)[ncol(S)] <- "df_dp_quiz"

S <- as.data.frame(S)


df_mgmt_score <- S$df_aware_quiz*0.2 +
                 S$df_rep_skill*0.35 +
                 S$df_dp_quiz*0.45
"""